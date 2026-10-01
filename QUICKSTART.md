# 视频自动发布工具 - 快速开始指南

## 1. 安装依赖

```bash
cd /Users/a123/Desktop/video-auto-publisher
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

## 2. 配置平台账号

### 方法一：直接编辑配置文件

编辑 `config/platforms.json`，填入你的账号信息。

### 方法二：获取 Cookies（推荐）

#### B站 Cookies 获取：
1. 在浏览器中登录 B站创作中心：https://member.bilibili.com/
2. 打开开发者工具（F12）
3. 切换到 Network 标签
4. 刷新页面
5. 找到任意请求，查看 Request Headers
6. 复制 `Cookie` 中的 `SESSDATA` 值
7. 复制 `bili_jct` 的值（这是 csrf token）

将这两个值填入 `config/platforms.json` 的 bilibili 部分：
```json
{
  "bilibili": {
    "enabled": true,
    "cookies": "your_SESSDATA_here",
    "csrf": "your_bili_jct_here"
  }
}
```

#### 抖音/小红书：
由于这两个平台使用浏览器自动化，第一次运行时会打开浏览器，你需要手动登录。
之后程序会保持登录状态。

## 3. 准备交付包

将你的视频交付包复制到 `packages/` 目录：

```bash
cp -r "/Users/a123/Desktop/新时代三件套-交付包-重制版" packages/
```

## 4. 测试提取功能

先测试一下能否正确提取交付包信息：

```bash
cd /Users/a123/Desktop/video-auto-publisher
python src/extractors/package_extractor.py
```

## 5. 发布视频

### 发布到单个平台（仅B站）：
```bash
python src/main.py --package "packages/新时代三件套-交付包-重制版" --platforms bilibili
```

### 发布到所有平台：
```bash
python src/main.py --package "packages/新时代三件套-交付包-重制版"
```

### 批量发布多个包：
```bash
python src/main.py --batch
```

## 6. 查看结果

发布完成后，查看 `output/` 目录：
- `publish_*.log` - 详细日志
- `record_*.json` - 发布记录

## 注意事项

### B站：
- ✅ 使用官方 API，稳定可靠
- ⚠️ 需要正确配置 SESSDATA 和 csrf token
- ⚠️ 首次使用建议先发布到"仅自己可见"测试

### 抖音/小红书：
- ⚠️ 使用浏览器自动化，需要手动登录
- ⚠️ 程序会打开浏览器窗口，不要关闭
- ⚠️ 需要手动点击最后的"发布"按钮（或等待自动点击）
- 💡 首次运行建议保持浏览器可见，观察自动化过程

## 常见问题

**Q: B站上传失败，提示 "credential error"？**
A: 检查你的 SESSDATA 和 csrf token 是否正确，是否过期。

**Q: 抖音/小红书一直卡在登录页面？**
A: 需要手动在打开的浏览器中登录，程序会等待30秒。

**Q: 如何只发布到某个平台？**
A: 使用 `--platforms` 参数指定，例如：`--platforms bilibili`

**Q: 可以定时发布吗？**
A: 目前版本不支持，后续可以配合系统的 cron 实现。

## 下一步

1. 先用测试账号验证功能
2. 确认各平台的发布规范
3. 批量处理多个交付包
4. 查看日志排查问题
