import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal


@dataclass
class AudioAnalysis:
    bpm: float
    key: str
    time_signature: Tuple[int, int]
    confidence: float


class AudioAnalyzer(QObject):
    analysis_finished = Signal(object)
    error_occurred = Signal(str)
    
    KEYS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    KEY_MODES = ['major', 'minor']
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._analysis: Optional[AudioAnalysis] = None
    
    def analyze(self, audio_data: np.ndarray, sample_rate: int) -> AudioAnalysis:
        try:
            import librosa
            
            tempo, beats = librosa.beat.beat_track(y=audio_data, sr=sample_rate)
            
            if isinstance(tempo, np.ndarray):
                bpm = float(tempo[0]) if len(tempo) > 0 else 120.0
            else:
                bpm = float(tempo)
            
            key, key_confidence = self._detect_key(audio_data, sample_rate)
            
            time_signature = self._estimate_time_signature(beats, sample_rate)
            
            self._analysis = AudioAnalysis(
                bpm=bpm,
                key=key,
                time_signature=time_signature,
                confidence=key_confidence
            )
            
            return self._analysis
            
        except Exception as e:
            self.error_occurred.emit(f"音频分析失败: {str(e)}")
            raise
    
    def _detect_key(self, audio_data: np.ndarray, sample_rate: int) -> Tuple[str, float]:
        try:
            import librosa
            
            chroma = librosa.feature.chroma_cqt(y=audio_data, sr=sample_rate)
            
            chroma_mean = np.mean(chroma, axis=1)
            
            major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
            minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
            
            major_correlations = []
            minor_correlations = []
            
            for shift in range(12):
                shifted_major = np.roll(major_profile, shift)
                shifted_minor = np.roll(minor_profile, shift)
                
                major_corr = np.corrcoef(chroma_mean, shifted_major)[0, 1]
                minor_corr = np.corrcoef(chroma_mean, shifted_minor)[0, 1]
                
                major_correlations.append(major_corr)
                minor_correlations.append(minor_corr)
            
            major_correlations = np.array(major_correlations)
            minor_correlations = np.array(minor_correlations)
            
            major_idx = np.argmax(major_correlations)
            minor_idx = np.argmax(minor_correlations)
            
            if major_correlations[major_idx] > minor_correlations[minor_idx]:
                key = f"{self.KEYS[major_idx]}"
                confidence = major_correlations[major_idx]
            else:
                key = f"{self.KEYS[minor_idx]}m"
                confidence = minor_correlations[minor_idx]
            
            return key, float(confidence)
            
        except Exception:
            return 'C', 0.0
    
    def _estimate_time_signature(self, beats: np.ndarray, sample_rate: int) -> Tuple[int, int]:
        if len(beats) < 4:
            return (4, 4)
        
        try:
            import librosa
            
            beat_intervals = np.diff(beats)
            
            if len(beat_intervals) == 0:
                return (4, 4)
            
            avg_interval = np.mean(beat_intervals)
            
            intervals_per_measure = 4
            
            return (intervals_per_measure, 4)
            
        except Exception:
            return (4, 4)
    
    def analyze_async(self, audio_data: np.ndarray, sample_rate: int) -> None:
        try:
            analysis = self.analyze(audio_data, sample_rate)
            self.analysis_finished.emit(analysis)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    @property
    def analysis(self) -> Optional[AudioAnalysis]:
        return self._analysis
    
    def clear(self) -> None:
        self._analysis = None
    
    @staticmethod
    def get_beat_times(audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        import librosa
        
        _, beats = librosa.beat.beat_track(y=audio_data, sr=sample_rate)
        return librosa.frames_to_time(beats, sr=sample_rate)
