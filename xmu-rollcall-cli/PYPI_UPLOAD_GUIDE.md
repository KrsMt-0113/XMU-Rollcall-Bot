# PyPI 上传指南

本文档指导如何将 xmu-rollcall-cli 上传到 PyPI。

## 前置准备

### 1. 注册 PyPI 账号

- 正式版：https://pypi.org/account/register/
- 测试版：https://test.pypi.org/account/register/ （建议先在测试环境试验）

### 2. 安装必要工具

```bash
pip install --upgrade pip setuptools wheel twine build
```

### 3. 配置 PyPI 凭证

创建 `~/.pypirc` 文件：

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
username = __token__
password = pypi-your-test-api-token-here
repository = https://test.pypi.org/legacy/
```

**安全提示**: 使用 API Token 而不是密码。在 PyPI 网站的 Account Settings -> API tokens 创建。

## 发布步骤

### 步骤 1: 清理旧的构建文件

```bash
cd IdeaProjects/Comet/xmu-rollcall-cli
rm -rf build/ dist/ *.egg-info
```

### 步骤 2: 构建分发包

使用现代构建工具：

```bash
python -m build
```

或使用传统方式：

```bash
python setup.py sdist bdist_wheel
```

这将在 `dist/` 目录下生成两个文件：
- `xmu-rollcall-cli-3.1.0.tar.gz` (源代码分发包)
- `xmu_rollcall_cli-3.1.0-py3-none-any.whl` (wheel 分发包)

### 步骤 3: 检查分发包

```bash
twine check dist/*
```

确保没有错误或警告。

### 步骤 4: 上传到 TestPyPI（可选但推荐）

先在测试环境测试：

```bash
twine upload --repository testpypi dist/*
```

测试安装：

```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps xmu-rollcall-cli
```

### 步骤 5: 上传到正式 PyPI

确认测试无误后，上传到正式 PyPI：

```bash
twine upload dist/*
```

### 步骤 6: 验证安装

```bash
pip install xmu-rollcall-cli
XMUrollcall-cli --help
```

## 更新版本

每次更新时：

1. 修改版本号：
   - `xmu_rollcall/__init__.py` 中的 `__version__`
   - `setup.py` 中的 `version`
   - `pyproject.toml` 中的 `version`

2. 重复上述构建和上传步骤

## 快速上传脚本

可以创建一个 `release.sh` 脚本自动化发布流程：

```bash
#!/bin/bash

# 清理
rm -rf build/ dist/ *.egg-info

# 构建
python -m build

# 检查
twine check dist/*

# 上传 (可以选择 testpypi 或 pypi)
echo "Upload to TestPyPI or PyPI?"
echo "1) TestPyPI"
echo "2) PyPI"
read -p "Choose: " choice

if [ "$choice" = "1" ]; then
    twine upload --repository testpypi dist/*
elif [ "$choice" = "2" ]; then
    twine upload dist/*
else
    echo "Invalid choice"
fi
```

## 常见问题

### Q: 包名已存在怎么办？

A: PyPI 上的包名是唯一的。如果 `xmu-rollcall-cli` 已被占用，需要更换包名。

### Q: 版本号冲突

A: 同一版本号只能上传一次。如需重新上传，必须增加版本号。

### Q: 忘记更新 README

A: 可以更新版本号后重新上传。PyPI 会显示新版本的 README。

### Q: 如何删除已上传的版本？

A: 登录 PyPI 网站，在项目管理页面可以删除特定版本（但不推荐）。

## 检查清单

上传前确认：

- [ ] README.md 内容完整且格式正确
- [ ] LICENSE 文件存在
- [ ] 版本号已更新（三处）
- [ ] MANIFEST.in 包含所有需要的文件
- [ ] requirements.txt 依赖正确
- [ ] 测试通过
- [ ] 邮箱地址已填写（setup.py 和 pyproject.toml）
- [ ] GitHub 仓库链接正确
- [ ] 已在 TestPyPI 测试

## 有用的命令

```bash
# 查看包信息
python setup.py --version
python setup.py --name
python setup.py --classifiers

# 查看将被包含的文件
python setup.py sdist --dry-run

# 本地安装测试
pip install -e .

# 卸载
pip uninstall xmu-rollcall-cli
```

## 参考资料

- [Python 打包用户指南](https://packaging.python.org/)
- [Twine 文档](https://twine.readthedocs.io/)
- [PyPI 帮助](https://pypi.org/help/)

