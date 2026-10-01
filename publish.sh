#!/bin/bash
# 一键发布脚本 - 发布交付包到所有平台

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  视频自动发布工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查是否提供了交付包路径
if [ $# -eq 0 ]; then
    echo -e "${RED}错误: 请提供交付包路径${NC}"
    echo ""
    echo "用法:"
    echo "  ./publish.sh <交付包路径> [平台]"
    echo ""
    echo "示例:"
    echo "  ./publish.sh '/Users/a123/Desktop/新时代三件套-交付包-重制版'"
    echo "  ./publish.sh '/Users/a123/Desktop/新时代三件套-交付包-重制版' bilibili"
    echo "  ./publish.sh '/Users/a123/Desktop/新时代三件套-交付包-重制版' 'bilibili douyin'"
    exit 1
fi

PACKAGE_PATH="$1"
PLATFORMS="${2:-}"

# 检查交付包是否存在
if [ ! -d "$PACKAGE_PATH" ]; then
    echo -e "${RED}错误: 交付包不存在: $PACKAGE_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 找到交付包: $PACKAGE_PATH${NC}"
echo ""

# 激活虚拟环境（如果有）
if [ -d "venv" ]; then
    echo -e "${BLUE}激活虚拟环境...${NC}"
    source venv/bin/activate
fi

# 运行发布程序
echo -e "${BLUE}开始发布...${NC}"
echo ""

if [ -n "$PLATFORMS" ]; then
    # 指定平台
    PLATFORM_ARGS=""
    for platform in $PLATFORMS; do
        PLATFORM_ARGS="$PLATFORM_ARGS --platforms $platform"
    done
    python src/main.py publish --package "$PACKAGE_PATH" $PLATFORM_ARGS
else
    # 所有平台
    python src/main.py publish --package "$PACKAGE_PATH"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  发布完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "查看详细日志: output/"
