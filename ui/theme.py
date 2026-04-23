from typing import Dict
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt


class ThemeManager:
    DARK_THEME = {
        'window_background': '#1a1a2e',
        'window_text': '#eaeaea',
        'base': '#16213e',
        'alternate_base': '#1a1a2e',
        'text': '#eaeaea',
        'button': '#0f3460',
        'button_text': '#eaeaea',
        'highlight': '#e94560',
        'highlighted_text': '#ffffff',
        'disabled_text': '#666666',
        'disabled_button': '#2a2a4a',
    }
    
    LIGHT_THEME = {
        'window_background': '#f5f5f5',
        'window_text': '#333333',
        'base': '#ffffff',
        'alternate_base': '#f0f0f0',
        'text': '#333333',
        'button': '#e0e0e0',
        'button_text': '#333333',
        'highlight': '#0078d4',
        'highlighted_text': '#ffffff',
        'disabled_text': '#999999',
        'disabled_button': '#cccccc',
    }
    
    @staticmethod
    def apply_theme(app: QApplication, theme: str = 'dark') -> None:
        if theme == 'dark':
            colors = ThemeManager.DARK_THEME
        elif theme == 'light':
            colors = ThemeManager.LIGHT_THEME
        else:
            return
        
        palette = QPalette()
        
        palette.setColor(QPalette.Window, QColor(colors['window_background']))
        palette.setColor(QPalette.WindowText, QColor(colors['window_text']))
        palette.setColor(QPalette.Base, QColor(colors['base']))
        palette.setColor(QPalette.AlternateBase, QColor(colors['alternate_base']))
        palette.setColor(QPalette.Text, QColor(colors['text']))
        palette.setColor(QPalette.Button, QColor(colors['button']))
        palette.setColor(QPalette.ButtonText, QColor(colors['button_text']))
        palette.setColor(QPalette.Highlight, QColor(colors['highlight']))
        palette.setColor(QPalette.HighlightedText, QColor(colors['highlighted_text']))
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(colors['disabled_text']))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(colors['disabled_text']))
        
        app.setPalette(palette)
        
        app.setStyleSheet(ThemeManager._get_stylesheet(theme))
    
    @staticmethod
    def _get_stylesheet(theme: str) -> str:
        if theme == 'dark':
            return """
                QMainWindow {
                    background-color: #1a1a2e;
                }
                QWidget {
                    background-color: #1a1a2e;
                    color: #eaeaea;
                }
                QGroupBox {
                    border: 1px solid #3a3a5a;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                    font-weight: bold;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
                QPushButton {
                    background-color: #0f3460;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    color: #eaeaea;
                }
                QPushButton:hover {
                    background-color: #1a4a7a;
                }
                QPushButton:pressed {
                    background-color: #e94560;
                }
                QPushButton:disabled {
                    background-color: #2a2a4a;
                    color: #666666;
                }
                QSlider::groove:horizontal {
                    border: 1px solid #3a3a5a;
                    height: 8px;
                    background: #16213e;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #e94560;
                    border: none;
                    width: 16px;
                    margin: -4px 0;
                    border-radius: 8px;
                }
                QProgressBar {
                    border: 1px solid #3a3a5a;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #16213e;
                }
                QProgressBar::chunk {
                    background-color: #e94560;
                    border-radius: 4px;
                }
                QComboBox {
                    background-color: #16213e;
                    border: 1px solid #3a3a5a;
                    border-radius: 5px;
                    padding: 5px 10px;
                    color: #eaeaea;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox QAbstractItemView {
                    background-color: #16213e;
                    selection-background-color: #e94560;
                }
                QSpinBox, QDoubleSpinBox {
                    background-color: #16213e;
                    border: 1px solid #3a3a5a;
                    border-radius: 5px;
                    padding: 5px;
                    color: #eaeaea;
                }
                QLineEdit {
                    background-color: #16213e;
                    border: 1px solid #3a3a5a;
                    border-radius: 5px;
                    padding: 5px;
                    color: #eaeaea;
                }
                QListWidget {
                    background-color: #16213e;
                    border: 1px solid #3a3a5a;
                    border-radius: 5px;
                }
                QListWidget::item:selected {
                    background-color: #e94560;
                }
                QTabWidget::pane {
                    border: 1px solid #3a3a5a;
                    border-radius: 5px;
                    background-color: #1a1a2e;
                }
                QTabBar::tab {
                    background-color: #16213e;
                    border: 1px solid #3a3a5a;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #0f3460;
                }
                QCheckBox {
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 3px;
                    border: 1px solid #3a3a5a;
                    background-color: #16213e;
                }
                QCheckBox::indicator:checked {
                    background-color: #e94560;
                    border-color: #e94560;
                }
                QStatusBar {
                    background-color: #16213e;
                    color: #eaeaea;
                }
                QMenuBar {
                    background-color: #16213e;
                    color: #eaeaea;
                }
                QMenuBar::item:selected {
                    background-color: #e94560;
                }
                QMenu {
                    background-color: #16213e;
                    color: #eaeaea;
                    border: 1px solid #3a3a5a;
                }
                QMenu::item:selected {
                    background-color: #e94560;
                }
                QScrollBar:vertical {
                    background-color: #16213e;
                    width: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #3a3a5a;
                    border-radius: 6px;
                    min-height: 30px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #4a4a6a;
                }
            """
        else:
            return """
                QMainWindow {
                    background-color: #f5f5f5;
                }
                QWidget {
                    background-color: #f5f5f5;
                    color: #333333;
                }
                QGroupBox {
                    border: 1px solid #cccccc;
                    border-radius: 5px;
                    margin-top: 10px;
                    padding-top: 10px;
                    font-weight: bold;
                }
                QPushButton {
                    background-color: #e0e0e0;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
                QPushButton:pressed {
                    background-color: #0078d4;
                    color: white;
                }
                QSlider::groove:horizontal {
                    border: 1px solid #cccccc;
                    height: 8px;
                    background: #ffffff;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #0078d4;
                    border: none;
                    width: 16px;
                    margin: -4px 0;
                    border-radius: 8px;
                }
                QProgressBar {
                    border: 1px solid #cccccc;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #ffffff;
                }
                QProgressBar::chunk {
                    background-color: #0078d4;
                    border-radius: 4px;
                }
            """
