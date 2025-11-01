# GUI界面模块
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QTextEdit, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap
import datetime


class SignalEmitter(QThread):
    """用于线程安全地发送信号的辅助类"""
    log_signal = pyqtSignal(str, str)  # message, level
    status_signal = pyqtSignal(str)
    qr_signal = pyqtSignal(str)  # qr code path

    def __init__(self):
        super().__init__()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XMU RollCall Bot v1.0")
        self.setMinimumSize(600, 600)

        # 设置主题颜色
        self.primary_color = "#4A90E2"
        self.success_color = "#5CB85C"
        self.warning_color = "#F0AD4E"
        self.danger_color = "#D9534F"
        self.bg_color = "#F5F7FA"
        self.card_color = "#FFFFFF"
        self.text_color = "#333333"
        self.text_muted = "#999999"

        self.setup_ui()

    def setup_ui(self):
        """设置UI布局"""
        # 设置窗口背景色
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.bg_color};
            }}
        """)

        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("RollCall Monitor")
        title_label.setFont(QFont("Monaco", 24, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self.text_color};")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # 状态指示器
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Monaco", 20))
        self.status_indicator.setStyleSheet(f"color: {self.text_muted};")
        title_layout.addWidget(self.status_indicator)

        self.status_label = QLabel("Initializing...")
        self.status_label.setFont(QFont("Monaco", 12))
        self.status_label.setStyleSheet(f"color: {self.text_muted};")
        title_layout.addWidget(self.status_label)

        main_layout.addLayout(title_layout)

        # 信息卡片区域
        info_frame = self.create_card()
        info_layout = QHBoxLayout(info_frame)
        info_layout.setSpacing(30)

        # 监控时长
        self.time_widget = self.create_info_widget("⏱️", "Running", "00:00:00")
        info_layout.addWidget(self.time_widget)

        # 检测次数
        self.check_widget = self.create_info_widget("🔍", "Queries", "0")
        info_layout.addWidget(self.check_widget)

        # 签到次数
        self.sign_widget = self.create_info_widget("✅", "Success", "0")
        info_layout.addWidget(self.sign_widget)

        main_layout.addWidget(info_frame)

        # 日志区域
        log_label = QLabel("Logs")
        log_label.setFont(QFont("Monaco", 14, QFont.Weight.Bold))
        log_label.setStyleSheet(f"color: {self.text_color};")
        main_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.card_color};
                border: 2px solid #E1E8ED;
                border-radius: 10px;
                padding: 15px;
                font-family: 'Monaco', monospace;
                font-size: 12px;
                color: {self.text_color};
            }}
        """)
        main_layout.addWidget(self.log_text, stretch=1)

        # 二维码显示区域（初始隐藏）
        self.qr_frame = self.create_card()
        qr_layout = QVBoxLayout(self.qr_frame)
        qr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        qr_title = QLabel("📱 Sign in with QR Code by WeCom.")
        qr_title.setFont(QFont("Monaco", 14, QFont.Weight.Bold))
        qr_title.setStyleSheet(f"color: {self.text_color};")
        qr_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_layout.addWidget(qr_title)

        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setStyleSheet("padding: 20px;")
        qr_layout.addWidget(self.qr_label)

        self.qr_frame.hide()
        main_layout.addWidget(self.qr_frame)

        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.stop_button = QPushButton(" Stop Monitoring ")
        self.stop_button.setEnabled(False)
        self.stop_button.setFixedSize(140, 40)
        self.stop_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.danger_color};
                color: white;
                border: none;
                border-radius: 8px;
                font-family: 'Monaco', monospace;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #C9302C;
            }}
            QPushButton:disabled {{
                background-color: #CCCCCC;
                color: #666666;
            }}
        """)
        button_layout.addWidget(self.stop_button)

        main_layout.addLayout(button_layout)

        # 初始化计数器
        self.check_count = 0
        self.sign_count = 0
        self.start_time = None

        # 定时器更新运行时间
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_runtime)

    def create_card(self):
        """创建卡片容器"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.card_color};
                border-radius: 15px;
                border: none;
            }}
        """)
        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 3)
        frame.setGraphicsEffect(shadow)
        return frame

    def create_info_widget(self, icon, title, value):
        """创建信息显示部件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(5)

        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Monaco", 32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        value_label = QLabel(value)
        value_label.setFont(QFont("Monaco", 24, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {self.primary_color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setObjectName("value")
        layout.addWidget(value_label)

        title_label = QLabel(title)
        title_label.setFont(QFont("Monaco", 11))
        title_label.setStyleSheet(f"color: {self.text_muted};")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        widget.setMinimumWidth(180)
        return widget

    def add_log(self, message, level="info"):
        """添加日志信息"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        color = self.text_color
        prefix = "ℹ️"

        if level == "success":
            color = self.success_color
            prefix = "✅"
        elif level == "warning":
            color = self.warning_color
            prefix = "⚠️"
        elif level == "error":
            color = self.danger_color
            prefix = "❌"

        html = f'<span style="color: {self.text_muted};">[{timestamp}]</span> <span style="color: {color};">{prefix} {message}</span>'
        self.log_text.append(html)

        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_status(self, status, color=None):
        """更新状态"""
        self.status_label.setText(status)
        if color is None:
            if "Monitoring..." in status:
                color = self.success_color
            elif "Failed" in status or "Error" in status:
                color = self.danger_color
            elif "Initializing..." in status or "Logging in" in status or "login" in status:
                color = self.warning_color
            else:
                color = self.text_muted

        self.status_label.setStyleSheet(f"color: {color};")
        self.status_indicator.setStyleSheet(f"color: {color};")

    def show_qr_code(self, image_path):
        """显示二维码"""
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # 缩放到合适大小
            scaled_pixmap = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
            self.qr_label.setPixmap(scaled_pixmap)
            self.qr_frame.show()

    def hide_qr_code(self):
        """隐藏二维码"""
        self.qr_frame.hide()

    def start_monitoring(self):
        """开始监控"""
        self.start_time = datetime.datetime.now()
        self.timer.start(1000)  # 每秒更新一次
        self.stop_button.setEnabled(True)
        self.update_status("Monitoring...")

    def stop_monitoring(self):
        """停止监控"""
        self.timer.stop()
        self.stop_button.setEnabled(False)
        self.update_status("Stopped")

    def update_runtime(self):
        """更新运行时间"""
        if self.start_time:
            delta = datetime.datetime.now() - self.start_time
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            time_value = self.time_widget.findChild(QLabel, "value")
            if time_value:
                time_value.setText(time_str)

    def increment_check_count(self):
        """增加检测次数"""
        self.check_count += 1
        check_value = self.check_widget.findChild(QLabel, "value")
        if check_value:
            check_value.setText(str(self.check_count))

    def increment_sign_count(self):
        """增加签到次数"""
        self.sign_count += 1
        sign_value = self.sign_widget.findChild(QLabel, "value")
        if sign_value:
            sign_value.setText(str(self.sign_count))

