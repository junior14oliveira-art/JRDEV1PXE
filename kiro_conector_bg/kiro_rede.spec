# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para KIRO_REDE.exe
# Onefile, sem janela, roda silencioso no WinPE

from pathlib import Path
ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / 'kiro_rede.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=['subprocess', 'time', 'os', 'sys'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'PySide6', 'PyQt5'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='KIRO_REDE',
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # sem janela
    uac_admin=False, # WinPE ja e admin
    onefile=True,
)
