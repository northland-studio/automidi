import pretty_midi
from typing import List, Optional
from pathlib import Path
from PySide6.QtCore import QObject, Signal

from .transcriber import Note


class MidiGenerator(QObject):
    progress_updated = Signal(int)
    generation_finished = Signal(object)
    error_occurred = Signal(str)
    
    DEFAULT_BPM = 120
    DEFAULT_PROGRAM = 0
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._midi_data: Optional[pretty_midi.PrettyMIDI] = None
        self._bpm = self.DEFAULT_BPM
        self._program = self.DEFAULT_PROGRAM
        self._instrument_name = "Piano"
    
    def set_parameters(self, bpm: int = 120, program: int = 0, instrument_name: str = "Piano") -> None:
        self._bpm = bpm
        self._program = program
        self._instrument_name = instrument_name
    
    def generate(self, notes: List[Note], duration: Optional[float] = None) -> pretty_midi.PrettyMIDI:
        self.progress_updated.emit(10)
        
        midi_data = pretty_midi.PrettyMIDI()
        
        self.progress_updated.emit(20)
        
        instrument = pretty_midi.Instrument(program=self._program, name=self._instrument_name)
        
        self.progress_updated.emit(30)
        
        for i, note in enumerate(notes):
            midi_note = pretty_midi.Note(
                velocity=note.velocity,
                pitch=note.pitch,
                start=note.start_time,
                end=note.end_time
            )
            instrument.notes.append(midi_note)
            
            if i % 100 == 0:
                progress = 30 + int((i / len(notes)) * 60)
                self.progress_updated.emit(progress)
        
        self.progress_updated.emit(90)
        
        midi_data.instruments.append(instrument)
        
        self._midi_data = midi_data
        
        self.progress_updated.emit(100)
        
        return midi_data
    
    def generate_async(self, notes: List[Note], duration: Optional[float] = None) -> None:
        try:
            midi_data = self.generate(notes, duration)
            self.generation_finished.emit(midi_data)
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def save(self, file_path: str, midi_data: Optional[pretty_midi.PrettyMIDI] = None) -> None:
        data = midi_data or self._midi_data
        if data is None:
            raise ValueError("没有可保存的 MIDI 数据")
        
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data.write(str(path))
    
    def get_midi_info(self, midi_data: Optional[pretty_midi.PrettyMIDI] = None) -> dict:
        data = midi_data or self._midi_data
        if data is None:
            return {}
        
        info = {
            'num_instruments': len(data.instruments),
            'total_notes': sum(len(inst.notes) for inst in data.instruments),
            'duration': data.get_end_time(),
            'tempo_changes': len(data.get_tempo_changes()[0]) if data.get_tempo_changes()[0].size > 0 else 0
        }
        
        if data.instruments:
            pitches = [note.pitch for inst in data.instruments for note in inst.notes]
            if pitches:
                info['pitch_range'] = (min(pitches), max(pitches))
        
        return info
    
    @property
    def midi_data(self) -> Optional[pretty_midi.PrettyMIDI]:
        return self._midi_data
    
    def clear(self) -> None:
        self._midi_data = None
    
    def add_tempo_change(self, midi_data: pretty_midi.PrettyMIDI, time: float, bpm: float) -> None:
        tempo_change = pretty_midi.ContinuousControlChange(
            number=pretty_midi.CONTROL_CHANGE_TEMPO,
            value=int(60000000 / bpm),
            time=time
        )
        if midi_data.instruments:
            midi_data.instruments[0].control_changes.append(tempo_change)
    
    @staticmethod
    def get_instrument_list() -> List[str]:
        return pretty_midi.constants.INSTRUMENT_MAP
