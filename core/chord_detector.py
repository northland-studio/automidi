import numpy as np
from typing import Optional, List, Tuple
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal


@dataclass
class Chord:
    name: str
    start_time: float
    end_time: float
    confidence: float
    notes: List[int]


class ChordDetector(QObject):
    detection_finished = Signal(list)
    error_occurred = Signal(str)
    
    CHORD_TEMPLATES = {
        'C': [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
        'Cm': [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0],
        'C#': [0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0],
        'C#m': [0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        'D': [0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0],
        'Dm': [0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0],
        'D#': [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0],
        'D#m': [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0],
        'E': [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1],
        'Em': [0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1],
        'F': [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0],
        'Fm': [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0],
        'F#': [0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        'F#m': [0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
        'G': [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0],
        'Gm': [0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1],
        'G#': [0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1],
        'G#m': [1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
        'A': [0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
        'Am': [0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0],
        'A#': [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        'A#m': [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        'B': [0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        'Bm': [0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0],
        'N': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    }
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._chords: List[Chord] = []
        self._hop_length = 512
        self._window_size = 8192
    
    def detect(self, audio_data: np.ndarray, sample_rate: int) -> List[Chord]:
        try:
            import librosa
            
            chroma = librosa.feature.chroma_cqt(
                y=audio_data,
                sr=sample_rate,
                hop_length=self._hop_length
            )
            
            self._chords = []
            time_per_frame = self._hop_length / sample_rate
            
            for i in range(chroma.shape[1]):
                chroma_frame = chroma[:, i]
                chord_name, confidence = self._match_chord(chroma_frame)
                
                current_time = i * time_per_frame
                
                if self._chords and self._chords[-1].name == chord_name:
                    self._chords[-1].end_time = current_time + time_per_frame
                else:
                    self._chords.append(Chord(
                        name=chord_name,
                        start_time=current_time,
                        end_time=current_time + time_per_frame,
                        confidence=confidence,
                        notes=self._get_chord_notes(chord_name)
                    ))
            
            return self._chords
            
        except Exception as e:
            self.error_occurred.emit(f"和弦检测失败: {str(e)}")
            raise
    
    def _match_chord(self, chroma_frame: np.ndarray) -> Tuple[str, float]:
        max_score = -1
        best_chord = 'N'
        
        for chord_name, template in self.CHORD_TEMPLATES.items():
            if chord_name == 'N':
                continue
            
            template = np.array(template)
            score = np.dot(chroma_frame, template)
            
            if score > max_score:
                max_score = score
                best_chord = chord_name
        
        confidence = max_score / (np.sum(chroma_frame) + 1e-8)
        
        if confidence < 0.3:
            return 'N', 0.0
        
        return best_chord, min(confidence, 1.0)
    
    def _get_chord_notes(self, chord_name: str) -> List[int]:
        if chord_name == 'N':
            return []
        
        root = chord_name[0]
        is_minor = chord_name.endswith('m') and len(chord_name) > 1
        
        root_notes = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
        
        if len(chord_name) > 1 and chord_name[1] == '#':
            root = chord_name[:2]
            is_minor = chord_name.endswith('m') and len(chord_name) > 2
        elif len(chord_name) > 1 and chord_name[1] == 'b':
            root = chord_name[:2]
            is_minor = chord_name.endswith('m') and len(chord_name) > 2
        
        base_note = root_notes.get(root[0], 0)
        if '#' in root:
            base_note += 1
        elif 'b' in root:
            base_note -= 1
        
        base_note = base_note % 12 + 60
        
        if is_minor:
            notes = [base_note, base_note + 3, base_note + 7]
        else:
            notes = [base_note, base_note + 4, base_note + 7]
        
        return notes
    
    def detect_async(self, audio_data: np.ndarray, sample_rate: int) -> None:
        try:
            chords = self.detect(audio_data, sample_rate)
            self.detection_finished.emit(chords)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    @property
    def chords(self) -> List[Chord]:
        return self._chords.copy()
    
    def get_chord_at_time(self, time: float) -> Optional[Chord]:
        for chord in self._chords:
            if chord.start_time <= time < chord.end_time:
                return chord
        return None
    
    def clear(self) -> None:
        self._chords = []
