# ⚡ 快速运行指南

## 当前状态

✅ 项目已创建完成
✅ 基础依赖已安装
✅ 提取功能已测试成功

## 🎯 现在就可以测试

### 1. 测试提取功能（已成功）

```bash
cd /Users/a123/Desktop/video-auto-publisher
python3 test_extract.py
```

**结果：**
```
✅ 标题: 新时代三件套：自媒体、AI、金融，为什么要一起做？
✅ 视频: 成片.mp4
✅ 封面: 封面-4x3.png
✅ B站标题: 新时代三件套：自媒体、AI、金融，2分钟画清个人增长循环
✅ 小红书标题: 新时代三件套，普通人怎么把机会接起来？
```

### 2. 配置发布平台

打开配置文件编辑：
```bash
open config/platforms.json
```

#### B站配置（推荐先配置）

1. 打开浏览器，登录 https://member.bilibili.com/
2. 按 F12 打开开发者工具
3. 切换到 **Application** → **Cookies** → **bilibili.com**
4. 找到这两个值：
   - `SESSDATA` - 复制整个值
   - `bili_jct` - 复制整个值
5. 编辑 `config/platforms.json`：
   ```json
   {
     "bilibili": {
       "enabled": true,
       "cookies": "粘贴SESSDATA的值",
       "csrf": "粘贴bili_jct的值"
     }
   }
   ```

#### 抖音和小红书（可选）

这两个平台使用浏览器自动化，只需要设置：
```json
{
  "douyin": {
    "enabled": true
  },
  "xiaohongshu": {
    "enabled": true
  }
}
```

首次运行时会打开浏览器，手动登录即可。

### 3. 发布视频

配置好后，运行：

```bash
# 发布到所有启用的平台
./publish.sh "/Users/a123/Desktop/新时代三件套-交付包-重制版"

# 或者只发布到 B站
./publish.sh "/Users/a123/Desktop/新时代三件套-交付包-重制版" bilibili

# 或者使用 Python
python3 src/main.py --package "/Users/a123/Desktop/新时代三件套-交付包-重制版"
```

## 📝 注意事项

### B站凭证获取详细步骤

1. **登录 B站创作中心**
   - 访问：https://member.bilibili.com/
   - 确保已登录

2. **打开开发者工具**
   - Windows: `F12` 或 `Ctrl+Shift+I`
   - Mac: `Cmd+Option+I`

3. **找到 Cookies**
   - 点击顶部 **Application** 标签（Chrome）
   - 或 **存储** 标签（Firefox）
   - 左侧展开 **Cookies** → 点击 **https://member.bilibili.com**

4. **复制值**
   - 找到 `SESSDATA` 这一行，双击右侧的值，全选复制
   - 找到 `bili_jct` 这一行，双击右侧的值，全选复制

5. **粘贴到配置文件**
   ```json
   {
     "bilibili": {
       "enabled": true,
       "cookies": "这里粘贴SESSDATA的完整值",
       "csrf": "这里粘贴bili_jct的完整值"
     }
   }
   ```

### 常见问题

**Q: SESSDATA 多久过期？**
A: 通常 1-3 个月，过期后重新获取即可。

**Q: 可以只发布到一个平台吗？**
A: 可以，只启用想发布的平台即可，或使用命令：
```bash
./publish.sh "包路径" bilibili
```

**Q: 能批量发布吗？**
A: 可以，将多个交付包放入 `packages/` 目录，然后：
```bash
python3 src/main.py --batch
```

**Q: 发布失败怎么办？**
A: 查看 `output/` 目录的日志文件，里面有详细错误信息。

## 🎉 准备好了！

现在：
1. ✅ 编辑 `config/platforms.json` 填写 B站凭证
2. ✅ 运行 `./publish.sh "交付包路径" bilibili` 测试
3. ✅ 确认无误后启用其他平台

祝发布顺利！
