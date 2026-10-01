# 视频自动发布工具使用指南

## 功能概述

本工具支持三种发布模式：
1. **单个发布** - 立即发布单个交付包
2. **批量发布** - 批量处理多个交付包，支持并发和重试
3. **定时发布** - 设置定时发布任务，支持一次性和重复发布

## 安装依赖

```bash
pip install -r requirements.txt
```

## 1. 单个发布

立即发布单个交付包到指定平台。

### 基本用法

```bash
# 发布到所有已启用的平台
python src/main.py publish --package '/path/to/package'

# 发布到指定平台
python src/main.py publish --package '/path/to/package' --platforms bilibili
python src/main.py publish --package '/path/to/package' --platforms bilibili --platforms douyin
```

### 参数说明

- `--package, -p`: 交付包路径（必填）
- `--platforms, -t`: 指定要发布的平台，可多次使用（可选）
  - 可选值: `bilibili`, `douyin`, `xiaohongshu`
  - 不指定则发布到配置文件中所有已启用的平台

## 2. 批量发布

批量处理 `packages/` 目录下的所有交付包。

### 基本用法

```bash
# 使用默认参数批量发布
python src/main.py batch

# 自定义并发数和重试次数
python src/main.py batch --concurrent 5 --retry 3

# 指定平台
python src/main.py batch --platforms bilibili --platforms xiaohongshu
```

### 参数说明

- `--platforms, -t`: 指定要发布的平台，可多次使用（可选）
- `--concurrent, -c`: 最大并发数，默认 3（可选）
- `--retry, -r`: 失败重试次数，默认 2（可选）
- `--skip-existing`: 跳过已发布的包，默认开启（可选）

### 功能特性

- ✅ 并发上传，提高效率
- ✅ 自动重试失败的任务
- ✅ 进度条实时显示
- ✅ 跳过已发布的包
- ✅ 生成批量发布报告

### 批量发布报告

报告保存在 `output/reports/batch_YYYYMMDD_HHMMSS.json`，包含：
- 总体统计（成功/失败/跳过）
- 每个包的发布结果
- 各平台的详细信息

## 3. 定时发布

设置定时发布任务，支持一次性和重复发布。

### 3.1 添加定时任务

```bash
# 30分钟后发布
python src/main.py schedule --package '/path/to/package' --time '+30m'

# 2小时后发布
python src/main.py schedule --package '/path/to/package' --time '+2h'

# 指定具体时间
python src/main.py schedule --package '/path/to/package' --time '2024-03-20 14:30'

# 每天同一时间发布
python src/main.py schedule --package '/path/to/package' --time '2024-03-20 09:00' --repeat daily

# 每周同一时间发布
python src/main.py schedule --package '/path/to/package' --time '2024-03-20 09:00' --repeat weekly

# 每月同一时间发布
python src/main.py schedule --package '/path/to/package' --time '2024-03-20 09:00' --repeat monthly

# 使用 cron 表达式（每天 9:00 和 18:00）
python src/main.py schedule --package '/path/to/package' --time '2024-03-20 09:00' --repeat '0 9,18 * * *'
```

### 3.2 查看定时任务

```bash
python src/main.py list-schedules
```

### 3.3 移除定时任务

```bash
python src/main.py remove-schedule <schedule_id>
```

### 3.4 启动调度器

添加任务后，需要启动调度器来执行定时任务：

```bash
python src/main.py run-scheduler
```

调度器会持续运行，按计划执行所有定时任务。按 `Ctrl+C` 停止。

### 参数说明

- `--package, -p`: 交付包路径（必填）
- `--time, -t`: 发布时间（必填）
  - 相对时间: `+30m`, `+2h`, `+1d`
  - 绝对时间: `2024-03-20 14:30`
- `--platforms, -pf`: 指定平台，可多次使用（可选）
- `--repeat`: 重复规则（可选）
  - `daily` - 每天
  - `weekly` - 每周
  - `monthly` - 每月
  - cron 表达式 - 自定义（格式: `分 时 日 月 周`）

### 功能特性

- ✅ 支持相对时间和绝对时间
- ✅ 支持一次性和重复发布
- ✅ 自定义 cron 表达式
- ✅ 任务持久化存储
- ✅ 自动保存发布记录

### 定时任务存储

- 任务配置: `output/schedules.json`
- 发布记录: `output/records/scheduled_*.json`

## 配置文件

### 平台配置 (`config/platforms.json`)

```json
{
  "bilibili": {
    "enabled": true,
    "cookies": "your_cookies_here",
    "csrf": "your_csrf_here"
  },
  "douyin": {
    "enabled": true,
    "cookies": "your_cookies_here"
  },
  "xiaohongshu": {
    "enabled": true,
    "cookie": "your_cookie_here",
    "a1": "your_a1_here"
  }
}
```

## 使用示例

### 场景 1: 立即发布单个视频

```bash
python src/main.py publish --package './packages/video1'
```

### 场景 2: 批量发布多个视频

1. 将所有交付包放入 `packages/` 目录
2. 运行批量发布命令：

```bash
python src/main.py batch --concurrent 5
```

### 场景 3: 定时发布

1. 添加定时任务：

```bash
# 明天早上 9:00 发布
python src/main.py schedule --package './packages/video1' --time '2024-03-21 09:00'
```

2. 启动调度器：

```bash
python src/main.py run-scheduler
```

### 场景 4: 重复发布

```bash
# 每天早上 9:00 发布
python src/main.py schedule \
  --package './packages/daily_video' \
  --time '2024-03-20 09:00' \
  --repeat daily

# 启动调度器
python src/main.py run-scheduler
```

## 故障排查

### 1. 导入错误

确保已安装所有依赖：

```bash
pip install -r requirements.txt
```

### 2. Cookie 过期

如果发布失败，检查 `config/platforms.json` 中的 cookies 是否过期。

### 3. 调度器未执行任务

- 确保调度器正在运行（`run-scheduler` 命令）
- 检查任务时间是否在未来
- 查看 `output/schedules.json` 确认任务已添加

### 4. 批量发布报错

- 检查 `packages/` 目录是否存在
- 确保交付包格式正确
- 降低并发数（`--concurrent 1`）逐个排查

## 日志

日志文件保存在项目根目录，查看详细错误信息：

```bash
tail -f *.log
```

## 技术支持

如有问题，请查看：
- 日志文件
- 发布报告 (`output/reports/`)
- 发布记录 (`output/records/`)
