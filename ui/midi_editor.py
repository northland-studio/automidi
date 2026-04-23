from typing import Optional, List, Dict
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSpinBox, QDoubleSpinBox, QSlider,
    QFileDialog, QMessageBox, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, Signal, QRect, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QMouseEvent, QKeyEvent

import pretty_midi

from core.transcriber import Note


class PianoRollWidget(QWidget):
    note_selected = Signal(int)
    note_modified = Signal(int, Note)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._notes: List[Note] = []
        self._selected_index: int = -1
        self._duration: float = 10.0
        self._zoom_x: float = 50.0
        self._zoom_y: float = 10.0
        self._scroll_x: int = 0
        self._scroll_y: int = 0
        self._min_pitch: int = 21
        self._max_pitch: int = 108
        self._dragging: bool = False
        self._drag_start: Optional[QRect] = None
        self._drag_type: str = ''
        
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
    
    def set_notes(self, notes: List[Note], duration: float = 10.0) -> None:
        self._notes = notes
        self._duration = duration
        
        if notes:
            pitches = [n.pitch for n in notes]
            self._min_pitch = max(0, min(pitches) - 2)
            self._max_pitch = min(127, max(pitches) + 2)
        
        self.update()
    
    def set_selected(self, index: int) -> None:
        self._selected_index = index
        self.update()
    
    def get_selected_note(self) -> Optional[Note]:
        if 0 <= self._selected_index < len(self._notes):
            return self._notes[self._selected_index]
        return None
    
    def update_note(self, index: int, note: Note) -> None:
        if 0 <= index < len(self._notes):
            self._notes[index] = note
            self.update()
    
    def delete_selected(self) -> None:
        if 0 <= self._selected_index < len(self._notes):
            self._notes.pop(self._selected_index)
            self._selected_index = -1
            self.update()
    
    def _pitch_to_y(self, pitch: int) -> int:
        pitch_range = self._max_pitch - self._min_pitch + 1
        y = int((self._max_pitch - pitch) * self._zoom_y)
        return y - self._scroll_y
    
    def _time_to_x(self, time: float) -> int:
        return int(time * self._zoom_x) - self._scroll_x
    
    def _y_to_pitch(self, y: int) -> int:
        pitch = self._max_pitch - int((y + self._scroll_y) / self._zoom_y)
        return max(self._min_pitch, min(self._max_pitch, pitch))
    
    def _x_to_time(self, x: int) -> float:
        return (x + self._scroll_x) / self._zoom_x
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        painter.fillRect(0, 0, width, height, QColor(30, 30, 50))
        
        pen = QPen(QColor(50, 50, 70))
        pen.setWidth(1)
        painter.setPen(pen)
        
        for pitch in range(self._min_pitch, self._max_pitch + 1):
            y = self._pitch_to_y(pitch)
            if 0 <= y <= height:
                if pitch % 12 in [0, 2, 4, 5, 7, 9, 11]:
                    painter.fillRect(0, y - int(self._zoom_y), width, int(self._zoom_y), QColor(40, 40, 60))
                painter.drawLine(0, y, width, y)
        
        pen = QPen(QColor(70, 70, 90))
        painter.setPen(pen)
        
        for beat in range(int(self._duration) + 1):
            x = self._time_to_x(float(beat))
            if 0 <= x <= width:
                painter.drawLine(x, 0, x, height)
        
        for i, note in enumerate(self._notes):
            x = self._time_to_x(note.start_time)
            y = self._pitch_to_y(note.pitch)
            w = int((note.end_time - note.start_time) * self._zoom_x)
            h = int(self._zoom_y) - 2
            
            if x + w < 0 or x > width:
                continue
            
            velocity = note.velocity / 127.0
            color = QColor(
                int(50 + velocity * 150),
                int(100 + velocity * 100),
                int(200 + velocity * 55)
            )
            
            if i == self._selected_index:
                painter.setBrush(QBrush(QColor(255, 100, 100)))
                pen = QPen(QColor(255, 255, 255))
                pen.setWidth(2)
            else:
                painter.setBrush(QBrush(color))
                pen = QPen(color.darker(120))
                pen.setWidth(1)
            
            painter.setPen(pen)
            painter.drawRoundedRect(x, y - h, max(w, 3), h, 3, 3)
        
        painter.end()
    
    def mousePressEvent(self, event: QMouseEvent):
        pos = event.pos()
        
        for i, note in enumerate(self._notes):
            x = self._time_to_x(note.start_time)
            y = self._pitch_to_y(note.pitch)
            w = int((note.end_time - note.start_time) * self._zoom_x)
            h = int(self._zoom_y) - 2
            
            rect = QRect(x, y - h, w, h)
            if rect.contains(pos):
                self._selected_index = i
                self._dragging = True
                self._drag_start = rect
                self.note_selected.emit(i)
                self.update()
                return
        
        self._selected_index = -1
        self.update()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and self._selected_index >= 0:
            pos = event.pos()
            note = self._notes[self._selected_index]
            
            new_pitch = self._y_to_pitch(pos.y())
            new_start = max(0, self._x_to_time(pos.x() - 10))
            
            duration = note.duration
            new_note = Note(
                pitch=new_pitch,
                start_time=new_start,
                end_time=new_start + duration,
                velocity=note.velocity
            )
            
            self._notes[self._selected_index] = new_note
            self.note_modified.emit(self._selected_index, new_note)
            self.update()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging = False
        self._drag_start = None
    
    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        
        if event.modifiers() & Qt.ControlModifier:
            if delta > 0:
                self._zoom_x *= 1.1
                self._zoom_y *= 1.1
            else:
                self._zoom_x /= 1.1
                self._zoom_y /= 1.1
        else:
            if delta > 0:
                self._scroll_y -= 30
            else:
                self._scroll_y += 30
        
        self.update()
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Delete:
            self.delete_selected()
        elif event.key() == Qt.Key_Escape:
            self._selected_index = -1
            self.update()


class MidiEditor(QWidget):
    notes_changed = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._notes: List[Note] = []
        self._midi_data: Optional[pretty_midi.PrettyMIDI] = None
        self._duration: float = 10.0
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        toolbar = QHBoxLayout()
        
        self._pitch_label = QLabel("音高:")
        self._pitch_spin = QSpinBox()
        self._pitch_spin.setRange(0, 127)
        self._pitch_spin.setValue(60)
        
        self._start_label = QLabel("开始:")
        self._start_spin = QDoubleSpinBox()
        self._start_spin.setRange(0, 1000)
        self._start_spin.setDecimals(3)
        self._start_spin.setSingleStep(0.1)
        
        self._end_label = QLabel("结束:")
        self._end_spin = QDoubleSpinBox()
        self._end_spin.setRange(0, 1000)
        self._end_spin.setDecimals(3)
        self._end_spin.setSingleStep(0.1)
        
        self._velocity_label = QLabel("力度:")
        self._velocity_spin = QSpinBox()
        self._velocity_spin.setRange(1, 127)
        self._velocity_spin.setValue(64)
        
        self._apply_btn = QPushButton("应用")
        self._apply_btn.clicked.connect(self._apply_changes)
        self._delete_btn = QPushButton("删除")
        self._delete_btn.clicked.connect(self._delete_note)
        
        toolbar.addWidget(self._pitch_label)
        toolbar.addWidget(self._pitch_spin)
        toolbar.addWidget(self._start_label)
        toolbar.addWidget(self._start_spin)
        toolbar.addWidget(self._end_label)
        toolbar.addWidget(self._end_spin)
        toolbar.addWidget(self._velocity_label)
        toolbar.addWidget(self._velocity_spin)
        toolbar.addWidget(self._apply_btn)
        toolbar.addWidget(self._delete_btn)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        self._piano_roll = PianoRollWidget()
        self._piano_roll.note_selected.connect(self._on_note_selected)
        self._piano_roll.note_modified.connect(self._on_note_modified)
        
        layout.addWidget(self._piano_roll)
        
        self._setEnabled(False)
    
    def _setEnabled(self, enabled: bool):
        self._pitch_spin.setEnabled(enabled)
        self._start_spin.setEnabled(enabled)
        self._end_spin.setEnabled(enabled)
        self._velocity_spin.setEnabled(enabled)
        self._apply_btn.setEnabled(enabled)
        self._delete_btn.setEnabled(enabled)
    
    def load_midi(self, midi_data: pretty_midi.PrettyMIDI) -> None:
        self._midi_data = midi_data
        self._notes = []
        
        if midi_data.instruments:
            for note in midi_data.instruments[0].notes:
                self._notes.append(Note(
                    pitch=note.pitch,
                    start_time=note.start,
                    end_time=note.end,
                    velocity=note.velocity
                ))
        
        self._duration = midi_data.get_end_time() + 1.0
        self._piano_roll.set_notes(self._notes, self._duration)
        self._setEnabled(True)
    
    def load_notes(self, notes: List[Note], duration: float = 10.0) -> None:
        self._notes = notes.copy()
        self._duration = duration
        self._piano_roll.set_notes(self._notes, self._duration)
        self._setEnabled(True)
    
    def get_notes(self) -> List[Note]:
        return self._notes.copy()
    
    def _on_note_selected(self, index: int):
        if 0 <= index < len(self._notes):
            note = self._notes[index]
            self._pitch_spin.setValue(note.pitch)
            self._start_spin.setValue(note.start_time)
            self._end_spin.setValue(note.end_time)
            self._velocity_spin.setValue(note.velocity)
    
    def _on_note_modified(self, index: int, note: Note):
        if 0 <= index < len(self._notes):
            self._notes[index] = note
            self._pitch_spin.setValue(note.pitch)
            self._start_spin.setValue(note.start_time)
            self._end_spin.setValue(note.end_time)
            self.notes_changed.emit(self._notes)
    
    def _apply_changes(self):
        index = self._piano_roll._selected_index
        if 0 <= index < len(self._notes):
            note = Note(
                pitch=self._pitch_spin.value(),
                start_time=self._start_spin.value(),
                end_time=self._end_spin.value(),
                velocity=self._velocity_spin.value()
            )
            self._notes[index] = note
            self._piano_roll.update_note(index, note)
            self.notes_changed.emit(self._notes)
    
    def _delete_note(self):
        self._piano_roll.delete_selected()
        if self._piano_roll._selected_index < 0:
            self.notes_changed.emit(self._notes)
    
    def clear(self):
        self._notes = []
        self._midi_data = None
        self._piano_roll.set_notes([])
        self._setEnabled(False)
