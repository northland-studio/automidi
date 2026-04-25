import numpy as np
import os
import sys
import subprocess
import shutil
from typing import Optional, List, Dict
from pathlib import Path
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal

from .logger import logger
from .ffmpeg_manager import setup_ffmpeg_env, check_ffmpeg_available, get_ffmpeg_dir


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
        self._ffmpeg_configured = False
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
            
            success, message = setup_ffmpeg_env()
            self._ffmpeg_configured = success
            if success:
                logger.info(message)
            else:
                logger.warning(message)
                
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
    
    def separate(self, audio_path: str) -> Dict[str, SeparatedTrack]:
        if not self._is_available:
            raise ImportError("demucs 未安装，请运行: pip install demucs")
        
        if not self._ffmpeg_configured:
            success, message = setup_ffmpeg_env()
            if not success:
                raise RuntimeError(message)
            self._ffmpeg_configured = success
        
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
        
        self.progress_updated.emit(20)
        
        model = pretrained.get_model(self._model_name)
        model.to(device)
        model.eval()
        
        self.progress_updated.emit(30)
        
        audio, sr = self._load_audio_with_librosa(audio_path)
        audio = torch.from_numpy(audio).float()
        if audio.ndim == 1:
            audio = audio.unsqueeze(0)
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
    
    def _load_audio_with_librosa(self, audio_path: str):
        import librosa
        audio, sr = librosa.load(audio_path, sr=44100, mono=False)
        if audio.ndim == 1:
            audio = np.stack([audio, audio])
        return audio, sr
    
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
