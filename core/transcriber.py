import numpy as np
import tempfile
import os
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
        self._min_note_length_ms = 50.0
    
    def set_thresholds(self, onset: float = 0.5, frame: float = 0.3, min_note_length: float = 0.05) -> None:
        self._onset_threshold = onset
        self._frame_threshold = frame
        self._min_note_length_ms = min_note_length * 1000
    
    def transcribe_from_file(self, audio_path: str) -> List[Note]:
        self.progress_updated.emit(5)
        
        try:
            from basic_pitch.inference import predict
            from basic_pitch import ICASSP_2022_MODEL_PATH
            self.progress_updated.emit(10)
            
            model_output, midi_data, note_events = predict(
                audio_path,
                onset_threshold=self._onset_threshold,
                frame_threshold=self._frame_threshold,
                minimum_note_length=self._min_note_length_ms,
            )
            
            self.progress_updated.emit(70)
            
            notes = self._parse_note_events(note_events)
            
            self.progress_updated.emit(90)
            
            self._notes = notes
            self._model_output = model_output
            
            self.progress_updated.emit(100)
            
            return notes
            
        except ImportError:
            raise ImportError("basic-pitch 未安装，请运行: pip install basic-pitch")
        except Exception as e:
            self.error_occurred.emit(f"转录失败: {str(e)}")
            raise
    
    def transcribe(self, audio_data: np.ndarray, sample_rate: int) -> List[Note]:
        self.progress_updated.emit(5)
        
        try:
            from basic_pitch.inference import predict
            from basic_pitch import ICASSP_2022_MODEL_PATH
            import soundfile as sf
            self.progress_updated.emit(10)
            
            temp_file = None
            try:
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                    temp_file = f.name
                
                sf.write(temp_file, audio_data, sample_rate)
                
                self.progress_updated.emit(20)
                
                model_output, midi_data, note_events = predict(
                    temp_file,
                    onset_threshold=self._onset_threshold,
                    frame_threshold=self._frame_threshold,
                    minimum_note_length=self._min_note_length_ms,
                )
                
                self.progress_updated.emit(70)
                
                notes = self._parse_note_events(note_events)
                
                self.progress_updated.emit(90)
                
                self._notes = notes
                self._model_output = model_output
                
                return notes
                
            finally:
                if temp_file and os.path.exists(temp_file):
                    os.remove(temp_file)
            
        except ImportError:
            return self._transcribe_fallback(audio_data, sample_rate)
        except Exception as e:
            self.error_occurred.emit(f"转录失败: {str(e)}")
            raise
    
    def _parse_note_events(self, note_events: List) -> List[Note]:
        notes = []
        for event in note_events:
            if isinstance(event, tuple) and len(event) >= 4:
                start_time, end_time, pitch, velocity = event[0], event[1], event[2], event[3]
                note = Note(
                    pitch=int(pitch),
                    start_time=float(start_time),
                    end_time=float(end_time),
                    velocity=int(velocity) if isinstance(velocity, int) else int(velocity * 127)
                )
                notes.append(note)
            else:
                note = Note(
                    pitch=int(event.pitch) if hasattr(event, 'pitch') else event[2],
                    start_time=float(event.start_time_seconds) if hasattr(event, 'start_time_seconds') else event[0],
                    end_time=float(event.end_time_seconds) if hasattr(event, 'end_time_seconds') else event[1],
                    velocity=int(event.velocity * 127) if hasattr(event, 'velocity') else int(event[3])
                )
                notes.append(note)
        return notes
    
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
    
    def transcribe_file_async(self, audio_path: str) -> None:
        try:
            notes = self.transcribe_from_file(audio_path)
            self.transcription_finished.emit(notes)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    @property
    def notes(self) -> List[Note]:
        return self._notes.copy()
    
    def clear(self) -> None:
        self._notes = []
        self._model_output = None
