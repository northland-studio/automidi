import librosa
import soundfile as sf
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Callable
from PySide6.QtCore import QObject, Signal


class AudioLoader(QObject):
    progress_updated = Signal(int)
    loading_finished = Signal(np.ndarray, int, dict)
    error_occurred = Signal(str)
    
    SUPPORTED_FORMATS = {'.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac'}
    TARGET_SAMPLE_RATE = 22050
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._audio_data: Optional[np.ndarray] = None
        self._sample_rate: int = 0
        self._file_info: dict = {}
    
    @staticmethod
    def is_supported(file_path: str) -> bool:
        return Path(file_path).suffix.lower() in AudioLoader.SUPPORTED_FORMATS
    
    def load_audio(self, file_path: str, target_sr: Optional[int] = None) -> Tuple[np.ndarray, int, dict]:
        if not Path(file_path).exists():
            raise FileNotFoundError(f"音频文件不存在: {file_path}")
        
        if not self.is_supported(file_path):
            raise ValueError(f"不支持的音频格式: {Path(file_path).suffix}")
        
        self.progress_updated.emit(10)
        
        try:
            info = sf.info(file_path)
            self._file_info = {
                'path': file_path,
                'duration': info.duration,
                'original_sr': info.samplerate,
                'channels': info.channels,
                'format': info.format,
                'subtype': info.subtype
            }
            
            self.progress_updated.emit(30)
            
            target_sample_rate = target_sr or self.TARGET_SAMPLE_RATE
            audio_data, sr = librosa.load(
                file_path,
                sr=target_sample_rate,
                mono=True,
                dtype=np.float32
            )
            
            self.progress_updated.emit(80)
            
            self._audio_data = audio_data
            self._sample_rate = sr
            
            self._file_info['loaded_sr'] = sr
            self._file_info['samples'] = len(audio_data)
            
            self.progress_updated.emit(100)
            
            return audio_data, sr, self._file_info
            
        except Exception as e:
            self.error_occurred.emit(f"加载音频失败: {str(e)}")
            raise
    
    def load_audio_async(self, file_path: str, target_sr: Optional[int] = None) -> None:
        try:
            audio_data, sr, info = self.load_audio(file_path, target_sr)
            self.loading_finished.emit(audio_data, sr, info)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    @property
    def audio_data(self) -> Optional[np.ndarray]:
        return self._audio_data
    
    @property
    def sample_rate(self) -> int:
        return self._sample_rate
    
    @property
    def file_info(self) -> dict:
        return self._file_info.copy()
    
    @property
    def duration(self) -> float:
        if self._audio_data is not None and self._sample_rate > 0:
            return len(self._audio_data) / self._sample_rate
        return 0.0
    
    def clear(self) -> None:
        self._audio_data = None
        self._sample_rate = 0
        self._file_info = {}
    
    def get_waveform_summary(self, num_points: int = 1000) -> Optional[np.ndarray]:
        if self._audio_data is None:
            return None
        
        samples = len(self._audio_data)
        if samples <= num_points:
            return self._audio_data
        
        chunk_size = samples // num_points
        summary = np.zeros(num_points, dtype=np.float32)
        
        for i in range(num_points):
            start = i * chunk_size
            end = start + chunk_size if i < num_points - 1 else samples
            chunk = self._audio_data[start:end]
            summary[i] = np.max(np.abs(chunk))
        
        return summary
