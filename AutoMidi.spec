# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

project_root = Path(SPECPATH)

ffmpeg_dir = project_root / "tools" / "ffmpeg"
ffmpeg_binaries = []
if ffmpeg_dir.exists():
    for f in ffmpeg_dir.iterdir():
        if f.is_file() and (f.suffix == '.exe' or f.name.startswith('ffmpeg') or f.name.startswith('ffprobe')):
            ffmpeg_binaries.append((str(f), 'tools/ffmpeg'))

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=ffmpeg_binaries,
    datas=[
        ('models', 'models'),
        ('ui/themes', 'ui/themes'),
    ],
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
    icon=None,
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
