@echo off
chcp 65001 >nul
echo ========================================
echo   AutoMidi 打包脚本
echo   开发者: 北域工作室
echo ========================================
echo.

if not exist "tools\ffmpeg\ffmpeg.exe" (
    echo [警告] 未找到 tools\ffmpeg\ffmpeg.exe
    echo 请先下载 ffmpeg 并放置到 tools\ffmpeg 目录:
    echo   1. 访问 https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
    echo   2. 解压后将 ffmpeg.exe 和 ffprobe.exe 复制到 tools\ffmpeg 目录
    echo.
    echo 按任意键继续打包（不包含ffmpeg）...
    pause >nul
)

echo [1/3] 检查依赖...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 正在安装 PyInstaller...
    pip install pyinstaller
)

echo.
echo [2/3] 开始打包...
pyinstaller AutoMidi.spec --clean

echo.
echo [3/3] 打包完成！
echo.
echo 输出目录: dist\AutoMidi
echo.
pause
