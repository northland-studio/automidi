import numpy as np
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal

from .transcriber import Note


class OnnxTranscriber(QObject):
    progress_updated = Signal(int)
    transcription_finished = Signal(list)
    error_occurred = Signal(str)
    
    MODEL_FILENAME = "basic_pitch.onnx"
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._session = None
        self._model_path: Optional[str] = None
        self._onset_threshold = 0.5
        self._frame_threshold = 0.3
        self._min_note_length_ms = 50.0
    
    def load_model(self, model_path: Optional[str] = None) -> bool:
        if model_path is None:
            model_dir = Path(__file__).parent.parent / "models"
            model_path = str(model_dir / self.MODEL_FILENAME)
        
        if not Path(model_path).exists():
            self.error_occurred.emit(f"ONNX 模型文件不存在: {model_path}")
            return False
        
        try:
            import onnxruntime as ort
            
            providers = ['CPUExecutionProvider']
            if 'CUDAExecutionProvider' in ort.get_available_providers():
                providers.insert(0, 'CUDAExecutionProvider')
            
            self._session = ort.InferenceSession(model_path, providers=providers)
            self._model_path = model_path
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"加载 ONNX 模型失败: {str(e)}")
            return False
    
    def set_thresholds(self, onset: float = 0.5, frame: float = 0.3, min_note_length_ms: float = 50.0) -> None:
        self._onset_threshold = onset
        self._frame_threshold = frame
        self._min_note_length_ms = min_note_length_ms
    
    def transcribe(self, audio_data: np.ndarray, sample_rate: int) -> List[Note]:
        if self._session is None:
            raise RuntimeError("ONNX 模型未加载")
        
        self.progress_updated.emit(10)
        
        try:
            from librosa import feature
            import librosa
            
            self.progress_updated.emit(20)
            
            if sample_rate != 22050:
                audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=22050)
                sample_rate = 22050
            
            self.progress_updated.emit(30)
            
            n_fft = 2048
            hop_length = 512
            n_mels = 229
            
            mel = feature.melspectrogram(
                y=audio_data,
                sr=sample_rate,
                n_fft=n_fft,
                hop_length=hop_length,
                n_mels=n_mels,
                fmin=30.0,
                fmax=8000.0
            )
            
            mel_db = librosa.power_to_db(mel, ref=np.max)
            mel_norm = (mel_db - mel_db.min()) / (mel_db.max() - mel_db.min() + 1e-8)
            
            self.progress_updated.emit(50)
            
            input_data = mel_norm.T.astype(np.float32)
            input_data = np.expand_dims(input_data, axis=0)
            input_data = np.expand_dims(input_data, axis=-1)
            
            self.progress_updated.emit(60)
            
            input_name = self._session.get_inputs()[0].name
            outputs = self._session.run(None, {input_name: input_data})
            
            self.progress_updated.emit(70)
            
            note_output = outputs[0] if len(outputs) > 0 else None
            onset_output = outputs[1] if len(outputs) > 1 else None
            
            notes = self._decode_notes(
                note_output[0] if note_output is not None else None,
                onset_output[0] if onset_output is not None else None,
                hop_length / sample_rate
            )
            
            self.progress_updated.emit(100)
            
            return notes
            
        except Exception as e:
            self.error_occurred.emit(f"ONNX 转录失败: {str(e)}")
            raise
    
    def _decode_notes(self, note_frame: Optional[np.ndarray], onset_frame: Optional[np.ndarray], 
                      time_per_frame: float) -> List[Note]:
        notes = []
        
        if note_frame is None:
            return notes
        
        if onset_frame is None:
            onset_frame = note_frame
        
        n_frames = note_frame.shape[0]
        n_pitches = note_frame.shape[1] if note_frame.ndim > 1 else 88
        
        active_notes = {}
        
        for frame_idx in range(n_frames):
            current_time = frame_idx * time_per_frame
            
            for pitch_idx in range(n_pitches):
                pitch = pitch_idx + 21
                
                note_prob = note_frame[frame_idx, pitch_idx] if note_frame.ndim > 1 else note_frame[frame_idx]
                onset_prob = onset_frame[frame_idx, pitch_idx] if onset_frame.ndim > 1 else onset_frame[frame_idx]
                
                if pitch in active_notes:
                    if note_prob < self._frame_threshold:
                        start_time, velocity = active_notes.pop(pitch)
                        duration = current_time - start_time
                        if duration * 1000 >= self._min_note_length_ms:
                            notes.append(Note(
                                pitch=pitch,
                                start_time=start_time,
                                end_time=current_time,
                                velocity=int(velocity * 127)
                            ))
                else:
                    if onset_prob > self._onset_threshold and note_prob > self._frame_threshold:
                        active_notes[pitch] = (current_time, note_prob)
        
        for pitch, (start_time, velocity) in active_notes.items():
            end_time = n_frames * time_per_frame
            duration = end_time - start_time
            if duration * 1000 >= self._min_note_length_ms:
                notes.append(Note(
                    pitch=pitch,
                    start_time=start_time,
                    end_time=end_time,
                    velocity=int(velocity * 127)
                ))
        
        return sorted(notes, key=lambda n: n.start_time)
    
    def transcribe_async(self, audio_data: np.ndarray, sample_rate: int) -> None:
        try:
            notes = self.transcribe(audio_data, sample_rate)
            self.transcription_finished.emit(notes)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    @property
    def is_loaded(self) -> bool:
        return self._session is not None
    
    @property
    def model_path(self) -> Optional[str]:
        return self._model_path
