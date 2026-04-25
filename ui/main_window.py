import sys
from typing import Optional, List
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QFileDialog,
    QGroupBox, QSlider, QSpinBox, QDoubleSpinBox,
    QCheckBox, QMessageBox, QStatusBar, QFrame,
    QSplitter, QTextEdit, QComboBox, QTabWidget,
    QDockWidget, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal, QSettings, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPainter, QColor, QPen, QKeySequence, QAction, QShortcut, QIcon

import numpy as np
import pretty_midi
import traceback

from core.audio_loader import AudioLoader
from core.transcriber import Transcriber, Note
from core.postprocess import NotePostProcessor
from core.midi_generator import MidiGenerator
from core.player import AudioPlayer
from core.source_separator import SourceSeparator
from core.chord_detector import ChordDetector
from core.analyzer import AudioAnalyzer
from core.logger import logger

from ui.midi_editor import MidiEditor
from ui.batch_dialog import BatchDialog
from ui.settings_dialog import SettingsDialog
from ui.theme import ThemeManager


def get_icon_path() -> Optional[Path]:
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent
    
    icon_path = base_path / "icon.ico"
    if icon_path.exists():
        return icon_path
    return None


class WorkerThread(QThread):
    progress = Signal(int)
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, task, *args, **kwargs):
        super().__init__()
        self._task = task
        self._args = args
        self._kwargs = kwargs
    
    def run(self):
        try:
            result = self._task(*self._args, **self._kwargs)
            self.finished.emit(result)
        except Exception as e:
            logger.exception(f"WorkerThread 错误: {str(e)}")
            self.error.emit(str(e))


class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._waveform: Optional[np.ndarray] = None
        self._duration: float = 0.0
        self._position: float = 0.0
        self.setMinimumHeight(100)
        self.setStyleSheet("background-color: #1a1a2e;")
    
    def set_waveform(self, waveform: Optional[np.ndarray], duration: float):
        self._waveform = waveform
        self._duration = duration
        self.update()
    
    def set_position(self, position: float):
        self._position = position
        self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        painter.fillRect(0, 0, width, height, QColor(26, 26, 46))
        
        if self._waveform is not None and len(self._waveform) > 0:
            pen = QPen(QColor(0, 200, 255))
            pen.setWidth(1)
            painter.setPen(pen)
            
            center_y = height / 2
            step = width / len(self._waveform)
            
            for i, value in enumerate(self._waveform):
                x = i * step
                bar_height = value * (height / 2) * 0.9
                painter.drawLine(int(x), int(center_y - bar_height), int(x), int(center_y + bar_height))
        
        if self._duration > 0 and self._position > 0:
            pen = QPen(QColor(255, 100, 100))
            pen.setWidth(2)
            painter.setPen(pen)
            x = (self._position / self._duration) * width
            painter.drawLine(int(x), 0, int(x), height)
        
        painter.end()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        logger.info("AutoMidi 启动中...")
        
        self._audio_loader = AudioLoader()
        self._transcriber = Transcriber()
        self._postprocessor = NotePostProcessor()
        self._midi_generator = MidiGenerator()
        self._player = AudioPlayer()
        self._source_separator = SourceSeparator()
        self._chord_detector = ChordDetector()
        self._audio_analyzer = AudioAnalyzer()
        
        self._audio_data: Optional[np.ndarray] = None
        self._sample_rate: int = 0
        self._audio_info: dict = {}
        self._notes: List[Note] = []
        self._midi_data: Optional[pretty_midi.PrettyMIDI] = None
        self._current_audio_path: Optional[str] = None
        
        self._worker_thread: Optional[WorkerThread] = None
        
        self._settings = QSettings("NorthlandStudio", "AutoMidi")
        
        self._init_ui()
        self._connect_signals()
        self._load_settings()
        self._setup_shortcuts()
        
        self._apply_theme()
        
        self.setAcceptDrops(True)
        
        logger.info(f"AutoMidi 启动完成，日志文件: {logger.log_path}")
    
    def _init_ui(self):
        self.setWindowTitle("AutoMidi - 音频转MIDI工具")
        self.setMinimumSize(900, 700)
        
        icon_path = get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(str(icon_path)))
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        self._create_menu_bar()
        
        self._create_drop_area(main_layout)
        
        self._create_waveform_area(main_layout)
        
        self._create_info_panel(main_layout)
        
        self._create_options_panel(main_layout)
        
        self._create_control_panel(main_layout)
        
        self._create_progress_bar(main_layout)
        
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("就绪")
    
    def _create_menu_bar(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("文件")
        
        open_action = QAction("打开音频文件", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self._open_file_dialog)
        file_menu.addAction(open_action)
        
        batch_action = QAction("批量处理", self)
        batch_action.triggered.connect(self._show_batch_dialog)
        file_menu.addAction(batch_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("导出MIDI", self)
        export_action.setShortcut(QKeySequence("Ctrl+S"))
        export_action.triggered.connect(self._export_midi)
        export_action.setEnabled(True)
        self._export_action = export_action
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        edit_menu = menubar.addMenu("编辑")
        
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._show_settings_dialog)
        edit_menu.addAction(settings_action)
        
        tools_menu = menubar.addMenu("工具")
        
        analyze_action = QAction("分析音频", self)
        analyze_action.triggered.connect(self._analyze_audio)
        tools_menu.addAction(analyze_action)
        
        chord_action = QAction("检测和弦", self)
        chord_action.triggered.connect(self._detect_chords)
        tools_menu.addAction(chord_action)
        
        view_menu = menubar.addMenu("视图")
        
        theme_group = view_menu.addMenu("主题")
        
        dark_action = QAction("深色主题", self)
        dark_action.triggered.connect(lambda: self._set_theme('dark'))
        theme_group.addAction(dark_action)
        
        light_action = QAction("浅色主题", self)
        light_action.triggered.connect(lambda: self._set_theme('light'))
        theme_group.addAction(light_action)
        
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_drop_area(self, parent_layout):
        drop_group = QGroupBox("音频文件")
        drop_layout = QVBoxLayout(drop_group)
        
        self._drop_label = QLabel("拖拽音频文件到此处\n或点击下方按钮选择文件\n支持格式: WAV, MP3, FLAC, OGG, M4A")
        self._drop_label.setAlignment(Qt.AlignCenter)
        self._drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #555;
                border-radius: 10px;
                padding: 40px;
                background-color: #2a2a4a;
                color: #aaa;
                font-size: 14px;
            }
            QLabel:hover {
                border-color: #0af;
                background-color: #3a3a5a;
            }
        """)
        drop_layout.addWidget(self._drop_label)
        
        btn_layout = QHBoxLayout()
        self._open_btn = QPushButton("选择文件")
        self._open_btn.clicked.connect(self._open_file_dialog)
        btn_layout.addStretch()
        btn_layout.addWidget(self._open_btn)
        btn_layout.addStretch()
        drop_layout.addLayout(btn_layout)
        
        parent_layout.addWidget(drop_group)
    
    def _create_waveform_area(self, parent_layout):
        self._waveform_widget = WaveformWidget()
        parent_layout.addWidget(self._waveform_widget)
    
    def _create_info_panel(self, parent_layout):
        info_group = QGroupBox("音频信息")
        info_layout = QHBoxLayout(info_group)
        
        self._file_name_label = QLabel("文件名: -")
        self._duration_label = QLabel("时长: -")
        self._sample_rate_label = QLabel("采样率: -")
        self._channels_label = QLabel("声道: -")
        
        info_layout.addWidget(self._file_name_label)
        info_layout.addWidget(self._duration_label)
        info_layout.addWidget(self._sample_rate_label)
        info_layout.addWidget(self._channels_label)
        info_layout.addStretch()
        
        parent_layout.addWidget(info_group)
    
    def _create_options_panel(self, parent_layout):
        options_group = QGroupBox("转录选项")
        options_layout = QVBoxLayout(options_group)
        
        row1_layout = QHBoxLayout()
        
        onset_label = QLabel("起音阈值:")
        self._onset_slider = QSlider(Qt.Horizontal)
        self._onset_slider.setRange(1, 100)
        self._onset_slider.setValue(50)
        self._onset_slider.setMinimumWidth(100)
        onset_value = QLabel("0.50")
        self._onset_slider.valueChanged.connect(
            lambda v: onset_value.setText(f"{v/100:.2f}")
        )
        
        row1_layout.addWidget(onset_label)
        row1_layout.addWidget(self._onset_slider)
        row1_layout.addWidget(onset_value)
        
        frame_label = QLabel("帧阈值:")
        self._frame_slider = QSlider(Qt.Horizontal)
        self._frame_slider.setRange(1, 100)
        self._frame_slider.setValue(30)
        self._frame_slider.setMinimumWidth(100)
        frame_value = QLabel("0.30")
        self._frame_slider.valueChanged.connect(
            lambda v: frame_value.setText(f"{v/100:.2f}")
        )
        
        row1_layout.addWidget(frame_label)
        row1_layout.addWidget(self._frame_slider)
        row1_layout.addWidget(frame_value)
        
        min_note_label = QLabel("最小音符时长(ms):")
        self._min_note_spin = QSpinBox()
        self._min_note_spin.setRange(10, 500)
        self._min_note_spin.setValue(50)
        
        row1_layout.addWidget(min_note_label)
        row1_layout.addWidget(self._min_note_spin)
        
        instrument_label = QLabel("乐器:")
        self._instrument_combo = QComboBox()
        instruments = MidiGenerator.get_instrument_list()
        self._instrument_combo.addItems(instruments[:20])
        self._instrument_combo.setCurrentIndex(0)
        
        row1_layout.addWidget(instrument_label)
        row1_layout.addWidget(self._instrument_combo)
        row1_layout.addStretch()
        
        options_layout.addLayout(row1_layout)
        
        row2_layout = QHBoxLayout()
        
        self._enable_separator = QCheckBox("启用音源分离")
        self._enable_separator.toggled.connect(self._on_separator_toggled)
        row2_layout.addWidget(self._enable_separator)
        
        self._separator_model_label = QLabel("模型:")
        self._separator_model_combo = QComboBox()
        self._separator_model_combo.addItems(SourceSeparator.get_available_models())
        self._separator_model_combo.setEnabled(False)
        row2_layout.addWidget(self._separator_model_label)
        row2_layout.addWidget(self._separator_model_combo)
        
        self._tracks_label = QLabel("转录轨道:")
        row2_layout.addWidget(self._tracks_label)
        
        self._track_vocals = QCheckBox("人声")
        self._track_vocals.setChecked(False)
        self._track_vocals.setEnabled(False)
        row2_layout.addWidget(self._track_vocals)
        
        self._track_drums = QCheckBox("鼓")
        self._track_drums.setChecked(False)
        self._track_drums.setEnabled(False)
        row2_layout.addWidget(self._track_drums)
        
        self._track_bass = QCheckBox("贝斯")
        self._track_bass.setChecked(False)
        self._track_bass.setEnabled(False)
        row2_layout.addWidget(self._track_bass)
        
        self._track_other = QCheckBox("其他")
        self._track_other.setChecked(True)
        self._track_other.setEnabled(False)
        row2_layout.addWidget(self._track_other)
        
        row2_layout.addStretch()
        
        options_layout.addLayout(row2_layout)
        
        parent_layout.addWidget(options_group)
    
    def _on_separator_toggled(self, enabled: bool):
        self._separator_model_combo.setEnabled(enabled)
        self._track_vocals.setEnabled(enabled)
        self._track_drums.setEnabled(enabled)
        self._track_bass.setEnabled(enabled)
        self._track_other.setEnabled(enabled)
        self._separator_model_label.setEnabled(enabled)
        self._tracks_label.setEnabled(enabled)
    
    def _create_control_panel(self, parent_layout):
        control_group = QGroupBox("控制")
        control_layout = QHBoxLayout(control_group)
        
        self._transcribe_btn = QPushButton("开始转录")
        self._transcribe_btn.clicked.connect(self._start_transcription)
        self._transcribe_btn.setEnabled(False)
        self._transcribe_btn.setStyleSheet("QPushButton { padding: 10px 20px; font-weight: bold; }")
        
        self._play_audio_btn = QPushButton("播放原音频")
        self._play_audio_btn.clicked.connect(self._toggle_play_audio)
        self._play_audio_btn.setEnabled(False)
        
        self._play_midi_btn = QPushButton("播放MIDI")
        self._play_midi_btn.clicked.connect(self._toggle_play_midi)
        self._play_midi_btn.setEnabled(False)
        
        self._stop_btn = QPushButton("停止")
        self._stop_btn.clicked.connect(self._stop_playback)
        self._stop_btn.setEnabled(False)
        
        self._export_btn = QPushButton("导出MIDI")
        self._export_btn.clicked.connect(self._export_midi)
        self._export_btn.setEnabled(False)
        
        control_layout.addWidget(self._transcribe_btn)
        control_layout.addWidget(self._play_audio_btn)
        control_layout.addWidget(self._play_midi_btn)
        control_layout.addWidget(self._stop_btn)
        control_layout.addWidget(self._export_btn)
        control_layout.addStretch()
        
        volume_label = QLabel("音量:")
        self._volume_slider = QSlider(Qt.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(80)
        self._volume_slider.setMaximumWidth(100)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)
        
        control_layout.addWidget(volume_label)
        control_layout.addWidget(self._volume_slider)
        
        parent_layout.addWidget(control_group)
    
    def _create_progress_bar(self, parent_layout):
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        parent_layout.addWidget(self._progress_bar)
    
    def _connect_signals(self):
        self._audio_loader.progress_updated.connect(self._on_load_progress)
        self._audio_loader.loading_finished.connect(self._on_audio_loaded)
        self._audio_loader.error_occurred.connect(self._on_error)
        
        self._transcriber.progress_updated.connect(self._on_transcribe_progress)
        self._transcriber.transcription_finished.connect(self._on_transcription_finished)
        self._transcriber.error_occurred.connect(self._on_error)
        
        self._postprocessor.processing_finished.connect(self._on_postprocess_finished)
        self._postprocessor.error_occurred.connect(self._on_error)
        
        self._midi_generator.progress_updated.connect(self._on_generate_progress)
        self._midi_generator.generation_finished.connect(self._on_midi_generated)
        self._midi_generator.error_occurred.connect(self._on_error)
        
        self._player.playback_started.connect(self._on_playback_started)
        self._player.playback_stopped.connect(self._on_playback_stopped)
        self._player.playback_finished.connect(self._on_playback_finished)
        self._player.position_changed.connect(self._on_position_changed)
        self._player.error_occurred.connect(self._on_error)
    
    def _load_settings(self):
        onset = self._settings.value("onset_threshold", 50, type=int)
        frame = self._settings.value("frame_threshold", 30, type=int)
        min_note = self._settings.value("min_note_length", 50, type=int)
        volume = self._settings.value("volume", 80, type=int)
        
        self._onset_slider.setValue(onset)
        self._frame_slider.setValue(frame)
        self._min_note_spin.setValue(min_note)
        self._volume_slider.setValue(volume)
    
    def _save_settings(self):
        self._settings.setValue("onset_threshold", self._onset_slider.value())
        self._settings.setValue("frame_threshold", self._frame_slider.value())
        self._settings.setValue("min_note_length", self._min_note_spin.value())
        self._settings.setValue("volume", self._volume_slider.value())
    
    def _reset_settings(self):
        self._settings.clear()
        self._load_settings()
        self._status_bar.showMessage("设置已重置")
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and AudioLoader.is_supported(urls[0].toLocalFile()):
                event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self._load_audio_file(file_path)
    
    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择音频文件",
            "",
            "音频文件 (*.wav *.mp3 *.flac *.ogg *.m4a);;所有文件 (*.*)"
        )
        if file_path:
            self._load_audio_file(file_path)
    
    def _load_audio_file(self, file_path: str):
        logger.info(f"加载音频文件: {file_path}")
        self._status_bar.showMessage(f"正在加载: {Path(file_path).name}")
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        
        self._current_audio_path = file_path
        
        try:
            audio_data, sr, info = self._audio_loader.load_audio(file_path)
            self._on_audio_loaded(audio_data, sr, info)
        except Exception as e:
            logger.exception(f"加载音频失败: {file_path}")
            self._on_error(f"加载音频失败: {str(e)}")
    
    def _on_audio_loaded(self, audio_data: np.ndarray, sample_rate: int, info: dict):
        logger.info(f"音频加载完成: {info['path']}, 时长: {info['duration']:.2f}s, 采样率: {info['original_sr']}Hz")
        self._audio_data = audio_data
        self._sample_rate = sample_rate
        self._audio_info = info
        
        self._file_name_label.setText(f"文件名: {Path(info['path']).name}")
        self._duration_label.setText(f"时长: {info['duration']:.2f}s")
        self._sample_rate_label.setText(f"采样率: {info['original_sr']}Hz")
        self._channels_label.setText(f"声道: {info['channels']}")
        
        waveform = self._audio_loader.get_waveform_summary(500)
        self._waveform_widget.set_waveform(waveform, info['duration'])
        
        self._transcribe_btn.setEnabled(True)
        self._play_audio_btn.setEnabled(True)
        
        self._progress_bar.setVisible(False)
        self._status_bar.showMessage("音频加载完成")
        
        self._drop_label.setText(f"已加载: {Path(info['path']).name}\n拖拽新文件替换")
    
    def _start_transcription(self):
        if self._audio_data is None and self._current_audio_path is None:
            return
        
        self._save_settings()
        
        onset_threshold = self._onset_slider.value() / 100
        frame_threshold = self._frame_slider.value() / 100
        min_note_length = self._min_note_spin.value() / 1000
        
        self._transcriber.set_thresholds(onset_threshold, frame_threshold, min_note_length)
        
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self._transcribe_btn.setEnabled(False)
        
        if self._enable_separator.isChecked():
            self._status_bar.showMessage("正在进行音源分离...")
            self._worker_thread = WorkerThread(
                self._transcribe_with_separation,
                self._current_audio_path or self._audio_data,
                self._sample_rate if self._audio_data is not None else None
            )
        else:
            self._status_bar.showMessage("正在转录...")
            if self._current_audio_path:
                self._worker_thread = WorkerThread(
                    self._transcriber.transcribe_from_file,
                    self._current_audio_path
                )
            else:
                self._worker_thread = WorkerThread(
                    self._transcriber.transcribe,
                    self._audio_data,
                    self._sample_rate
                )
        
        self._worker_thread.progress.connect(self._on_transcribe_progress)
        self._worker_thread.finished.connect(self._on_transcription_finished)
        self._worker_thread.error.connect(self._on_error)
        self._worker_thread.start()
    
    def _transcribe_with_separation(self, audio_path_or_data, sample_rate=None):
        logger.info("开始音源分离转录...")
        all_notes = []
        temp_path = None
        
        try:
            model_name = self._separator_model_combo.currentText()
            logger.info(f"使用分离模型: {model_name}")
            self._source_separator.set_model(model_name)
            
            device_index = self._settings.value("separator_device", 0, type=int)
            device_map = {0: "auto", 1: "cpu", 2: "cuda"}
            device = device_map.get(device_index, "auto")
            self._source_separator.set_device(device)
            
            if isinstance(audio_path_or_data, str):
                logger.debug(f"从文件分离: {audio_path_or_data}")
                tracks = self._source_separator.separate(audio_path_or_data)
            else:
                import tempfile
                import soundfile as sf
                import os
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                    temp_path = f.name
                logger.debug(f"创建临时文件: {temp_path}")
                sf.write(temp_path, audio_path_or_data, sample_rate)
                tracks = self._source_separator.separate(temp_path)
            
            track_selection = {
                'vocals': self._track_vocals.isChecked(),
                'drums': self._track_drums.isChecked(),
                'bass': self._track_bass.isChecked(),
                'other': self._track_other.isChecked()
            }
            
            logger.info(f"选择的轨道: {track_selection}")
            
            for track_name, track_data in tracks.items():
                if not track_selection.get(track_name, False):
                    continue
                
                logger.info(f"转录轨道: {track_name}")
                audio = track_data.audio_data
                sr = track_data.sample_rate
                
                notes = self._transcriber.transcribe(audio, sr)
                logger.info(f"轨道 {track_name} 转录完成: {len(notes)} 个音符")
                all_notes.extend(notes)
            
            logger.info(f"音源分离转录完成，共 {len(all_notes)} 个音符")
            return all_notes
            
        except Exception as e:
            logger.exception(f"音源分离转录失败: {str(e)}")
            raise
        finally:
            if temp_path:
                import os
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        logger.debug(f"删除临时文件: {temp_path}")
                except Exception as e:
                    logger.warning(f"删除临时文件失败: {str(e)}")
    
    def _on_transcribe_progress(self, progress: int):
        self._progress_bar.setValue(progress)
    
    def _on_transcription_finished(self, notes: List[Note]):
        self._notes = notes
        self._status_bar.showMessage(f"转录完成，共 {len(notes)} 个音符")
        
        self._progress_bar.setValue(0)
        self._status_bar.showMessage("正在后处理...")
        
        min_duration = self._min_note_spin.value() / 1000
        self._postprocessor.set_parameters(min_duration=min_duration)
        
        processed_notes = self._postprocessor.process(notes)
        self._on_postprocess_finished(processed_notes)
    
    def _on_postprocess_finished(self, notes: List[Note]):
        self._notes = notes
        
        self._progress_bar.setValue(0)
        self._status_bar.showMessage("正在生成MIDI...")
        
        instrument_index = self._instrument_combo.currentIndex()
        self._midi_generator.set_parameters(program=instrument_index)
        
        midi_data = self._midi_generator.generate(notes, self._audio_info.get('duration'))
        self._on_midi_generated(midi_data)
    
    def _on_midi_generated(self, midi_data: pretty_midi.PrettyMIDI):
        self._midi_data = midi_data
        
        info = self._midi_generator.get_midi_info(midi_data)
        
        self._progress_bar.setVisible(False)
        self._transcribe_btn.setEnabled(True)
        self._play_midi_btn.setEnabled(True)
        self._export_btn.setEnabled(True)
        self._export_action.setEnabled(True)
        
        self._status_bar.showMessage(
            f"MIDI生成完成: {info['total_notes']}个音符, "
            f"时长{info['duration']:.2f}秒"
        )
    
    def _toggle_play_audio(self):
        if self._player.is_playing:
            self._player.pause()
            self._play_audio_btn.setText("继续播放")
        else:
            if self._current_audio_path:
                self._player.load_audio(self._current_audio_path)
            self._player.play()
            self._play_audio_btn.setText("暂停")
    
    def _toggle_play_midi(self):
        logger.debug("切换MIDI播放")
        if self._player.is_playing:
            self._player.pause()
            self._play_midi_btn.setText("继续播放MIDI")
        else:
            if self._midi_data:
                logger.info("加载并播放MIDI")
                try:
                    if self._player.load_midi(self._midi_data):
                        self._player.play()
                        self._play_midi_btn.setText("暂停MIDI")
                    else:
                        logger.error("加载MIDI失败")
                        QMessageBox.warning(self, "警告", "无法加载MIDI进行播放")
                except Exception as e:
                    logger.exception(f"播放MIDI失败: {str(e)}")
                    QMessageBox.critical(self, "错误", f"播放MIDI失败: {str(e)}")
            else:
                logger.warning("没有MIDI数据可播放")
    
    def _stop_playback(self):
        self._player.stop()
        self._play_audio_btn.setText("播放原音频")
        self._play_midi_btn.setText("播放MIDI")
    
    def _on_playback_started(self):
        self._stop_btn.setEnabled(True)
    
    def _on_playback_stopped(self):
        pass
    
    def _on_playback_finished(self):
        self._play_audio_btn.setText("播放原音频")
        self._play_midi_btn.setText("播放MIDI")
        self._stop_btn.setEnabled(False)
    
    def _on_position_changed(self, position: float):
        self._waveform_widget.set_position(position)
    
    def _on_volume_changed(self, value: int):
        self._player.set_volume(value / 100)
    
    def _export_midi(self):
        if self._midi_data is None:
            QMessageBox.warning(self, "警告", "没有可导出的MIDI数据")
            return
        
        default_name = "output.mid"
        if self._current_audio_path:
            base_name = Path(self._current_audio_path).stem
            
            if self._enable_separator.isChecked():
                track_suffixes = []
                if self._track_vocals.isChecked():
                    track_suffixes.append("vocals")
                if self._track_drums.isChecked():
                    track_suffixes.append("drums")
                if self._track_bass.isChecked():
                    track_suffixes.append("bass")
                if self._track_other.isChecked():
                    track_suffixes.append("other")
                
                if track_suffixes:
                    default_name = f"{base_name}_{'_'.join(track_suffixes)}.mid"
                else:
                    default_name = f"{base_name}.mid"
            else:
                default_name = f"{base_name}.mid"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存MIDI文件",
            default_name,
            "MIDI文件 (*.mid);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                self._midi_generator.save(file_path, self._midi_data)
                self._status_bar.showMessage(f"MIDI已导出: {file_path}")
                QMessageBox.information(self, "成功", f"MIDI文件已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def _on_load_progress(self, progress: int):
        self._progress_bar.setValue(progress)
    
    def _on_generate_progress(self, progress: int):
        self._progress_bar.setValue(progress)
    
    def _on_error(self, message: str):
        logger.error(f"错误: {message}")
        self._progress_bar.setVisible(False)
        self._transcribe_btn.setEnabled(self._audio_data is not None)
        self._status_bar.showMessage(f"错误: {message}")
        QMessageBox.critical(self, "错误", message)
    
    def _show_about(self):
        QMessageBox.about(
            self,
            "关于 AutoMidi",
            "AutoMidi - 音频转MIDI工具\n\n"
            "版本: 2.0.0\n"
            "开发者: 北域工作室\n\n"
            "一款将音频文件自动转录为MIDI的桌面应用\n"
            "支持多种音频格式，提供可视化波形预览\n\n"
            "新功能: 音源分离、批量处理、MIDI编辑、和弦检测"
        )
    
    def _show_batch_dialog(self):
        dialog = BatchDialog(self)
        dialog.exec()
    
    def _show_settings_dialog(self):
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def _setup_shortcuts(self):
        self._shortcut_play = QShortcut(QKeySequence(Qt.Key_Space), self)
        self._shortcut_play.activated.connect(self._toggle_playback)
        
        self._shortcut_stop = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self._shortcut_stop.activated.connect(self._stop_playback)
    
    def _toggle_playback(self):
        if self._player.is_playing:
            self._stop_playback()
        elif self._midi_data:
            self._toggle_play_midi()
        elif self._current_audio_path:
            self._toggle_play_audio()
    
    def _apply_theme(self):
        theme = self._settings.value("theme", 0, type=int)
        theme_name = ['dark', 'light', 'dark'][theme]
        ThemeManager.apply_theme(QApplication.instance(), theme_name)
    
    def _set_theme(self, theme_name: str):
        theme_index = {'dark': 0, 'light': 1}.get(theme_name, 0)
        self._settings.setValue("theme", theme_index)
        ThemeManager.apply_theme(QApplication.instance(), theme_name)
        self._status_bar.showMessage(f"已切换到{'深色' if theme_name == 'dark' else '浅色'}主题")
    
    def _analyze_audio(self):
        if self._audio_data is None:
            QMessageBox.warning(self, "警告", "请先加载音频文件")
            return
        
        self._status_bar.showMessage("正在分析音频...")
        
        try:
            analysis = self._audio_analyzer.analyze(self._audio_data, self._sample_rate)
            
            QMessageBox.information(
                self,
                "音频分析结果",
                f"BPM: {analysis.bpm:.1f}\n"
                f"调性: {analysis.key}\n"
                f"拍号: {analysis.time_signature[0]}/{analysis.time_signature[1]}\n"
                f"置信度: {analysis.confidence:.2%}"
            )
            
            self._status_bar.showMessage(f"分析完成: BPM={analysis.bpm:.1f}, 调性={analysis.key}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"分析失败: {str(e)}")
    
    def _detect_chords(self):
        if self._audio_data is None:
            QMessageBox.warning(self, "警告", "请先加载音频文件")
            return
        
        self._status_bar.showMessage("正在检测和弦...")
        
        try:
            chords = self._chord_detector.detect(self._audio_data, self._sample_rate)
            
            chord_summary = []
            for chord in chords[:10]:
                chord_summary.append(f"{chord.name}: {chord.start_time:.2f}s - {chord.end_time:.2f}s")
            
            if len(chords) > 10:
                chord_summary.append(f"... 共 {len(chords)} 个和弦")
            
            QMessageBox.information(
                self,
                "和弦检测结果",
                "\n".join(chord_summary)
            )
            
            self._status_bar.showMessage(f"检测完成: 共 {len(chords)} 个和弦")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"检测失败: {str(e)}")
    
    def closeEvent(self, event):
        self._save_settings()
        self._player.cleanup()
        if self._worker_thread and self._worker_thread.isRunning():
            self._worker_thread.terminate()
            self._worker_thread.wait()
        event.accept()
