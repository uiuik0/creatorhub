# 🚀 开始使用

欢迎使用视频自动发布工具！这个工具可以帮你一键将视频交付包发布到 B站、抖音、小红书三个平台。

## 📍 你现在在这里

项目位置：`/Users/a123/Desktop/video-auto-publisher/`

## ⚡ 三步开始

### 1️⃣ 安装依赖（首次使用）

```bash
cd /Users/a123/Desktop/video-auto-publisher
./install.sh
```

这会自动安装所有需要的 Python 库和浏览器驱动。

### 2️⃣ 配置账号

```bash
python setup_config.py
```

按照提示配置：
- **B站**：需要从浏览器获取 `SESSDATA` 和 `bili_jct`
- **抖音/小红书**：首次运行时手动登录即可

### 3️⃣ 发布视频

```bash
./publish.sh "/Users/a123/Desktop/新时代三件套-交付包-重制版"
```

或者只发布到 B站（测试推荐）：

```bash
./publish.sh "/Users/a123/Desktop/新时代三件套-交付包-重制版" bilibili
```

---

## 📚 更多信息

- 📄 **PROJECT_SUMMARY.md** - 完整的项目总结和功能说明
- 📄 **QUICKSTART.md** - 详细的快速开始指南
- 📄 **README.md** - 完整的项目文档
- 📖 **examples.py** - 代码使用示例

---

## ✅ 测试结果

工具已成功解析你的示例交付包：

```
✅ 标题: 新时代三件套：自媒体、AI、金融，为什么要一起做？
✅ 视频: 成片.mp4
✅ 封面: 封面-4x3.png
✅ B站标题: 新时代三件套：自媒体、AI、金融，2分钟画清个人增长循环
✅ 小红书标题: 新时代三件套，普通人怎么把机会接起来？
```

你可以运行 `python test_extract.py` 查看完整提取结果。

---

## 🎯 推荐流程

**首次使用建议：**

1. ✅ 先配置 B站（最稳定，使用官方 API）
2. ✅ 只发布到 B站测试一次
3. ✅ 确认无误后，再配置抖音和小红书
4. ✅ 最后一键发布到所有平台

**命令示例：**

```bash
# 步骤 1: 配置
python setup_config.py

# 步骤 2: 测试提取
python test_extract.py

# 步骤 3: 发布到 B站测试
./publish.sh "/Users/a123/Desktop/新时代三件套-交付包-重制版" bilibili

# 步骤 4: 发布到所有平台
./publish.sh "/Users/a123/Desktop/新时代三件套-交付包-重制版"
```

---

## ⚠️ 重要提示

- B站需要从浏览器 cookies 获取凭证（会过期，需要重新获取）
- 抖音和小红书使用浏览器自动化，会打开浏览器窗口
- 首次发布建议设置为"仅自己可见"测试
- 配置文件 `config/platforms.json` 包含敏感信息，不要分享

---

## 🆘 遇到问题？

1. 查看 `output/` 目录的日志文件
2. 阅读 `QUICKSTART.md` 的故障排除部分
3. 运行 `python test_extract.py` 测试提取功能

---

**祝你发布顺利！** 🎉

如有疑问，随时查看 `PROJECT_SUMMARY.md` 获取完整说明。
