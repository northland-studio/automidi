#!/bin/bash
echo "========================================"
echo "  AutoMidi 打包脚本"
echo "  开发者: 北域工作室"
echo "========================================"
echo

if [ ! -f "tools/ffmpeg/ffmpeg" ]; then
    echo "[警告] 未找到 tools/ffmpeg/ffmpeg"
    echo "请先下载 ffmpeg 并放置到 tools/ffmpeg 目录"
    echo
    read -p "按回车继续打包（不包含ffmpeg）..."
fi

echo "[1/3] 检查依赖..."
if ! pip show pyinstaller > /dev/null 2>&1; then
    echo "正在安装 PyInstaller..."
    pip install pyinstaller
fi

echo
echo "[2/3] 开始打包..."
pyinstaller AutoMidi.spec --clean

echo
echo "[3/3] 打包完成！"
echo
echo "输出目录: dist/AutoMidi"
