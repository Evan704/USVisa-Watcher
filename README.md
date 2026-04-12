# Visa Appointment Scraper

自动监控 qmq.app 美签面签预约信息的 Python 脚本。

## 功能

- 实时监控北京 F-1 Other Student 签证预约日期
- 当发现比目标日期更早的预约时发送邮件提醒
- 支持单次检查和持续循环监控模式
- 使用 Playwright 处理 JavaScript 动态加载内容

## 安装

### 1. 创建 Conda 环境

```bash
conda env create -f environment.yml
conda activate visa-scraper
```

### 2. 安装浏览器

```bash
playwright install chromium
```

## 配置

复制 `.env.example` 为 `.env` 并填写您的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# 目标日期 - 发现早于该日期的预约时提醒
TARGET_DATE=2025-06-01

# 签证信息
CITY=北京
VISA_TYPE=F-1
VISA_CATEGORY=Other Student

# SMTP 配置 (以 Gmail 为例)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFY_EMAIL=recipient@example.com

# 检查间隔（分钟）
CHECK_INTERVAL_MINUTES=30
```

**注意：** 如果使用 Gmail，需要生成应用专用密码：
1. 访问 https://myaccount.google.com/apppasswords
2. 生成 16 位应用密码
3. 将密码填入 `SMTP_PASSWORD`

## 使用

### 单次检查

```bash
python main.py
```

### 持续监控（循环模式）

```bash
python main.py --loop
```

### 详细日志

```bash
python main.py --verbose
python main.py --loop --verbose
```

## 测试

```bash
# 运行单元测试
pytest tests/ -v

# 运行集成测试（会访问真实网站）
pytest tests/test_integration.py -v --run-integration
```

## 项目结构

```
.
├── config.py          # 配置管理
├── notifier.py        # 邮件通知
├── scraper.py         # 网页抓取
├── main.py            # 主程序入口
├── tests/             # 测试文件
├── environment.yml    # Conda 环境配置
├── requirements.txt   # pip 依赖
├── .env.example       # 配置模板
└── README.md          # 本文档
```

## 注意事项

1. **网络要求**：需要能访问 qmq.app
2. **频率限制**：不要过于频繁地抓取，建议间隔至少 10 分钟
3. **邮件延迟**：某些邮箱服务商可能有投递延迟

## 故障排除

### 浏览器启动失败

```bash
playwright install --with-deps chromium
```

### SSL 证书错误

如果在 WSL 中遇到 SSL 错误，尝试：
```bash
sudo apt-get update
sudo apt-get install ca-certificates
```

### 邮件发送失败

- 检查 SMTP 配置是否正确
- 确认已使用应用专用密码（非登录密码）
- 检查发件邮箱是否启用了 SMTP 访问

---

# Visa Appointment Scraper (English)

Python script to automatically monitor US visa appointment availability on qmq.app.

## Features

- Real-time monitoring for Beijing F-1 Other Student visa appointments
- Email alerts when earlier appointments become available
- Supports single check and continuous loop monitoring modes
- Uses Playwright to handle JavaScript-heavy pages

## Installation

### 1. Create Conda Environment

```bash
conda env create -f environment.yml
conda activate visa-scraper
```

### 2. Install Browser

```bash
playwright install chromium
```

## Configuration

Copy `.env.example` to `.env` and fill in your settings:

```bash
cp .env.example .env
```

Edit the `.env` file:

```bash
# Target date - alerts when earlier dates are found
TARGET_DATE=2025-06-01

# Visa information
CITY=北京
VISA_TYPE=F-1
VISA_CATEGORY=Other Student

# SMTP configuration (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFY_EMAIL=recipient@example.com

# Check interval (minutes)
CHECK_INTERVAL_MINUTES=30
```

**Note:** If using Gmail, you need to generate an app-specific password:
1. Visit https://myaccount.google.com/apppasswords
2. Generate a 16-character app password
3. Use this password for `SMTP_PASSWORD`

## Usage

### Single Check

```bash
python main.py
```

### Continuous Monitoring (Loop Mode)

```bash
python main.py --loop
```

### Verbose Logging

```bash
python main.py --verbose
python main.py --loop --verbose
```

## Testing

```bash
# Run unit tests
pytest tests/ -v

# Run integration tests (hits real website)
pytest tests/test_integration.py -v --run-integration
```

## Project Structure

```
.
├── config.py          # Configuration management
├── notifier.py        # Email notifications
├── scraper.py         # Web scraping
├── main.py            # Main entry point
├── tests/             # Test files
├── environment.yml    # Conda environment config
├── requirements.txt   # pip dependencies
├── .env.example       # Configuration template
└── README.md          # This document
```

## Important Notes

1. **Network Requirements**: Must be able to access qmq.app
2. **Rate Limiting**: Don't scrape too frequently; recommend at least 10 minute intervals
3. **Email Delays**: Some email providers may have delivery delays

## Troubleshooting

### Browser Launch Failure

```bash
playwright install --with-deps chromium
```

### SSL Certificate Errors

If you encounter SSL errors in WSL, try:
```bash
sudo apt-get update
sudo apt-get install ca-certificates
```

### Email Sending Failure

- Verify SMTP configuration is correct
- Confirm you're using an app-specific password (not login password)
- Check that the sender email has SMTP access enabled
