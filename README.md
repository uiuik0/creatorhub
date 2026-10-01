# 🎬 视频自动发布工具

一键将视频交付包发布到 B站、抖音、小红书 三个平台的自动化工具。

## ✨ 特性

- ✅ **智能提取** - 自动识别交付包中的视频、封面、字幕、标题、描述等
- 🎯 **平台适配** - 自动为各平台生成合适的标题、描述和标签
- 🚀 **一键发布** - 支持单平台或多平台同时发布
- 📊 **结果追踪** - 详细的发布日志和结果记录
- 🎨 **封面处理** - 自动调整封面尺寸以适配各平台要求

## 📁 项目结构

```
video-auto-publisher/
├── src/
│   ├── extractors/          # 交付包解析器
│   │   └── package_extractor.py
│   ├── publishers/          # 平台发布器
│   │   ├── bilibili_publisher.py
│   │   ├── douyin_publisher.py
│   │   └── xiaohongshu_publisher.py
│   └── main.py             # 主程序
├── config/
│   ├── platforms.json      # 平台配置
│   ├── platforms.json.template  # 配置模板
│   └── rules.json         # 发布规则
├── packages/              # 待发布的交付包
├── output/                # 发布日志和结果
├── publish.sh            # 一键发布脚本
├── test_extract.py       # 测试脚本
├── QUICKSTART.md         # 快速开始指南
└── requirements.txt      # Python 依赖
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd /Users/a123/Desktop/video-auto-publisher
pip install -r requirements.txt

# 安装浏览器（用于抖音和小红书）
playwright install chromium
```

### 2. 配置账号

复制配置模板并填入你的账号信息：

```bash
cp config/platforms.json.template config/platforms.json
# 编辑 config/platforms.json，填入你的 B站 SESSDATA 和 csrf token
```

### 3. 测试提取功能

```bash
python test_extract.py
```

### 4. 发布视频

```bash
# 方法一：使用脚本（推荐）
./publish.sh "/Users/a123/Desktop/新时代三件套-交付包-重制版"

# 方法二：直接运行 Python
python src/main.py --package "/Users/a123/Desktop/新时代三件套-交付包-重制版"

# 只发布到 B站
./publish.sh "/Users/a123/Desktop/新时代三件套-交付包-重制版" bilibili
```

## 📦 支持的交付包格式

工具会自动识别标准交付包中的以下文件：

### 必需文件：
- **视频文件**: `成片.mp4`, `final.mp4` 或任何 `.mp4` 文件
- **发布文案**: `发布.md` - 包含各平台的标题、描述等

### 可选文件：
- **封面图**: `封面-*.png`, `cover.png` 等
- **字幕文件**: `字幕.srt`, `*.srt` 等
- **旁白稿**: `旁白稿.md` - 用于提取描述
- **README**: `README.md` - 备用标题和描述来源

### 示例交付包结构：

```
新时代三件套-交付包-重制版/
├── 成片.mp4           # 视频文件
├── 封面-4x3.png       # 封面图
├── 封面-3x4.png       # 封面图（备用）
├── 字幕.srt          # 字幕文件
├── 发布.md           # 发布文案（各平台标题描述）
├── 旁白稿.md         # 旁白稿
├── README.md         # 项目说明
└── assets/           # 其他素材
```

## 🎯 平台说明

### B站（哔哩哔哩）

- ✅ 使用官方 API，稳定可靠
- 📝 需要配置 `SESSDATA` 和 `csrf` token
- 🎨 封面自动调整为 16:9 (1920x1080)
- 🏷️ 最多支持 12 个标签

**如何获取凭证：**
1. 登录 [B站创作中心](https://member.bilibili.com/)
2. 打开浏览器开发者工具（F12）
3. Application > Cookies > bilibili.com
4. 复制 `SESSDATA` 和 `bili_jct` 的值

### 抖音

- 🤖 使用浏览器自动化
- 🔐 首次运行需要手动登录
- 📏 标题限制 55 字符
- 🏷️ 最多支持 5 个话题标签
- ⏱️ 程序会等待你确认后发布

### 小红书

- 🤖 使用浏览器自动化
- 🔐 首次运行需要手动登录
- 📏 标题限制 20 字符
- 📝 正文限制 1000 字符
- 🏷️ 最多支持 10 个话题标签
- ⏱️ 程序会等待你确认后发布

## 📋 使用示例

### 发布到所有平台

```bash
./publish.sh "/Users/a123/Desktop/新时代三件套-交付包-重制版"
```

### 只发布到 B站（测试推荐）

```bash
./publish.sh "/Users/a123/Desktop/新时代三件套-交付包-重制版" bilibili
```

### 批量发布多个交付包

```bash
# 将所有交付包放入 packages/ 目录
cp -r "/Users/a123/Desktop/新时代三件套-交付包-重制版" packages/
cp -r "/Users/a123/Desktop/其他视频-交付包" packages/

# 批量发布
python src/main.py --batch
```

### 发布到指定平台

```bash
python src/main.py --package "packages/新时代三件套-交付包-重制版" --platforms bilibili --platforms douyin
```

## 📊 查看结果

发布完成后，查看 `output/` 目录：

```bash
ls -lh output/

# 查看最新日志
tail -f output/publish_*.log

# 查看发布记录
cat output/record_*.json
```

## ⚠️ 注意事项

1. **首次使用建议先用测试账号验证**
2. **B站需要正确的 SESSDATA，过期需要重新获取**
3. **抖音和小红书首次需要手动登录**
4. **建议先发布"仅自己可见"测试**
5. **遵守各平台的发布频率限制**
6. **不要在浏览器自动化过程中关闭浏览器**

## 🔧 故障排除

### B站上传失败

```bash
# 检查配置
cat config/platforms.json | grep -A 5 bilibili

# 重新获取 SESSDATA（可能已过期）
```

### 抖音/小红书卡在登录页面

- 在打开的浏览器中手动登录
- 程序会等待 30 秒
- 登录成功后程序会自动继续

### 找不到视频文件

```bash
# 测试提取功能
python test_extract.py

# 确保交付包包含 成片.mp4 或 final.mp4
```

## 🛠️ 高级配置

### 自定义发布规则

编辑 `config/rules.json` 来自定义：
- 标题转换规则
- 描述模板
- 标签生成规则
- 封面选择优先级
- 视频处理参数

### 环境变量

```bash
# 设置日志级别
export LOG_LEVEL=DEBUG

# 设置超时时间
export UPLOAD_TIMEOUT=600
```

## 📝 开发计划

- [ ] 支持定时发布
- [ ] 支持视频预处理（压缩、转码）
- [ ] 支持更多平台（快手、视频号等）
- [ ] Web 管理界面
- [ ] 发布队列管理
- [ ] 发布数据统计

## 📄 许可证

MIT License

---

**提示**: 详细使用说明请查看 [QUICKSTART.md](./QUICKSTART.md)
