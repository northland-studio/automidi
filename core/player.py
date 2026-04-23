import pygame
import numpy as np
import tempfile
import threading
from typing import Optional, Callable
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QTimer

import pretty_midi


class AudioPlayer(QObject):
    playback_started = Signal()
    playback_stopped = Signal()
    playback_finished = Signal()
    position_changed = Signal(float)
    error_occurred = Signal(str)
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        
        self._initialized = False
        self._is_playing = False
        self._is_paused = False
        self._current_file: Optional[str] = None
        self._duration: float = 0.0
        self._position: float = 0.0
        
        self._position_timer = QTimer(self)
        self._position_timer.timeout.connect(self._update_position)
        
        self._init_pygame()
    
    def _init_pygame(self) -> None:
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._initialized = True
        except Exception as e:
            self.error_occurred.emit(f"初始化音频播放器失败: {str(e)}")
    
    def load_audio(self, file_path: str) -> bool:
        if not self._initialized:
            return False
        
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"音频文件不存在: {file_path}")
            
            self.stop()
            
            pygame.mixer.music.load(file_path)
            self._current_file = file_path
            
            import librosa
            duration = librosa.get_duration(path=file_path)
            self._duration = duration
            self._position = 0.0
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"加载音频失败: {str(e)}")
            return False
    
    def load_midi(self, midi_data: pretty_midi.PrettyMIDI, soundfont_path: Optional[str] = None) -> bool:
        if not self._initialized:
            return False
        
        try:
            self.stop()
            
            audio_data = midi_data.fluidsynth(sf2_path=soundfont_path)
            
            audio_data = np.mean(audio_data, axis=0) if audio_data.ndim > 1 else audio_data
            audio_data = (audio_data * 32767).astype(np.int16)
            
            audio_data = np.column_stack((audio_data, audio_data))
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_path = f.name
            
            import soundfile as sf
            sf.write(temp_path, audio_data, 44100)
            
            pygame.mixer.music.load(temp_path)
            self._current_file = temp_path
            self._duration = midi_data.get_end_time()
            self._position = 0.0
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"加载MIDI失败: {str(e)}")
            return False
    
    def play(self) -> bool:
        if not self._initialized or not self._current_file:
            return False
        
        try:
            if self._is_paused:
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.play()
            
            self._is_playing = True
            self._is_paused = False
            self._position_timer.start(100)
            self.playback_started.emit()
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"播放失败: {str(e)}")
            return False
    
    def pause(self) -> None:
        if self._is_playing and not self._is_paused:
            pygame.mixer.music.pause()
            self._is_paused = True
            self._position_timer.stop()
            self.playback_stopped.emit()
    
    def resume(self) -> None:
        if self._is_paused:
            pygame.mixer.music.unpause()
            self._is_paused = False
            self._position_timer.start(100)
            self.playback_started.emit()
    
    def stop(self) -> None:
        if self._initialized:
            pygame.mixer.music.stop()
        
        self._is_playing = False
        self._is_paused = False
        self._position = 0.0
        self._position_timer.stop()
        self.playback_stopped.emit()
    
    def seek(self, position: float) -> None:
        if self._initialized and self._current_file:
            try:
                pygame.mixer.music.set_pos(position)
                self._position = position
                self.position_changed.emit(position)
            except Exception as e:
                self.error_occurred.emit(f"跳转失败: {str(e)}")
    
    def set_volume(self, volume: float) -> None:
        if self._initialized:
            pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
    
    def get_volume(self) -> float:
        if self._initialized:
            return pygame.mixer.music.get_volume()
        return 0.0
    
    def _update_position(self) -> None:
        if self._is_playing and not self._is_paused:
            if self._current_file:
                try:
                    pos = pygame.mixer.music.get_pos() / 1000.0
                    if pos >= 0:
                        self._position = pos
                        self.position_changed.emit(pos)
                    
                    if not pygame.mixer.music.get_busy():
                        self._on_playback_finished()
                except Exception:
                    pass
    
    def _on_playback_finished(self) -> None:
        self._is_playing = False
        self._is_paused = False
        self._position = 0.0
        self._position_timer.stop()
        self.playback_finished.emit()
    
    @property
    def is_playing(self) -> bool:
        return self._is_playing and not self._is_paused
    
    @property
    def is_paused(self) -> bool:
        return self._is_paused
    
    @property
    def duration(self) -> float:
        return self._duration
    
    @property
    def position(self) -> float:
        return self._position
    
    @property
    def current_file(self) -> Optional[str]:
        return self._current_file
    
    def cleanup(self) -> None:
        self.stop()
        if self._initialized:
            pygame.mixer.quit()
        self._initialized = False
