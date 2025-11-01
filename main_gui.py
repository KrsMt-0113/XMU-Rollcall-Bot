# 厦大数字化教学平台自动签到机器人 V1.0 - GUI版本
# by KrsMt-0113
import sys
import time
import json
import uuid
import requests
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from serverchan_sdk import sc_send
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from parse_rollcalls import parse_rollcalls
from gui import MainWindow


class WorkerSignals(QObject):
    """工作线程信号"""
    log = pyqtSignal(str, str)  # message, level
    status = pyqtSignal(str)
    qr_code = pyqtSignal(str)  # image path
    hide_qr = pyqtSignal()
    started = pyqtSignal()
    finished = pyqtSignal()
    check_increment = pyqtSignal()
    sign_increment = pyqtSignal()


class MonitorWorker(QThread):
    """监控工作线程"""

    def __init__(self, username, password, sendkey):
        super().__init__()
        self.username = username
        self.password = password
        self.sendkey = sendkey
        self.signals = WorkerSignals()
        self.running = True
        self.driver = None

    def log(self, message, level="info"):
        """发送日志信号"""
        self.signals.log.emit(message, level)

    def update_status(self, status):
        """更新状态"""
        self.signals.status.emit(status)

    def run(self):
        """运行监控任务"""
        try:
            # 签到列表获取接口，轮询间隔，轮询脚本
            api_url = "https://lnt.xmu.edu.cn/api/radar/rollcalls"
            interval = 1.5
            fetch_script = """
const url = arguments[0];
const callback = arguments[arguments.length - 1];
fetch(url, {credentials: 'include'})
  .then(resp => resp.text().then(text => callback({status: resp.status, ok: resp.ok, text: text})))
  .catch(err => callback({error: String(err)}));
"""

            chrome_options = Options()
            chrome_options.add_argument("--headless")  # 无头运行

            # 启动selenium
            self.log("Initializing Selenium...", "info")
            self.update_status("Initializing...")
            sc_send(self.sendkey, "签到机器人", "正在初始化...", {"tags": "签到机器人"})
            self.driver = webdriver.Chrome(options=chrome_options)

            # 访问登录页面
            self.driver.get("https://lnt.xmu.edu.cn")
            self.log("Connected to XMU Course platform.", "success")

            # 检查是否需要验证码
            ts = int(time.time() * 1000)
            temp_header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"}
            temp_url = f"https://ids.xmu.edu.cn/authserver/checkNeedCaptcha.htl?username={self.username}&_={ts}"
            res_data = requests.get(temp_url, cookies={c['name']: c['value'] for c in self.driver.get_cookies()}, headers=temp_header).json()

            if not res_data['isNeed']:
                self.log("No captcha needed. Logging you in...", "info")
                self.update_status("Logging in...")
                sc_send(self.sendkey, "签到机器人", "账号密码登录中...", {"tags": "签到机器人"})

                WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "userNameLogin_a"))
                ).click()
                self.driver.find_element(By.ID, "username").send_keys(self.username)
                self.driver.find_element(By.ID, "password").send_keys(self.password)
                self.driver.find_element(By.ID, "login_submit").click()
                time.sleep(1)
            else:
                self.log("Captcha needed. Please login in through QR code.", "warning")
                self.update_status("Waiting for QR code login...")
                sc_send(self.sendkey, "签到机器人", "需要图形验证码，请扫码登录。", {"tags": "签到机器人"})

                # 切换到二维码登录
                self.driver.find_element(By.ID, "qrLogin_a").click()
                self.driver.set_window_size(1920, 1080)
                time.sleep(1)

                # 截图并显示二维码
                self.driver.get_screenshot_as_file("cache/fullpage.png")
                self.signals.qr_code.emit("cache/fullpage.png")

                # 等待登录成功（轮询检查）
                login_success = False
                for _ in range(120):  # 最多等待2分钟
                    if not self.running:
                        return
                    try:
                        res = requests.get(api_url, cookies={c['name']: c['value'] for c in self.driver.get_cookies()})
                        if res.status_code == 200:
                            login_success = True
                            break
                    except:
                        pass
                    time.sleep(1)

                self.signals.hide_qr.emit()

                if not login_success:
                    self.log("Login timeout.", "error")
                    return

            # 验证登录
            res = requests.get(api_url, cookies={c['name']: c['value'] for c in self.driver.get_cookies()})
            if res.status_code == 200:
                self.log("Successfully login!", "success")
                sc_send(self.sendkey, "签到机器人", "登录成功！五秒后进入监控模式...", {"tags": "签到机器人"})
            else:
                self.log("Login failed.", "error")
                return

            time.sleep(5)

            deviceID = uuid.uuid4()
            self.log("Start monitoring.", "success")
            self.update_status("Monitoring...")
            sc_send(self.sendkey, "签到机器人", "签到监控已启动。", {"tags": "签到机器人"})
            self.signals.started.emit()

            temp_data = {'rollcalls': []}
            check_count = 0

            while self.running:
                res = self.driver.execute_async_script(fetch_script, api_url)
                check_count += 1

                if check_count % 10 == 0:  # 每10次检测更新一次计数
                    self.signals.check_increment.emit()

                if res['status'] == 200:
                    text = res.get('text', '')
                    try:
                        data = json.loads(text)
                        if temp_data == data:
                            continue
                        else:
                            temp_data = data
                            if len(temp_data['rollcalls']) > 0:
                                self.log(f"Find {len(temp_data['rollcalls'])} new rollcalls！", "warning")
                                self.signals.sign_increment.emit()

                                # 显示详细信息
                                for idx, rollcall in enumerate(temp_data['rollcalls']):
                                    self.log(f"Rollcall {idx+1}/{len(temp_data['rollcalls'])}: {rollcall['course_title']}", "info")
                                    self.log(f"  Launch by: {rollcall['created_by_name']}", "info")
                                    self.log(f"  Status: {rollcall['rollcall_status']}", "info")

                                if not parse_rollcalls(temp_data, self.driver):
                                    temp_data = {'rollcalls': []}
                                else:
                                    self.log("Rollcall done.", "success")
                    except Exception as e:
                        self.log(f"Error: {str(e)}", "error")

                elif res['status'] != 200:
                    self.log("Disconnected, monitor has stopped.", "error")
                    sc_send(self.sendkey, "签到机器人", "失去连接，监控已终止。", {"tags": "签到机器人"})
                    break

                time.sleep(interval)

        except Exception as e:
            self.log(f"Error: {str(e)}", "error")
        finally:
            if self.driver:
                self.driver.quit()
            self.signals.finished.emit()

    def stop(self):
        """停止监控"""
        self.running = False
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


def main():
    """主函数"""
    # 读取配置
    try:
        with open("config.json") as f:
            config = json.load(f)
            username = config["username"]
            password = config["password"]
            sendkey = config["sendkey"]
    except Exception as e:
        print(f"读取配置文件失败: {e}")
        return

    # 创建应用
    app = QApplication(sys.argv)

    # 创建主窗口
    window = MainWindow()

    # 创建工作线程
    worker = MonitorWorker(username, password, sendkey)

    # 连接信号
    worker.signals.log.connect(window.add_log)
    worker.signals.status.connect(window.update_status)
    worker.signals.qr_code.connect(window.show_qr_code)
    worker.signals.hide_qr.connect(window.hide_qr_code)
    worker.signals.started.connect(window.start_monitoring)
    worker.signals.finished.connect(window.stop_monitoring)
    worker.signals.check_increment.connect(window.increment_check_count)
    worker.signals.sign_increment.connect(window.increment_sign_count)

    # 连接停止按钮
    window.stop_button.clicked.connect(worker.stop)
    window.stop_button.clicked.connect(lambda: window.add_log("用户手动停止监控", "warning"))

    # 启动工作线程
    worker.start()

    # 显示窗口
    window.show()

    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

