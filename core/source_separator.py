import numpy as np
import tempfile
import os
from typing import Optional, List, Dict, Callable
from pathlib import Path
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal


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
        self._check_availability()
    
    def _check_availability(self) -> None:
        try:
            import demucs
            self._is_available = True
        except ImportError:
            self._is_available = False
    
    @property
    def is_available(self) -> bool:
        return self._is_available
    
    def set_model(self, model_name: str) -> None:
        self._model_name = model_name
    
    def separate(self, audio_path: str) -> Dict[str, SeparatedTrack]:
        if not self._is_available:
            raise ImportError("demucs 未安装，请运行: pip install demucs")
        
        self.progress_updated.emit(5)
        
        try:
            import torch
            from demucs import pretrained
            from demucs.apply import apply_model
            from demucs.audio import AudioFile
            import librosa
            
            self.progress_updated.emit(10)
            
            model = pretrained.get_model(self._model_name)
            self.progress_updated.emit(20)
            
            audio_file = AudioFile(audio_path)
            audio = audio_file.read(streams=0, samplerate=44100, channels=2)
            
            self.progress_updated.emit(30)
            
            ref = audio.mean(0)
            audio = audio - ref
            
            self.progress_updated.emit(40)
            
            sources = apply_model(model, audio[None], progress=False)[0]
            sources = sources + ref[None]
            
            self.progress_updated.emit(80)
            
            self._separated_tracks = {}
            for i, name in enumerate(self.TRACK_NAMES):
                track_audio = sources[i].numpy()
                if track_audio.ndim > 1:
                    track_audio = np.mean(track_audio, axis=0)
                
                self._separated_tracks[name] = SeparatedTrack(
                    name=name,
                    audio_data=track_audio.astype(np.float32),
                    sample_rate=44100
                )
            
            self.progress_updated.emit(100)
            
            return self._separated_tracks
            
        except Exception as e:
            self.error_occurred.emit(f"音源分离失败: {str(e)}")
            raise
    
    def separate_async(self, audio_path: str) -> None:
        try:
            tracks = self.separate(audio_path)
            self.separation_finished.emit({k: {'audio_data': v.audio_data, 'sample_rate': v.sample_rate} for k, v in tracks.items()})
        except Exception as e:
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
            return True
        except Exception:
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
