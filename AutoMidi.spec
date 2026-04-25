# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

project_root = Path(SPECPATH)

def collect_datas():
    datas = []
    
    models_dir = project_root / "models"
    if models_dir.exists():
        datas.append(('models', 'models'))
    
    themes_dir = project_root / "ui" / "themes"
    if themes_dir.exists():
        datas.append(('ui/themes', 'ui/themes'))
    
    return datas

def collect_ffmpeg_binaries():
    binaries = []
    ffmpeg_dir = project_root / "tools" / "ffmpeg"
    if ffmpeg_dir.exists():
        for f in ffmpeg_dir.iterdir():
            if f.is_file() and (f.suffix == '.exe' or f.name.startswith('ffmpeg') or f.name.startswith('ffprobe')):
                binaries.append((str(f), 'tools/ffmpeg'))
    return binaries

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=collect_ffmpeg_binaries(),
    datas=collect_datas(),
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'librosa',
        'soundfile',
        'pretty_midi',
        'pygame',
        'basic_pitch',
        'demucs',
        'demucs.api',
        'demucs.pretrained',
        'demucs.apply',
        'onnxruntime',
        'torch',
        'numpy',
        'resampy',
        'imageio_ffmpeg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

icon_path = project_root / "icon.ico"
icon_arg = str(icon_path) if icon_path.exists() else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AutoMidi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_arg,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AutoMidi',
)
