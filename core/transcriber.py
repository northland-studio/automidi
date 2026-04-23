import numpy as np
from typing import Optional, List, Tuple
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal


@dataclass
class Note:
    pitch: int
    start_time: float
    end_time: float
    velocity: int = 64
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    def __repr__(self) -> str:
        return f"Note(pitch={self.pitch}, start={self.start_time:.3f}, end={self.end_time:.3f}, vel={self.velocity})"


class Transcriber(QObject):
    progress_updated = Signal(int)
    transcription_finished = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._notes: List[Note] = []
        self._model_output = None
        self._onset_threshold = 0.5
        self._frame_threshold = 0.3
        self._min_note_length = 0.05
    
    def set_thresholds(self, onset: float = 0.5, frame: float = 0.3, min_note_length: float = 0.05) -> None:
        self._onset_threshold = onset
        self._frame_threshold = frame
        self._min_note_length = min_note_length
    
    def transcribe(self, audio_data: np.ndarray, sample_rate: int) -> List[Note]:
        self.progress_updated.emit(5)
        
        try:
            from basic_pitch.inference import predict_and_save
            from basic_pitch import ICASSP_2022_MODEL_PATH
            self.progress_updated.emit(10)
            
            model_output, midi_data, note_events = predict_and_save(
                [audio_data],
                sample_rate,
                onset_threshold=self._onset_threshold,
                frame_threshold=self._frame_threshold,
                minimum_note_length=self._min_note_length,
                model_or_model_path=ICASSP_2022_MODEL_PATH
            )
            
            self.progress_updated.emit(70)
            
            notes = []
            for note_event in note_events:
                note = Note(
                    pitch=note_event.pitch,
                    start_time=note_event.start_time_seconds,
                    end_time=note_event.end_time_seconds,
                    velocity=int(note_event.velocity * 127)
                )
                notes.append(note)
            
            self.progress_updated.emit(90)
            
            self._notes = notes
            self._model_output = model_output
            
            self.progress_updated.emit(100)
            
            return notes
            
        except ImportError:
            return self._transcribe_fallback(audio_data, sample_rate)
        except Exception as e:
            self.error_occurred.emit(f"转录失败: {str(e)}")
            raise
    
    def _transcribe_fallback(self, audio_data: np.ndarray, sample_rate: int) -> List[Note]:
        self.progress_updated.emit(10)
        
        try:
            import librosa
            
            self.progress_updated.emit(20)
            
            chroma = librosa.feature.chroma_cqt(y=audio_data, sr=sample_rate)
            onset_env = librosa.onset.onset_strength(y=audio_data, sr=sample_rate)
            onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sample_rate)
            
            self.progress_updated.emit(50)
            
            notes = []
            hop_length = 512
            time_per_frame = hop_length / sample_rate
            
            for frame in onset_frames:
                time = frame * time_per_frame
                pitch_class = np.argmax(chroma[:, frame])
                midi_pitch = pitch_class + 60
                
                note = Note(
                    pitch=midi_pitch,
                    start_time=time,
                    end_time=time + 0.2,
                    velocity=64
                )
                notes.append(note)
            
            self.progress_updated.emit(100)
            
            self._notes = notes
            return notes
            
        except Exception as e:
            self.error_occurred.emit(f"备用转录失败: {str(e)}")
            raise
    
    def transcribe_async(self, audio_data: np.ndarray, sample_rate: int) -> None:
        try:
            notes = self.transcribe(audio_data, sample_rate)
            self.transcription_finished.emit(notes)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    @property
    def notes(self) -> List[Note]:
        return self._notes.copy()
    
    def clear(self) -> None:
        self._notes = []
        self._model_output = None
