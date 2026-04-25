# FFmpeg 安装说明

音源分离功能需要 FFmpeg 支持。请按以下步骤安装：

## Windows 用户

1. 下载 FFmpeg:
   - 访问: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
   - 或使用镜像: https://github.com/BtbN/FFmpeg-Builds/releases

2. 解压下载的 zip 文件

3. 将以下文件复制到本目录 (`tools/ffmpeg/`):
   - `ffmpeg.exe`
   - `ffprobe.exe`

4. 目录结构应为:
   ```
   AutoMidi/
   └── tools/
       └── ffmpeg/
           ├── ffmpeg.exe
           └── ffprobe.exe
   ```

## 替代方案

如果不想手动下载，可以安装 imageio-ffmpeg:

```bash
pip install imageio-ffmpeg
```

程序会自动检测并使用 imageio-ffmpeg 提供的 ffmpeg。

## 打包说明

打包时，PyInstaller 会自动将 `tools/ffmpeg` 目录中的文件包含到最终程序中。
