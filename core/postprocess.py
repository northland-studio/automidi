import numpy as np
from typing import List, Optional
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal

from .transcriber import Note


class NotePostProcessor(QObject):
    progress_updated = Signal(int)
    processing_finished = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._min_duration = 0.05
        self._max_duration = 10.0
        self._merge_gap = 0.05
        self._min_velocity = 20
        self._max_velocity = 127
    
    def set_parameters(
        self,
        min_duration: float = 0.05,
        max_duration: float = 10.0,
        merge_gap: float = 0.05,
        min_velocity: int = 20
    ) -> None:
        self._min_duration = min_duration
        self._max_duration = max_duration
        self._merge_gap = merge_gap
        self._min_velocity = min_velocity
    
    def process(self, notes: List[Note]) -> List[Note]:
        if not notes:
            return []
        
        self.progress_updated.emit(10)
        
        filtered_notes = self._filter_by_duration(notes)
        self.progress_updated.emit(30)
        
        merged_notes = self._merge_adjacent_notes(filtered_notes)
        self.progress_updated.emit(50)
        
        velocity_adjusted = self._adjust_velocity(merged_notes)
        self.progress_updated.emit(70)
        
        sorted_notes = self._sort_and_validate(velocity_adjusted)
        self.progress_updated.emit(100)
        
        return sorted_notes
    
    def _filter_by_duration(self, notes: List[Note]) -> List[Note]:
        filtered = []
        for note in notes:
            duration = note.duration
            if self._min_duration <= duration <= self._max_duration:
                filtered.append(note)
        return filtered
    
    def _merge_adjacent_notes(self, notes: List[Note]) -> List[Note]:
        if not notes:
            return []
        
        sorted_notes = sorted(notes, key=lambda n: (n.pitch, n.start_time))
        merged = []
        current_note = None
        
        for note in sorted_notes:
            if current_note is None:
                current_note = Note(
                    pitch=note.pitch,
                    start_time=note.start_time,
                    end_time=note.end_time,
                    velocity=note.velocity
                )
            elif (note.pitch == current_note.pitch and
                  note.start_time - current_note.end_time <= self._merge_gap):
                current_note = Note(
                    pitch=current_note.pitch,
                    start_time=current_note.start_time,
                    end_time=max(current_note.end_time, note.end_time),
                    velocity=max(current_note.velocity, note.velocity)
                )
            else:
                merged.append(current_note)
                current_note = Note(
                    pitch=note.pitch,
                    start_time=note.start_time,
                    end_time=note.end_time,
                    velocity=note.velocity
                )
        
        if current_note is not None:
            merged.append(current_note)
        
        return merged
    
    def _adjust_velocity(self, notes: List[Note]) -> List[Note]:
        adjusted = []
        for note in notes:
            velocity = max(self._min_velocity, min(self._max_velocity, note.velocity))
            adjusted.append(Note(
                pitch=note.pitch,
                start_time=note.start_time,
                end_time=note.end_time,
                velocity=velocity
            ))
        return adjusted
    
    def _sort_and_validate(self, notes: List[Note]) -> List[Note]:
        valid_notes = []
        for note in notes:
            if note.start_time < note.end_time and 0 <= note.pitch <= 127:
                valid_notes.append(note)
        return sorted(valid_notes, key=lambda n: n.start_time)
    
    def process_async(self, notes: List[Note]) -> None:
        try:
            processed = self.process(notes)
            self.processing_finished.emit(processed)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def quantize(
        self,
        notes: List[Note],
        bpm: float = 120.0,
        quantize_value: int = 16
    ) -> List[Note]:
        beat_duration = 60.0 / bpm
        quantize_step = beat_duration / quantize_value
        
        quantized = []
        for note in notes:
            quantized_start = round(note.start_time / quantize_step) * quantize_step
            quantized_end = round(note.end_time / quantize_step) * quantize_step
            
            if quantized_end > quantized_start:
                quantized.append(Note(
                    pitch=note.pitch,
                    start_time=quantized_start,
                    end_time=quantized_end,
                    velocity=note.velocity
                ))
        
        return quantized
    
    def transpose(self, notes: List[Note], semitones: int) -> List[Note]:
        transposed = []
        for note in notes:
            new_pitch = note.pitch + semitones
            if 0 <= new_pitch <= 127:
                transposed.append(Note(
                    pitch=new_pitch,
                    start_time=note.start_time,
                    end_time=note.end_time,
                    velocity=note.velocity
                ))
        return transposed
