#!/bin/bash
# 一键打开配置文件

echo "📝 打开配置文件编辑器..."
echo ""
echo "请填写以下信息："
echo ""
echo "B站配置："
echo "  1. 访问 https://member.bilibili.com/ 并登录"
echo "  2. 按 F12 打开开发者工具"
echo "  3. Application → Cookies → bilibili.com"
echo "  4. 复制 SESSDATA 和 bili_jct 的值"
echo "  5. 将 enabled 改为 true"
echo ""
echo "抖音/小红书："
echo "  只需将 enabled 改为 true 即可"
echo "  首次运行会打开浏览器手动登录"
echo ""

# 打开配置文件
if [[ "$OSTYPE" == "darwin"* ]]; then
    open config/platforms.json
else
    ${EDITOR:-nano} config/platforms.json
fi

echo "✅ 配置文件已打开"
echo ""
echo "配置完成后，运行以下命令测试："
echo "./publish.sh \"/Users/a123/Desktop/新时代三件套-交付包-重制版\" bilibili"
