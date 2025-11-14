# CatchCore 新手快速入门指南

## 👋 欢迎！

如果你是编程新手，不用担心！这份指南会一步步教你如何部署 CatchCore。

---

## 第一步: 准备工作 (5 分钟)

### 1.1 下载和安装 Python

**Windows 用户:**
1. 访问 [python.org](https://www.python.org/downloads/)
2. 点击 "Download Python 3.11"
3. 双击下载的文件 `python-3.11.x.exe`
4. ⚠️ **重要**: 勾选 "Add Python to PATH"
5. 点击 "Install Now"
6. 安装完成后，重启电脑

**macOS 用户:**
1. 打开终端 (Applications > Utilities > Terminal)
2. 复制粘贴以下命令:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
3. 等待安装完成
4. 再输入:
```bash
brew install python@3.11
```

**Linux 用户:**
1. 打开终端
2. 输入:
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip
```

### 1.2 验证安装

打开新的终端/命令提示符，输入:
```bash
python --version
```

你应该看到:
```
Python 3.11.x
```

如果看到 "command not found"，说明安装有问题，回到上一步。

---

## 第二步: 获取项目代码 (2 分钟)

### 2.1 下载项目

**方法 1: 使用 Git (推荐)**

```bash
git clone https://github.com/yourusername/CatchCore.git
cd CatchCore/backend
```

**方法 2: 直接下载**

1. 访问 https://github.com/yourusername/CatchCore
2. 点击绿色的 "Code" 按钮
3. 点击 "Download ZIP"
4. 解压文件
5. 打开终端/命令提示符
6. 进入 `CatchCore/backend` 文件夹

---

## 第三步: 自动部署 (3-5 分钟)

### 3.1 运行部署脚本

**Windows 用户:**

1. 在 `CatchCore\backend` 目录中，右键打开 PowerShell
2. 运行:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup.ps1
```

**macOS 和 Linux 用户:**

1. 打开终端
2. 进入 `CatchCore/backend` 目录
3. 运行:
```bash
bash ../../setup.sh
```

脚本会自动做以下事情:
- ✅ 创建虚拟环境
- ✅ 安装所有依赖
- ✅ 配置数据库
- ✅ 创建 .env 文件
- ✅ 运行测试

等待脚本完成 (可能需要 3-5 分钟)。

### 3.2 如果脚本失败

不用担心！继续手动部署:

**Windows:**
```powershell
# 打开 PowerShell，进入 CatchCore\backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

**macOS/Linux:**
```bash
# 打开终端，进入 CatchCore/backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

---

## 第四步: 运行应用 (1 分钟)

### 4.1 启动应用

确保虚拟环境已激活 (你应该看到 `(venv)` 前缀):

```bash
python -m uvicorn app.main:app --reload
```

你应该看到:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 4.2 测试应用

1. 打开浏览器
2. 访问: http://localhost:8000/docs
3. 你应该看到一个漂亮的 API 文档页面

恭喜！你已经成功部署了 CatchCore！

---

## 第五步: 基本使用 (5 分钟)

### 5.1 创建用户账户

在 API 文档页面中:

1. 找到 `/api/v1/users/register` 端点
2. 点击 "Try it out"
3. 输入用户名和邮箱
4. 点击 "Execute"

### 5.2 创建扫描任务

1. 找到 `/api/v1/tasks` 端点
2. 点击 "Try it out"
3. 填写任务信息
4. 点击 "Execute"

### 5.3 查看结果

访问: http://localhost:8000/api/v1/tasks

---

## 常见新手问题

### Q1: "ModuleNotFoundError: No module named 'fastapi'"

**A:** 你没有激活虚拟环境

```bash
# 你应该看到 (venv) 前缀在命令行前面

# 如果没有，激活它:
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\Activate.ps1  # Windows
```

### Q2: "Address already in use"

**A:** 端口 8000 被其他程序占用

```bash
# 使用不同的端口
python -m uvicorn app.main:app --port 8001 --reload

# 或关闭占用该端口的程序
```

### Q3: 怎样停止应用?

**A:** 按 `Ctrl + C`

---

## 安装问题排查

### 问题: pip 安装很慢

**解决:**

中国用户可以使用国内镜像:

```bash
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
```

### 问题: "No module named 'app'"

**解决:**

确保你在正确的目录:

```bash
pwd  # 输出应该以 /backend 或 \backend 结尾

# 应该看到:
# app/
# tests/
# requirements.txt
# .env
```

### 问题: Python 版本太旧

**解决:**

你需要 Python 3.10 或更高版本:

```bash
python --version

# 如果版本太旧，安装新版本:
# Windows: https://www.python.org/downloads/
# macOS: brew install python@3.11
# Linux: sudo apt install python3.11
```

---

## 下一步

现在你已经成功部署了应用！可以：

1. **探索 API 文档:** http://localhost:8000/docs
2. **运行测试:**
   ```bash
   python -m pytest tests/ -v
   ```

3. **阅读完整文档:** `DEPLOYMENT_GUIDE.md`
4. **处理问题:** `TROUBLESHOOTING_GUIDE.md`

---

## 需要帮助？

如果你遇到问题:

1. **查看错误消息** - 这通常会告诉你出了什么问题
2. **查看日志:**
   ```bash
   tail -f logs/catchcore.log  # macOS/Linux
   Get-Content logs/catchcore.log -Tail 50 -Wait  # Windows
   ```

3. **查看完整的故障排查指南:** `TROUBLESHOOTING_GUIDE.md`
4. **提交 Issue:** https://github.com/yourusername/CatchCore/issues

---

## 终端/命令提示符基础

如果你对终端不熟悉，这里有一些基本命令:

| 命令 | 说明 | 例子 |
|------|------|------|
| `cd` | 改变目录 | `cd CatchCore/backend` |
| `ls` / `dir` | 列出文件 | `ls` |
| `pwd` | 显示当前目录 | `pwd` |
| `mkdir` | 创建目录 | `mkdir test` |
| `touch` | 创建文件 | `touch file.txt` |
| `cat` / `type` | 显示文件内容 | `cat file.txt` |
| `echo` | 打印文本 | `echo "Hello"` |

**快速技巧:**
- 按 `Ctrl + C` 停止运行的程序
- 按 ↑ 查看之前的命令
- 输入前几个字符，按 `Tab` 自动完成

---

## 虚拟环境说明

**什么是虚拟环境?**

虚拟环境是一个隔离的 Python 环境，这样不同的项目可以有不同的依赖版本，互不影响。

**激活虚拟环境的标志:**

```bash
# 激活前
$ python --version

# 激活后
(venv) $ python --version  # 看到 (venv) 前缀
```

---

## 环境变量 (.env) 说明

`.env` 文件存储敏感配置，比如数据库密码。

**为什么很重要?**
- 不要把密码提交到 Git
- 不同的环境 (开发/生产) 需要不同的配置
- 保持敏感信息的安全

**如何编辑 .env:**

```bash
# 使用文本编辑器打开
nano .env  # Linux/macOS
notepad .env  # Windows
```

---

## 总结

你现在已经:
- ✅ 安装了 Python
- ✅ 下载了项目
- ✅ 创建了虚拟环境
- ✅ 安装了依赖
- ✅ 运行了应用
- ✅ 验证了安装

**恭喜！你已经成为 CatchCore 的开发者了！** 🎉

---

## 更多资源

- **Python 基础:** https://docs.python.org/3/tutorial/
- **FastAPI 教程:** https://fastapi.tiangolo.com/
- **Git 基础:** https://git-scm.com/book/en/v2

---

**需要帮助?**

查看 `TROUBLESHOOTING_GUIDE.md` 获取更多帮助！

