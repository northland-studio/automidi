from typing import Optional, List
from pathlib import Path
import sys

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QProgressBar, QLabel, QFileDialog, QGroupBox,
    QMessageBox, QCheckBox, QSpinBox, QDoubleSpinBox, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon

from core.transcriber import Transcriber, Note
from core.postprocess import NotePostProcessor
from core.midi_generator import MidiGenerator


def get_icon_path() -> Optional[Path]:
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent
    icon_path = base_path / "icon.ico"
    if icon_path.exists():
        return icon_path
    return None


class BatchWorker(QThread):
    progress = Signal(int, str)
    file_finished = Signal(str, bool)
    all_finished = Signal(int, int)

    def __init__(self, files: List[str], output_dir: str, transcriber: Transcriber,
                 postprocessor: NotePostProcessor, midi_generator: MidiGenerator,
                 onset_threshold: float, frame_threshold: float, min_note_length: float):
        super().__init__()
        self._files = files
        self._output_dir = output_dir
        self._transcriber = transcriber
        self._postprocessor = postprocessor
        self._midi_generator = midi_generator
        self._onset_threshold = onset_threshold
        self._frame_threshold = frame_threshold
        self._min_note_length = min_note_length
        self._is_cancelled = False

    def run(self):
        success_count = 0
        fail_count = 0
        
        for i, file_path in enumerate(self._files):
            if self._is_cancelled:
                break
            
            self.progress.emit(int((i / len(self._files)) * 100), f"处理: {Path(file_path).name}")
            
            try:
                self._transcriber.set_thresholds(
                    self._onset_threshold, self._frame_threshold, self._min_note_length
                )
                notes = self._transcriber.transcribe_from_file(file_path)
                
                processed_notes = self._postprocessor.process(notes)
                
                midi_data = self._midi_generator.generate(processed_notes)
                
                output_name = Path(file_path).stem + ".mid"
                output_path = str(Path(self._output_dir) / output_name)
                self._midi_generator.save(output_path, midi_data)
                
                success_count += 1
                self.file_finished.emit(file_path, True)
                
            except Exception as e:
                fail_count += 1
                self.file_finished.emit(file_path, False)
        
        self.all_finished.emit(success_count, fail_count)

    def cancel(self):
        self._is_cancelled = True


class BatchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量处理")
        self.setMinimumSize(600, 500)
        
        icon_path = get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(str(icon_path)))
        
        self._transcriber = Transcriber()
        self._postprocessor = NotePostProcessor()
        self._midi_generator = MidiGenerator()
        self._worker: Optional[BatchWorker] = None
        self._files: List[str] = []
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        files_group = QGroupBox("文件列表")
        files_layout = QVBoxLayout(files_group)
        
        self._file_list = QListWidget()
        files_layout.addWidget(self._file_list)
        
        btn_layout = QHBoxLayout()
        self._add_btn = QPushButton("添加文件")
        self._add_btn.clicked.connect(self._add_files)
        self._remove_btn = QPushButton("移除选中")
        self._remove_btn.clicked.connect(self._remove_selected)
        self._clear_btn = QPushButton("清空列表")
        self._clear_btn.clicked.connect(self._clear_list)
        
        btn_layout.addWidget(self._add_btn)
        btn_layout.addWidget(self._remove_btn)
        btn_layout.addWidget(self._clear_btn)
        btn_layout.addStretch()
        files_layout.addLayout(btn_layout)
        
        layout.addWidget(files_group)
        
        options_group = QGroupBox("转录选项")
        options_layout = QHBoxLayout(options_group)
        
        options_layout.addWidget(QLabel("起音阈值:"))
        self._onset_spin = QDoubleSpinBox()
        self._onset_spin.setRange(0.1, 0.9)
        self._onset_spin.setValue(0.5)
        self._onset_spin.setSingleStep(0.05)
        options_layout.addWidget(self._onset_spin)
        
        options_layout.addWidget(QLabel("帧阈值:"))
        self._frame_spin = QDoubleSpinBox()
        self._frame_spin.setRange(0.1, 0.9)
        self._frame_spin.setValue(0.3)
        self._frame_spin.setSingleStep(0.05)
        options_layout.addWidget(self._frame_spin)
        
        options_layout.addWidget(QLabel("最小音符(ms):"))
        self._min_note_spin = QSpinBox()
        self._min_note_spin.setRange(10, 500)
        self._min_note_spin.setValue(50)
        options_layout.addWidget(self._min_note_spin)
        
        options_layout.addStretch()
        layout.addWidget(options_group)
        
        output_group = QGroupBox("输出设置")
        output_layout = QHBoxLayout(output_group)
        
        output_layout.addWidget(QLabel("输出目录:"))
        self._output_label = QLabel("未选择")
        self._output_label.setStyleSheet("color: #888;")
        output_layout.addWidget(self._output_label, 1)
        self._browse_btn = QPushButton("浏览")
        self._browse_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(self._browse_btn)
        
        layout.addWidget(output_group)
        
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)
        
        self._status_label = QLabel("就绪")
        layout.addWidget(self._status_label)
        
        control_layout = QHBoxLayout()
        self._start_btn = QPushButton("开始处理")
        self._start_btn.clicked.connect(self._start_processing)
        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.clicked.connect(self._cancel_processing)
        self._cancel_btn.setEnabled(False)
        self._close_btn = QPushButton("关闭")
        self._close_btn.clicked.connect(self.close)
        
        control_layout.addStretch()
        control_layout.addWidget(self._start_btn)
        control_layout.addWidget(self._cancel_btn)
        control_layout.addWidget(self._close_btn)
        layout.addLayout(control_layout)
    
    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择音频文件",
            "",
            "音频文件 (*.wav *.mp3 *.flac *.ogg *.m4a);;所有文件 (*.*)"
        )
        for f in files:
            if f not in self._files:
                self._files.append(f)
                self._file_list.addItem(Path(f).name)
    
    def _remove_selected(self):
        for item in self._file_list.selectedItems():
            row = self._file_list.row(item)
            self._file_list.takeItem(row)
            self._files.pop(row)
    
    def _clear_list(self):
        self._file_list.clear()
        self._files.clear()
    
    def _browse_output(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self._output_dir = dir_path
            self._output_label.setText(dir_path)
            self._output_label.setStyleSheet("color: #fff;")
    
    def _start_processing(self):
        if not self._files:
            QMessageBox.warning(self, "警告", "请先添加要处理的文件")
            return
        
        if not hasattr(self, '_output_dir'):
            QMessageBox.warning(self, "警告", "请选择输出目录")
            return
        
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self._start_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._add_btn.setEnabled(False)
        self._remove_btn.setEnabled(False)
        self._clear_btn.setEnabled(False)
        
        self._worker = BatchWorker(
            self._files,
            self._output_dir,
            self._transcriber,
            self._postprocessor,
            self._midi_generator,
            self._onset_spin.value(),
            self._frame_spin.value(),
            self._min_note_spin.value() / 1000
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.file_finished.connect(self._on_file_finished)
        self._worker.all_finished.connect(self._on_all_finished)
        self._worker.start()
    
    def _cancel_processing(self):
        if self._worker:
            self._worker.cancel()
    
    def _on_progress(self, value: int, message: str):
        self._progress_bar.setValue(value)
        self._status_label.setText(message)
    
    def _on_file_finished(self, file_path: str, success: bool):
        pass
    
    def _on_all_finished(self, success_count: int, fail_count: int):
        self._progress_bar.setVisible(False)
        self._start_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._add_btn.setEnabled(True)
        self._remove_btn.setEnabled(True)
        self._clear_btn.setEnabled(True)
        
        self._status_label.setText(f"完成: 成功 {success_count} 个, 失败 {fail_count} 个")
        
        QMessageBox.information(
            self,
            "批量处理完成",
            f"处理完成!\n成功: {success_count} 个\n失败: {fail_count} 个"
        )
    
    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()
        event.accept()
