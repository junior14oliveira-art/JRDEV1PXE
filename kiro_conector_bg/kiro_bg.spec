# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para KIRO Conector Background
# Gera: kiro_bg.exe — sem janela, roda silencioso

from pathlib import Path
ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / 'kiro_bg.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=['subprocess', 'time', 'os', 'sys'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'numpy', 'pandas',
        'PySide6', 'PyQt5', 'wx',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='KIRODHCP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=False,
    onefile=True,
)
