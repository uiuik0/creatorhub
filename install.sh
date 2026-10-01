#!/bin/bash
# 安装脚本 - 自动安装所有依赖

set -e

echo "========================================"
echo "  视频自动发布工具 - 安装脚本"
echo "========================================"
echo ""

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ 检测到 Python: $python_version"

# 创建虚拟环境（可选）
if [ ! -d "venv" ]; then
    echo ""
    read -p "是否创建虚拟环境？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "创建虚拟环境..."
        python3 -m venv venv
        source venv/bin/activate
        echo "✓ 虚拟环境已创建并激活"
    fi
else
    echo "✓ 发现现有虚拟环境"
    source venv/bin/activate
fi

# 安装 Python 依赖
echo ""
echo "安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✓ Python 依赖安装完成"

# 安装 Playwright 浏览器
echo ""
echo "安装 Playwright 浏览器（用于抖音和小红书）..."
playwright install chromium

echo ""
echo "✓ Playwright 浏览器安装完成"

# 创建必要的目录
echo ""
echo "创建必要的目录..."
mkdir -p packages
mkdir -p output
mkdir -p config

echo "✓ 目录创建完成"

# 配置账号
echo ""
echo "========================================"
echo "  安装完成！"
echo "========================================"
echo ""
echo "下一步："
echo "  1. 运行配置向导: python setup_config.py"
echo "  2. 测试提取功能: python test_extract.py"
echo "  3. 发布视频: ./publish.sh '/path/to/package'"
echo ""
