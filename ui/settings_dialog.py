from typing import Optional, List, Dict
from pathlib import Path
import sys

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QFileDialog, QLineEdit, QMessageBox, QTabWidget, QWidget,
    QColorDialog, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QColor, QIcon

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


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(500, 400)
        
        icon_path = get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(str(icon_path)))
        
        self._settings = QSettings("NorthlandStudio", "AutoMidi")
        
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        tabs = QTabWidget()
        
        tabs.addTab(self._create_transcribe_tab(), "转录")
        tabs.addTab(self._create_export_tab(), "导出")
        tabs.addTab(self._create_theme_tab(), "主题")
        tabs.addTab(self._create_presets_tab(), "预设")
        
        layout.addWidget(tabs)
        
        btn_layout = QHBoxLayout()
        self._save_btn = QPushButton("保存")
        self._save_btn.clicked.connect(self._save_settings)
        self._reset_btn = QPushButton("重置")
        self._reset_btn.clicked.connect(self._reset_settings)
        self._close_btn = QPushButton("关闭")
        self._close_btn.clicked.connect(self.close)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self._save_btn)
        btn_layout.addWidget(self._reset_btn)
        btn_layout.addWidget(self._close_btn)
        layout.addLayout(btn_layout)
    
    def _create_transcribe_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        threshold_group = QGroupBox("阈值设置")
        threshold_layout = QVBoxLayout(threshold_group)
        
        onset_layout = QHBoxLayout()
        onset_layout.addWidget(QLabel("起音阈值:"))
        self._onset_spin = QDoubleSpinBox()
        self._onset_spin.setRange(0.1, 0.9)
        self._onset_spin.setSingleStep(0.05)
        onset_layout.addWidget(self._onset_spin)
        onset_layout.addStretch()
        threshold_layout.addLayout(onset_layout)
        
        frame_layout = QHBoxLayout()
        frame_layout.addWidget(QLabel("帧阈值:"))
        self._frame_spin = QDoubleSpinBox()
        self._frame_spin.setRange(0.1, 0.9)
        self._frame_spin.setSingleStep(0.05)
        frame_layout.addWidget(self._frame_spin)
        frame_layout.addStretch()
        threshold_layout.addLayout(frame_layout)
        
        min_note_layout = QHBoxLayout()
        min_note_layout.addWidget(QLabel("最小音符时长(ms):"))
        self._min_note_spin = QSpinBox()
        self._min_note_spin.setRange(10, 500)
        min_note_layout.addWidget(self._min_note_spin)
        min_note_layout.addStretch()
        threshold_layout.addLayout(min_note_layout)
        
        layout.addWidget(threshold_group)
        
        source_group = QGroupBox("音源分离")
        source_layout = QVBoxLayout(source_group)
        
        self._enable_separator = QCheckBox("启用音源分离")
        source_layout.addWidget(self._enable_separator)
        
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("分离模型:"))
        self._separator_model = QComboBox()
        self._separator_model.addItems([
            "htdemucs", "htdemucs_ft", "mdx", "mdx_extra"
        ])
        model_layout.addWidget(self._separator_model)
        model_layout.addStretch()
        source_layout.addLayout(model_layout)
        
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("计算设备:"))
        self._separator_device = QComboBox()
        self._separator_device.addItems(["自动", "CPU", "GPU (CUDA)"])
        device_layout.addWidget(self._separator_device)
        
        cuda_available = self._check_cuda_available()
        cuda_status = "✓ CUDA可用" if cuda_available else "✗ CUDA不可用"
        self._cuda_status_label = QLabel(cuda_status)
        self._cuda_status_label.setStyleSheet(
            "color: green;" if cuda_available else "color: red;"
        )
        device_layout.addWidget(self._cuda_status_label)
        device_layout.addStretch()
        source_layout.addLayout(device_layout)
        
        layout.addWidget(source_group)
        layout.addStretch()
        
        return widget
    
    def _create_export_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        path_group = QGroupBox("导出路径")
        path_layout = QVBoxLayout(path_group)
        
        default_layout = QHBoxLayout()
        self._use_source_dir = QCheckBox("使用源文件目录")
        default_layout.addWidget(self._use_source_dir)
        default_layout.addStretch()
        path_layout.addLayout(default_layout)
        
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("自定义路径:"))
        self._export_path = QLineEdit()
        self._export_path.setPlaceholderText("选择默认导出目录...")
        custom_layout.addWidget(self._export_path)
        self._browse_export = QPushButton("浏览")
        self._browse_export.clicked.connect(self._browse_export_path)
        custom_layout.addWidget(self._browse_export)
        path_layout.addLayout(custom_layout)
        
        layout.addWidget(path_group)
        
        naming_group = QGroupBox("文件命名")
        naming_layout = QVBoxLayout(naming_group)
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("命名模板:"))
        self._name_template = QLineEdit()
        self._name_template.setPlaceholderText("{name}_transcribed")
        name_layout.addWidget(self._name_template)
        naming_layout.addLayout(name_layout)
        
        hint_label = QLabel("可用变量: {name} 原文件名, {date} 日期, {time} 时间")
        hint_label.setStyleSheet("color: #888; font-size: 11px;")
        naming_layout.addWidget(hint_label)
        
        layout.addWidget(naming_group)
        
        midi_group = QGroupBox("MIDI设置")
        midi_layout = QVBoxLayout(midi_group)
        
        instrument_layout = QHBoxLayout()
        instrument_layout.addWidget(QLabel("默认乐器:"))
        self._default_instrument = QComboBox()
        instruments = MidiGenerator.get_instrument_list()
        self._default_instrument.addItems(instruments[:30])
        instrument_layout.addWidget(self._default_instrument)
        instrument_layout.addStretch()
        midi_layout.addLayout(instrument_layout)
        
        bpm_layout = QHBoxLayout()
        bpm_layout.addWidget(QLabel("默认BPM:"))
        self._default_bpm = QSpinBox()
        self._default_bpm.setRange(40, 240)
        self._default_bpm.setValue(120)
        bpm_layout.addWidget(self._default_bpm)
        bpm_layout.addStretch()
        midi_layout.addLayout(bpm_layout)
        
        layout.addWidget(midi_group)
        layout.addStretch()
        
        return widget
    
    def _create_theme_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        theme_group = QGroupBox("主题设置")
        theme_layout = QVBoxLayout(theme_group)
        
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("主题:"))
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["深色", "浅色", "跟随系统"])
        select_layout.addWidget(self._theme_combo)
        select_layout.addStretch()
        theme_layout.addLayout(select_layout)
        
        layout.addWidget(theme_group)
        layout.addStretch()
        
        return widget
    
    def _create_presets_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        preset_group = QGroupBox("参数预设")
        preset_layout = QVBoxLayout(preset_group)
        
        self._preset_list = QListWidget()
        preset_layout.addWidget(self._preset_list)
        
        btn_layout = QHBoxLayout()
        self._save_preset_btn = QPushButton("保存当前设置")
        self._save_preset_btn.clicked.connect(self._save_preset)
        self._load_preset_btn = QPushButton("加载选中")
        self._load_preset_btn.clicked.connect(self._load_preset)
        self._delete_preset_btn = QPushButton("删除选中")
        self._delete_preset_btn.clicked.connect(self._delete_preset)
        
        btn_layout.addWidget(self._save_preset_btn)
        btn_layout.addWidget(self._load_preset_btn)
        btn_layout.addWidget(self._delete_preset_btn)
        btn_layout.addStretch()
        preset_layout.addLayout(btn_layout)
        
        layout.addWidget(preset_group)
        
        return widget
    
    def _check_cuda_available(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _browse_export_path(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if dir_path:
            self._export_path.setText(dir_path)
    
    def _load_settings(self):
        self._onset_spin.setValue(self._settings.value("onset_threshold", 0.5, type=float))
        self._frame_spin.setValue(self._settings.value("frame_threshold", 0.3, type=float))
        self._min_note_spin.setValue(self._settings.value("min_note_length", 50, type=int))
        self._enable_separator.setChecked(self._settings.value("enable_separator", False, type=bool))
        self._separator_model.setCurrentText(self._settings.value("separator_model", "htdemucs"))
        self._separator_device.setCurrentIndex(self._settings.value("separator_device", 0, type=int))
        self._use_source_dir.setChecked(self._settings.value("use_source_dir", True, type=bool))
        self._export_path.setText(self._settings.value("export_path", ""))
        self._name_template.setText(self._settings.value("name_template", "{name}"))
        self._default_instrument.setCurrentIndex(self._settings.value("default_instrument", 0, type=int))
        self._default_bpm.setValue(self._settings.value("default_bpm", 120, type=int))
        self._theme_combo.setCurrentIndex(self._settings.value("theme", 0, type=int))
        
        self._load_presets()
    
    def _save_settings(self):
        self._settings.setValue("onset_threshold", self._onset_spin.value())
        self._settings.setValue("frame_threshold", self._frame_spin.value())
        self._settings.setValue("min_note_length", self._min_note_spin.value())
        self._settings.setValue("enable_separator", self._enable_separator.isChecked())
        self._settings.setValue("separator_model", self._separator_model.currentText())
        self._settings.setValue("separator_device", self._separator_device.currentIndex())
        self._settings.setValue("use_source_dir", self._use_source_dir.isChecked())
        self._settings.setValue("export_path", self._export_path.text())
        self._settings.setValue("name_template", self._name_template.text())
        self._settings.setValue("default_instrument", self._default_instrument.currentIndex())
        self._settings.setValue("default_bpm", self._default_bpm.value())
        self._settings.setValue("theme", self._theme_combo.currentIndex())
        
        QMessageBox.information(self, "成功", "设置已保存")
    
    def _reset_settings(self):
        self._settings.clear()
        self._load_settings()
        QMessageBox.information(self, "成功", "设置已重置")
    
    def _load_presets(self):
        self._preset_list.clear()
        import json
        presets_json = self._settings.value("presets", "{}")
        try:
            presets = json.loads(presets_json) if presets_json else {}
        except json.JSONDecodeError:
            presets = {}
        for name in presets.keys():
            self._preset_list.addItem(name)
    
    def _save_preset(self):
        from PySide6.QtWidgets import QInputDialog
        import json
        name, ok = QInputDialog.getText(self, "保存预设", "预设名称:")
        if ok and name:
            presets_json = self._settings.value("presets", "{}")
            try:
                presets = json.loads(presets_json) if presets_json else {}
            except json.JSONDecodeError:
                presets = {}
            presets[name] = {
                "onset": self._onset_spin.value(),
                "frame": self._frame_spin.value(),
                "min_note": self._min_note_spin.value(),
            }
            self._settings.setValue("presets", json.dumps(presets))
            self._load_presets()
    
    def _load_preset(self):
        item = self._preset_list.currentItem()
        if item:
            import json
            presets_json = self._settings.value("presets", "{}")
            try:
                presets = json.loads(presets_json) if presets_json else {}
            except json.JSONDecodeError:
                presets = {}
            preset = presets.get(item.text(), {})
            if preset:
                self._onset_spin.setValue(preset.get("onset", 0.5))
                self._frame_spin.setValue(preset.get("frame", 0.3))
                self._min_note_spin.setValue(preset.get("min_note", 50))
    
    def _delete_preset(self):
        item = self._preset_list.currentItem()
        if item:
            import json
            presets_json = self._settings.value("presets", "{}")
            try:
                presets = json.loads(presets_json) if presets_json else {}
            except json.JSONDecodeError:
                presets = {}
            if item.text() in presets:
                del presets[item.text()]
                self._settings.setValue("presets", json.dumps(presets))
                self._load_presets()
