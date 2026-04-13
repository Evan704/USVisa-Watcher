# USVisa-Watcher

自动监控 qmq.app 美签面签预约信息的 Python 脚本。当发现比目标日期更早的预约时，自动发送邮件提醒。

## 功能特点

- 实时监控指定城市、签证类型的预约日期
- 发现更早预约时自动邮件提醒
- 支持单次检查和持续监控两种模式
- 使用 Playwright 处理动态网页
- 支持 Gmail、QQ邮箱、163邮箱等多种 SMTP 服务商

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/USVisa-Watcher.git
cd USVisa-Watcher
```

### 2. 安装依赖

**方式一：使用 Conda（推荐）**

```bash
# 创建并激活环境
conda env create -f environment.yml
conda activate usvisa-watcher

# 安装浏览器
playwright install chromium
```

**方式二：使用 pip**

```bash
# 创建虚拟环境（可选但推荐）
python -m venv venv

# 激活虚拟环境
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
playwright install chromium
```

### 3. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑配置文件（选择你喜欢的编辑器）
nano .env        # 或 vim .env，或直接用文本编辑器打开
```

编辑 `.env` 文件，填入你的配置（详见下方【配置说明】）。

### 4. 运行

```bash
# 单次检查
python main.py

# 持续监控模式（推荐）
python main.py --loop

# 显示详细日志
python main.py --verbose
```

---

## 配置说明

### 基础配置

```bash
# 目标日期 - 发现早于该日期的预约时提醒（格式：YYYY-MM-DD）
TARGET_DATE=2025-06-01

# 签证信息
CITY=北京                    # 城市名称
VISA_TYPE=F-1               # 签证类型
VISA_CATEGORY=Other Student # 签证类别

# 检查间隔（分钟，仅循环模式有效）
CHECK_INTERVAL_MINUTES=30
```

### 邮箱配置（选择一种）

#### QQ 邮箱（推荐国内用户）

```bash
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=your_qq@qq.com
# 授权码获取方式：
# 1. 登录 QQ 邮箱网页版
# 2. 设置 → 账户 → 开启 POP3/SMTP 服务
# 3. 按提示获取 16 位授权码（不是登录密码！）
SMTP_PASSWORD=your_auth_code
NOTIFY_EMAIL=your_qq@qq.com
```

#### 163 邮箱

```bash
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USER=your_email@163.com
# 授权码获取：设置 → POP3/SMTP/IMAP → 客户端授权密码
SMTP_PASSWORD=your_auth_code
NOTIFY_EMAIL=your_email@163.com
```

#### Gmail（推荐海外用户）

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
# 应用密码获取：
# 1. 访问 https://myaccount.google.com/apppasswords
# 2. 需要开启两步验证
# 3. 生成 16 位应用密码
SMTP_PASSWORD=your_app_password
NOTIFY_EMAIL=your_email@gmail.com
```

---

## 使用指南

### 单次检查模式

适合手动检查或添加到系统定时任务（cron）：

```bash
python main.py
```

输出示例：
```
2025-01-15 10:30:00 - INFO - Checking for 北京 F-1 (Other Student) appointments before 2025-06-01
2025-01-15 10:30:05 - INFO - Found earliest appointment: 2025-05-15
2025-01-15 10:30:05 - INFO - Appointment date 2025-05-15 is earlier than target 2025-06-01 - sending notification
2025-01-15 10:30:07 - INFO - Notification sent successfully
```

### 持续监控模式

推荐用法，后台持续运行：

```bash
python main.py --loop
```

配合 `nohup` 或 `screen` 在服务器后台运行：

```bash
# 方式一：nohup
nohup python main.py --loop > watcher.log 2>&1 &

# 方式二：screen
creen -S usvisa
python main.py --loop
# 按 Ctrl+A, D  detach

# 重新连接
screen -r usvisa
```

### 详细日志模式

排查问题时使用：

```bash
python main.py --verbose
# 或
python main.py --loop --verbose
```

日志文件保存在 `logs/usvisa-watcher.log`。

---

## 高级用法

### 设置系统定时任务（Linux/macOS）

每 30 分钟检查一次：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（修改路径为你的实际路径）
*/30 * * * * cd /path/to/USVisa-Watcher && /path/to/conda/envs/usvisa-watcher/bin/python main.py >> /path/to/USVisa-Watcher/cron.log 2>&1
```

### Docker 运行（可选）

```bash
# 构建镜像
docker build -t usvisa-watcher .

# 运行容器
docker run -d --env-file .env --name usvisa-watcher usvisa-watcher

# 查看日志
docker logs -f usvisa-watcher
```

---

## 测试

```bash
# 运行单元测试
pytest tests/ -v

# 运行集成测试（会访问真实网站，需要配置好 .env）
pytest tests/test_integration.py -v --run-integration
```

---

## 项目结构

```
.
├── main.py            # 主程序入口
├── scraper.py         # 网页抓取逻辑
├── notifier.py        # 邮件通知
├── config.py          # 配置管理
├── tests/             # 测试文件
├── environment.yml    # Conda 环境配置
├── requirements.txt   # pip 依赖
├── .env.example       # 配置模板
└── README.md          # 本文档
```

---

## 常见问题

### Q: 浏览器启动失败？

**A:** 尝试安装系统依赖：

```bash
# Ubuntu/Debian
playwright install --with-deps chromium

# 或手动安装
sudo apt-get update
sudo apt-get install -y libwoff1 libopus0 libwebp7 libwebpdemux2 libenchant-2-2 libsecret-1-0 libhyphen0 libgdk-pixbuf2.0-0 libegl1 libgles2 libevent-2.1-7 libgstreamer1.0-0 libgstreamer-plugins-base1.0-0 libgstreamer-gl1.0-0 libgstreamer-plugins-bad1.0-0 libopenjp2-7 libharfbuzz-icu0 libwebpmux3
```

### Q: 邮件发送失败？

**A:** 检查以下几点：
1. SMTP 配置是否正确（特别是端口）
2. 是否使用了授权码/应用密码（不是登录密码）
3. 邮箱是否开启了 SMTP 服务
4. 防火墙是否阻断了 SMTP 端口

测试邮件配置：
```python
python -c "from notifier import EmailNotifier; from config import get_settings; n = EmailNotifier(get_settings()); print('SMTP OK' if n._send_email('Test', 'Test body') else 'SMTP Failed')"
```

### Q: SSL 证书错误？

**A:** 在 WSL 或某些 Linux 发行版上：

```bash
sudo apt-get update
sudo apt-get install ca-certificates
```

### Q: 如何监控其他城市或签证类型？

**A:** 修改 `.env` 文件：

```bash
CITY=上海                    # 支持：北京、上海、广州、成都、沈阳等
VISA_TYPE=F-1               # 支持：F-1, B-1/B-2, H-1B, J-1 等
VISA_CATEGORY=Other Student # 支持：Other Student, Student, Business, Tourism 等
```

### Q: 能否同时监控多个地区？

**A:** 当前版本不支持，建议复制多个实例到不同目录，分别配置运行。

---

## 注意事项

1. **网络要求**：需要能访问 https://qmq.app
2. **频率限制**：建议检查间隔不少于 10 分钟，过于频繁的请求可能导致 IP 被临时封禁
3. **邮件延迟**：部分邮箱服务商可能有 1-5 分钟的投递延迟
4. **安全性**：`.env` 文件包含敏感信息，不要提交到 Git 仓库（已添加到 `.gitignore`）

---

## License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

# USVisa-Watcher (English)

Python script to automatically monitor US visa appointment availability on qmq.app and send email alerts when earlier dates become available.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/yourusername/USVisa-Watcher.git
cd USVisa-Watcher

# 2. Install dependencies
conda env create -f environment.yml
conda activate usvisa-watcher
playwright install chromium

# 3. Configure
cp .env.example .env
# Edit .env with your settings

# 4. Run
python main.py --loop
```

See Chinese section above for detailed configuration options.
