# Temu Agentseller 邮件验证自动化工具

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/playwright-1.40+-green.svg)](https://playwright.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 自动批量处理 Temu Agentseller 平台的邮件验证 Confirm 确认任务

## 功能特性

- **全自动处理**: 自动输入验证码、筛选状态、批量点击 Confirm
- **智能翻页**: 自动处理多页数据，支持断点续传
- **过期检测**: 自动跳过已过期的确认项
- **防遮挡处理**: 自动处理 modal 弹窗遮挡问题
- **持续运行模式**: 支持循环运行直到所有数据处理完成

## 快速开始

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install playwright

# 安装浏览器
playwright install chromium
```

### 2. 配置参数

编辑 `run_temu_full_fixed.py` 修改以下配置：

```python
# Temu Agentseller 邮件验证页面 URL
URL = "https://agentseller.temu.com/safety-service/email-validate?urlToken=YOUR_TOKEN&repType=10"

# 验证码（用于解锁页面）
VERIFY_CODE = "YOUR_CODE"
```

### 3. 运行脚本

**单次运行：**
```bash
python3 run_temu_full_fixed.py
```

**持续运行模式（推荐）：**
```bash
python3 run_until_complete.py
```

**重置进度从头开始：**
```bash
echo '{"last_page": 0}' > page_record_temu.json
```

## 项目结构

```
.
├── run_temu_full_fixed.py      # 主脚本（单次运行）
├── run_until_complete.py       # 持续运行模式
├── run_until_empty.sh          # Bash 持续运行脚本
├── page_record_temu.json       # 进度记录文件
├── quick_verify.py             # 快速验证脚本
└── README.md                   # 本文件
```

## 工作原理

1. **页面访问**: 使用 Playwright 打开 Temu Agentseller 邮件验证页面
2. **验证码输入**: 自动识别并输入验证码解锁页面
3. **状态筛选**: 选择 "Requires verification" 筛选待处理项目
4. **批量处理**: 遍历表格中的 Confirm 按钮，自动点击确认
5. **翻页处理**: 自动翻页继续处理，直到所有页面完成
6. **进度保存**: 实时保存处理进度，支持断点续传

## 注意事项

- **验证码有效期**: 验证码通常有有效期，过期后需要重新获取
- **IP 限制**: 频繁操作可能触发平台风控，建议适当控制操作频率
- **页面结构变化**: 如果 Temu 页面结构更新，可能需要调整选择器

## 故障排除

**Q: 脚本提示 "modal 弹窗遮挡" 错误**
A: 脚本已内置防遮挡处理，如果仍有问题，请检查是否有新的弹窗类型

**Q: 进度卡在某一页不继续**
A: 运行 `echo '{"last_page": 0}' > page_record_temu.json` 重置进度从头开始

**Q: 验证码输入后页面无响应**
A: 验证码可能已过期，请获取新的验证码并更新 `VERIFY_CODE` 变量

## 许可证

[MIT](LICENSE) © mcliu

## 更新日志

### v1.0.0 (2024-04-13)
- 初始版本发布
- 支持自动验证码输入
- 支持批量 Confirm 处理
- 支持智能翻页和断点续传
- 支持持续运行模式
