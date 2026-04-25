import numpy as np
import os
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
        self._check_availability()
    
    def _check_availability(self) -> None:
        try:
            import demucs
            self._is_available = True
            logger.info("demucs 可用")
        except ImportError:
            self._is_available = False
            logger.warning("demucs 未安装")
    
    @property
    def is_available(self) -> bool:
        return self._is_available
    
    def set_model(self, model_name: str) -> None:
        self._model_name = model_name
        self._separator = None
        logger.info(f"设置分离模型: {model_name}")
    
    def _get_separator(self):
        if self._separator is None:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"加载分离模型 {self._model_name}, 设备: {device}")
            
            from demucs.api import Separator
            self._separator = Separator(
                model=self._model_name,
                device=device,
                progress=False
            )
        return self._separator
    
    def separate(self, audio_path: str) -> Dict[str, SeparatedTrack]:
        if not self._is_available:
            raise ImportError("demucs 未安装，请运行: pip install demucs")
        
        logger.info(f"开始分离音频: {audio_path}")
        self.progress_updated.emit(5)
        
        try:
            import torch
            
            self.progress_updated.emit(10)
            
            separator = self._get_separator()
            self.progress_updated.emit(20)
            
            logger.debug("加载音频文件...")
            origin, separated = separator.separate_audio_file(Path(audio_path))
            
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
                        sample_rate=separator.samplerate
                    )
                    logger.debug(f"轨道 {name}: {len(track_audio)} 样本")
            
            self.progress_updated.emit(100)
            logger.info(f"音频分离完成，共 {len(self._separated_tracks)} 个轨道")
            
            return self._separated_tracks
            
        except Exception as e:
            logger.exception(f"音源分离失败: {str(e)}")
            self.error_occurred.emit(f"音源分离失败: {str(e)}")
            raise
    
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
