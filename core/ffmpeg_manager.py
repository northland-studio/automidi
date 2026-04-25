import os
import sys
import subprocess
from pathlib import Path
from typing import Optional, Tuple


def get_ffmpeg_dir() -> Optional[str]:
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent
    
    ffmpeg_dir = base_path / "tools" / "ffmpeg"
    if ffmpeg_dir.exists():
        return str(ffmpeg_dir)
    
    return None


def get_ffmpeg_exe() -> Optional[str]:
    ffmpeg_dir = get_ffmpeg_dir()
    if ffmpeg_dir:
        if sys.platform == 'win32':
            exe_path = Path(ffmpeg_dir) / "ffmpeg.exe"
        else:
            exe_path = Path(ffmpeg_dir) / "ffmpeg"
        
        if exe_path.exists():
            return str(exe_path)
    
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
        if result.returncode == 0:
            return 'ffmpeg'
    except FileNotFoundError:
        pass
    
    return None


def get_ffprobe_exe() -> Optional[str]:
    ffmpeg_dir = get_ffmpeg_dir()
    if ffmpeg_dir:
        if sys.platform == 'win32':
            exe_path = Path(ffmpeg_dir) / "ffprobe.exe"
        else:
            exe_path = Path(ffmpeg_dir) / "ffprobe"
        
        if exe_path.exists():
            return str(exe_path)
    
    try:
        import imageio_ffmpeg
        ffmpeg_path = Path(imageio_ffmpeg.get_ffmpeg_exe())
        ffprobe_path = ffmpeg_path.parent / ('ffprobe.exe' if sys.platform == 'win32' else 'ffprobe')
        if ffprobe_path.exists():
            return str(ffprobe_path)
    except ImportError:
        pass
    
    try:
        result = subprocess.run(['ffprobe', '-version'], capture_output=True)
        if result.returncode == 0:
            return 'ffprobe'
    except FileNotFoundError:
        pass
    
    return None


def setup_ffmpeg_env() -> Tuple[bool, str]:
    ffmpeg_exe = get_ffmpeg_exe()
    ffprobe_exe = get_ffprobe_exe()
    
    if ffmpeg_exe and ffprobe_exe:
        ffmpeg_dir = str(Path(ffmpeg_exe).parent)
        
        current_path = os.environ.get('PATH', '')
        if ffmpeg_dir not in current_path:
            os.environ['PATH'] = ffmpeg_dir + os.pathsep + current_path
        
        os.environ['FFMPEG_BINARY'] = ffmpeg_exe
        os.environ['FFPROBE_BINARY'] = ffprobe_exe
        
        return True, f"ffmpeg 已配置: {ffmpeg_dir}"
    
    return False, (
        "ffmpeg/ffprobe 未找到。\n\n"
        "解决方案:\n"
        "1. 下载 ffmpeg: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip\n"
        "2. 解压后将 ffmpeg.exe 和 ffprobe.exe 放到项目的 tools/ffmpeg 目录\n"
        "3. 或运行: pip install imageio-ffmpeg"
    )


def check_ffmpeg_available() -> bool:
    ffmpeg_exe = get_ffmpeg_exe()
    ffprobe_exe = get_ffprobe_exe()
    return ffmpeg_exe is not None and ffprobe_exe is not None
