#!/bin/bash
# 定时发布脚本 - 添加定时任务并启动调度器

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  定时发布工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 显示使用说明
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}用法:${NC}"
    echo "  ./schedule.sh <交付包路径> <时间> [选项]"
    echo ""
    echo -e "${YELLOW}时间格式:${NC}"
    echo "  相对时间: +30m (30分钟后), +2h (2小时后), +1d (1天后)"
    echo "  绝对时间: '2026-10-01 20:00'"
    echo ""
    echo -e "${YELLOW}选项:${NC}"
    echo "  --repeat daily     每天重复"
    echo "  --repeat weekly    每周重复"
    echo "  --repeat monthly   每月重复"
    echo "  --platforms <平台> 指定平台（可多次使用）"
    echo ""
    echo -e "${YELLOW}示例:${NC}"
    echo "  # 30分钟后发布"
    echo "  ./schedule.sh '/Users/a123/Desktop/新时代三件套-交付包-重制版' '+30m'"
    echo ""
    echo "  # 今晚8点发布"
    echo "  ./schedule.sh '/Users/a123/Desktop/新时代三件套-交付包-重制版' '2026-10-01 20:00'"
    echo ""
    echo "  # 每天早上9点发布"
    echo "  ./schedule.sh '/Users/a123/Desktop/新时代三件套-交付包-重制版' '2026-10-02 09:00' --repeat daily"
    echo ""
    echo "  # 指定平台"
    echo "  ./schedule.sh '/Users/a123/Desktop/新时代三件套-交付包-重制版' '+1h' --platforms bilibili"
    echo ""
    exit 0
fi

PACKAGE_PATH="$1"
TIME="$2"
shift 2

# 检查交付包是否存在
if [ ! -d "$PACKAGE_PATH" ]; then
    echo -e "${RED}错误: 交付包不存在: $PACKAGE_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 交付包: $PACKAGE_PATH${NC}"
echo -e "${GREEN}✓ 发布时间: $TIME${NC}"

# 激活虚拟环境（如果有）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 添加定时任务
echo ""
echo -e "${BLUE}添加定时任务...${NC}"
python src/main.py schedule --package "$PACKAGE_PATH" --time "$TIME" "$@"

echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  提示: 调度器需要保持运行才能执行任务${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "选择操作:"
echo "  1) 立即启动调度器（前台运行）"
echo "  2) 后台运行调度器"
echo "  3) 查看任务列表"
echo "  4) 退出"
echo ""
read -p "请选择 [1-4]: " choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}启动调度器...${NC}"
        echo -e "${YELLOW}按 Ctrl+C 停止调度器${NC}"
        echo ""
        python src/main.py run-scheduler
        ;;
    2)
        echo ""
        echo -e "${GREEN}后台启动调度器...${NC}"
        nohup python src/main.py run-scheduler > scheduler.log 2>&1 &
        PID=$!
        echo -e "${GREEN}✓ 调度器已在后台运行 (PID: $PID)${NC}"
        echo ""
        echo "管理命令:"
        echo "  查看日志: tail -f scheduler.log"
        echo "  停止调度器: kill $PID"
        ;;
    3)
        echo ""
        python src/main.py list-schedules
        echo ""
        echo -e "${YELLOW}提示: 使用以下命令启动调度器${NC}"
        echo "  python src/main.py run-scheduler"
        ;;
    *)
        echo ""
        echo -e "${YELLOW}任务已添加，请手动启动调度器:${NC}"
        echo "  python src/main.py run-scheduler"
        ;;
esac
