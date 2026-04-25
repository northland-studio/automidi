import pygame
import numpy as np
import tempfile
import os
from typing import Optional
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QTimer

import pretty_midi

from .logger import logger


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
        self._temp_file: Optional[str] = None
        self._duration: float = 0.0
        self._position: float = 0.0
        
        self._position_timer = QTimer(self)
        self._position_timer.timeout.connect(self._update_position)
        
        self._init_pygame()
    
    def _init_pygame(self) -> None:
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._initialized = True
            logger.info("Pygame mixer 初始化成功")
        except Exception as e:
            logger.exception(f"初始化音频播放器失败: {str(e)}")
            self.error_occurred.emit(f"初始化音频播放器失败: {str(e)}")
    
    def load_audio(self, file_path: str) -> bool:
        if not self._initialized:
            logger.warning("播放器未初始化")
            return False
        
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"音频文件不存在: {file_path}")
            
            logger.info(f"加载音频文件: {file_path}")
            self.stop()
            self._cleanup_temp_file()
            
            pygame.mixer.music.load(file_path)
            self._current_file = file_path
            
            import librosa
            duration = librosa.get_duration(path=file_path)
            self._duration = duration
            self._position = 0.0
            
            logger.debug(f"音频加载成功，时长: {duration:.2f}s")
            return True
            
        except Exception as e:
            logger.exception(f"加载音频失败: {str(e)}")
            self.error_occurred.emit(f"加载音频失败: {str(e)}")
            return False
    
    def load_midi(self, midi_data: pretty_midi.PrettyMIDI, soundfont_path: Optional[str] = None) -> bool:
        if not self._initialized:
            logger.warning("播放器未初始化")
            return False
        
        try:
            logger.info("开始加载MIDI数据")
            self.stop()
            self._cleanup_temp_file()
            
            try:
                logger.debug("尝试使用 fluidsynth 合成")
                audio_data = midi_data.fluidsynth(sf2_path=soundfont_path)
                audio_data = np.mean(audio_data, axis=0) if audio_data.ndim > 1 else audio_data
                logger.debug("fluidsynth 合成成功")
            except Exception as e:
                logger.warning(f"fluidsynth 合成失败: {str(e)}，使用 synthesize")
                audio_data = midi_data.synthesize()
            
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            audio_data = np.clip(audio_data, -1.0, 1.0)
            audio_data_int = (audio_data * 32767).astype(np.int16)
            audio_stereo = np.column_stack((audio_data_int, audio_data_int))
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                self._temp_file = f.name
            
            logger.debug(f"创建临时WAV文件: {self._temp_file}")
            
            import soundfile as sf
            sf.write(self._temp_file, audio_stereo, 44100)
            
            pygame.mixer.music.load(self._temp_file)
            self._current_file = self._temp_file
            self._duration = midi_data.get_end_time()
            self._position = 0.0
            
            logger.info(f"MIDI加载成功，时长: {self._duration:.2f}s")
            return True
            
        except Exception as e:
            logger.exception(f"加载MIDI失败: {str(e)}")
            self.error_occurred.emit(f"加载MIDI失败: {str(e)}")
            return False
    
    def _cleanup_temp_file(self):
        if self._temp_file and os.path.exists(self._temp_file):
            try:
                os.remove(self._temp_file)
                logger.debug(f"清理临时文件: {self._temp_file}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {str(e)}")
            self._temp_file = None
    
    def play(self) -> bool:
        if not self._initialized or not self._current_file:
            logger.warning("无法播放: 播放器未初始化或没有加载文件")
            return False
        
        try:
            if self._is_paused:
                pygame.mixer.music.unpause()
                logger.debug("继续播放")
            else:
                pygame.mixer.music.play()
                logger.info("开始播放")
            
            self._is_playing = True
            self._is_paused = False
            self._position_timer.start(100)
            self.playback_started.emit()
            
            return True
            
        except Exception as e:
            logger.exception(f"播放失败: {str(e)}")
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
        self._cleanup_temp_file()
        if self._initialized:
            pygame.mixer.quit()
        self._initialized = False
