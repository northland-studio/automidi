import numpy as np
import os
import subprocess
from typing import Optional, List, Dict
from pathlib import Path
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal

from .logger import logger


@dataclass
class SeparatedTrack:
    name: str
    audio_data: np.ndarray
    sample_rate: int


class SourceSeparator(QObject):
    progress_updated = Signal(int)
    separation_finished = Signal(dict)
    error_occurred = Signal(str)
    
    TRACK_NAMES = ['drums', 'bass', 'other', 'vocals']
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._separated_tracks: Dict[str, SeparatedTrack] = {}
        self._model_name = "htdemucs"
        self._is_available = False
        self._separator = None
        self._has_new_api = False
        self._ffmpeg_path: Optional[str] = None
        self._check_availability()
    
    def _check_availability(self) -> None:
        try:
            import demucs
            self._is_available = True
            try:
                from demucs.api import Separator
                self._has_new_api = True
                logger.info("demucs 可用 (新API)")
            except ImportError:
                self._has_new_api = False
                logger.info("demucs 可用 (旧API)")
            
            self._setup_ffmpeg()
                
        except ImportError:
            self._is_available = False
            logger.warning("demucs 未安装")
    
    def _setup_ffmpeg(self) -> bool:
        try:
            import imageio_ffmpeg
            self._ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            ffmpeg_dir = str(Path(self._ffmpeg_path).parent)
            
            current_path = os.environ.get('PATH', '')
            if ffmpeg_dir not in current_path:
                os.environ['PATH'] = ffmpeg_dir + os.pathsep + current_path
            
            ffmpeg_exe = self._ffmpeg_path
            ffprobe_exe = str(Path(self._ffmpeg_path).parent / 'ffprobe.exe')
            
            if not os.path.exists(ffprobe_exe):
                ffprobe_exe = self._ffmpeg_path
            
            os.environ['FFMPEG_BINARY'] = ffmpeg_exe
            os.environ['FFPROBE_BINARY'] = ffprobe_exe
            
            logger.info(f"使用内置 ffmpeg: {self._ffmpeg_path}")
            return True
            
        except ImportError:
            logger.debug("imageio-ffmpeg 未安装，尝试系统 ffmpeg")
            return self._check_system_ffmpeg()
        except Exception as e:
            logger.warning(f"设置内置 ffmpeg 失败: {str(e)}")
            return self._check_system_ffmpeg()
    
    def _check_system_ffmpeg(self) -> bool:
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
            logger.info("使用系统 ffmpeg")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("ffmpeg/ffprobe 未找到")
            return False
    
    def _check_ffmpeg(self) -> bool:
        if self._ffmpeg_path:
            return True
        
        try:
            import imageio_ffmpeg
            self._ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            return True
        except ImportError:
            pass
        
        return self._check_system_ffmpeg()
    
    @property
    def is_available(self) -> bool:
        return self._is_available
    
    def set_model(self, model_name: str) -> None:
        self._model_name = model_name
        self._separator = None
        logger.info(f"设置分离模型: {model_name}")
    
    def separate(self, audio_path: str) -> Dict[str, SeparatedTrack]:
        if not self._is_available:
            raise ImportError("demucs 未安装，请运行: pip install demucs")
        
        if not self._check_ffmpeg():
            raise RuntimeError(
                "ffmpeg/ffprobe 未安装。\n"
                "请安装:\n"
                "- pip install imageio-ffmpeg (推荐，自动内置)\n"
                "- 或从 https://ffmpeg.org/download.html 下载并添加到 PATH"
            )
        
        logger.info(f"开始分离音频: {audio_path}")
        self.progress_updated.emit(5)
        
        try:
            if self._has_new_api:
                return self._separate_new_api(audio_path)
            else:
                return self._separate_old_api(audio_path)
        except Exception as e:
            logger.exception(f"音源分离失败: {str(e)}")
            self.error_occurred.emit(f"音源分离失败: {str(e)}")
            raise
    
    def _separate_new_api(self, audio_path: str) -> Dict[str, SeparatedTrack]:
        import torch
        
        self.progress_updated.emit(10)
        
        if self._separator is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"加载分离模型 {self._model_name}, 设备: {device}")
            
            from demucs.api import Separator
            self._separator = Separator(
                model=self._model_name,
                device=device,
                progress=False
            )
        
        self.progress_updated.emit(20)
        
        logger.debug("加载音频文件...")
        origin, separated = self._separator.separate_audio_file(Path(audio_path))
        
        self.progress_updated.emit(80)
        
        self._separated_tracks = {}
        for name in self.TRACK_NAMES:
            if name in separated:
                track_tensor = separated[name]
                
                if track_tensor.ndim > 1:
                    track_audio = track_tensor.mean(dim=0).numpy()
                else:
                    track_audio = track_tensor.numpy()
                
                self._separated_tracks[name] = SeparatedTrack(
                    name=name,
                    audio_data=track_audio.astype(np.float32),
                    sample_rate=self._separator.samplerate
                )
                logger.debug(f"轨道 {name}: {len(track_audio)} 样本")
        
        self.progress_updated.emit(100)
        logger.info(f"音频分离完成，共 {len(self._separated_tracks)} 个轨道")
        
        return self._separated_tracks
    
    def _separate_old_api(self, audio_path: str) -> Dict[str, SeparatedTrack]:
        import torch
        
        self.progress_updated.emit(10)
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"加载分离模型 {self._model_name}, 设备: {device}")
        
        from demucs import pretrained
        from demucs.apply import apply_model
        from demucs.audio import AudioFile
        
        self.progress_updated.emit(20)
        
        model = pretrained.get_model(self._model_name)
        model.to(device)
        model.eval()
        
        self.progress_updated.emit(30)
        
        audio_file = AudioFile(audio_path)
        audio = audio_file.read(streams=0, samplerate=44100, channels=2)
        audio = audio.to(device)
        
        self.progress_updated.emit(40)
        
        ref = audio.mean(0)
        audio = audio - ref
        
        self.progress_updated.emit(50)
        
        with torch.no_grad():
            sources = apply_model(model, audio[None], progress=False)[0]
        sources = sources + ref[None]
        
        self.progress_updated.emit(80)
        
        self._separated_tracks = {}
        for i, name in enumerate(self.TRACK_NAMES):
            track_audio = sources[i].cpu().numpy()
            if track_audio.ndim > 1:
                track_audio = np.mean(track_audio, axis=0)
            
            self._separated_tracks[name] = SeparatedTrack(
                name=name,
                audio_data=track_audio.astype(np.float32),
                sample_rate=44100
            )
            logger.debug(f"轨道 {name}: {len(track_audio)} 样本")
        
        self.progress_updated.emit(100)
        logger.info(f"音频分离完成，共 {len(self._separated_tracks)} 个轨道")
        
        return self._separated_tracks
    
    def separate_async(self, audio_path: str) -> None:
        try:
            tracks = self.separate(audio_path)
            self.separation_finished.emit({k: {'audio_data': v.audio_data, 'sample_rate': v.sample_rate} for k, v in tracks.items()})
        except Exception as e:
            logger.exception(f"异步分离失败: {str(e)}")
            self.error_occurred.emit(str(e))
    
    def get_track(self, name: str) -> Optional[SeparatedTrack]:
        return self._separated_tracks.get(name)
    
    def get_all_tracks(self) -> Dict[str, SeparatedTrack]:
        return self._separated_tracks.copy()
    
    def save_track(self, name: str, output_path: str) -> bool:
        track = self._separated_tracks.get(name)
        if track is None:
            return False
        
        try:
            import soundfile as sf
            sf.write(output_path, track.audio_data, track.sample_rate)
            logger.info(f"保存轨道 {name} 到 {output_path}")
            return True
        except Exception as e:
            logger.error(f"保存轨道失败: {str(e)}")
            return False
    
    def clear(self) -> None:
        self._separated_tracks.clear()
    
    @staticmethod
    def get_available_models() -> List[str]:
        return [
            "htdemucs",
            "htdemucs_ft",
            "mdx",
            "mdx_extra",
            "mdx_q",
            "mdx_extra_q"
        ]
