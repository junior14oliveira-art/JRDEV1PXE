# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — WinPE Studio Pro
# Gera: dist/WinPE_Studio/WinPE_Studio.exe  (pasta com tudo)

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

ROOT = Path(SPECPATH)

# ── Coleta completa de pacotes que o PyInstaller não detecta sozinho ─────────
_req_datas, _req_binaries, _req_hiddenimports = collect_all('requests')
_urllib3_datas, _urllib3_binaries, _urllib3_hiddenimports = collect_all('urllib3')
_certifi_datas, _certifi_binaries, _certifi_hiddenimports = collect_all('certifi')

# ── Dados a embutir no executável ────────────────────────────────────────────
# Formato: (origem, destino_dentro_do_exe)
datas = [
    # Estilos QSS
    (str(ROOT / 'app' / 'ui' / 'styles' / 'dark_theme.qss'),
     'app/ui/styles'),

    # Arquivos de boot (sem o boot.wim — muito grande, fica ao lado)
    (str(ROOT / 'app' / 'resources' / 'boot' / 'ipxe.efi'),       'app/resources/boot'),
    (str(ROOT / 'app' / 'resources' / 'boot' / 'snponly.efi'),     'app/resources/boot'),
    (str(ROOT / 'app' / 'resources' / 'boot' / 'undionly.kpxe'),   'app/resources/boot'),
    (str(ROOT / 'app' / 'resources' / 'boot' / 'wimboot'),         'app/resources/boot'),
    (str(ROOT / 'app' / 'resources' / 'boot' / 'httpdisk.exe'),    'app/resources/boot'),
    (str(ROOT / 'app' / 'resources' / 'boot' / 'httpdisk.sys'),    'app/resources/boot'),
    (str(ROOT / 'app' / 'resources' / 'boot' / 'boot.sdi'),        'app/resources/boot'),

    # Pacotes de drivers corporativos
    (str(ROOT / 'app' / 'resources' / 'drivers'),
     'app/resources/drivers'),

    # Ferramentas embutidas (7-Zip + oscdimg) — sem dependencia externa
    (str(ROOT / 'app' / 'resources' / 'tools'),
     'app/resources/tools'),

    # Imagens e assets da interface
    (str(ROOT / 'app' / 'resources' / 'JRDEV1_Wallpaper_WinPE.jpg'),
     'app/resources'),
    (str(ROOT / 'app' / 'resources' / 'JRDEV1.jpg'),
     'app/resources'),
]

# ── Imports ocultos necessários ───────────────────────────────────────────────
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtNetwork',
    'loguru',
    'pydantic',
    'pydantic.deprecated.class_validators',
    'pydantic.deprecated.config',
    'pydantic.deprecated.tools',
    'yaml',
    'wmi',
    'win32api',
    'win32con',
    'win32security',
    'requests',
    'requests.adapters',
    'requests.auth',
    'requests.models',
    'requests.sessions',
    'urllib3',
    'urllib3.util',
    'urllib3.util.retry',
    'certifi',
    'charset_normalizer',
    'idna',
    'socket',
    'threading',
    'struct',
    'select',
    'json',
    'shutil',
    'subprocess',
    # http.server e dependencias — PyInstaller nao inclui automaticamente
    'http',
    'http.server',
    'http.client',
    'http.cookies',
    'http.cookiejar',
    'urllib',
    'urllib.parse',
    'urllib.request',
    'urllib.error',
    'email',
    'email.mime',
    'email.mime.text',
    'email.mime.multipart',
    'html',
    'html.parser',
]

a = Analysis(
    [str(ROOT / 'app' / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[] + _req_binaries + _urllib3_binaries + _certifi_binaries,
    datas=datas + _req_datas + _urllib3_datas + _certifi_datas,
    hiddenimports=hiddenimports + _req_hiddenimports + _urllib3_hiddenimports + _certifi_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy',
        'tkinter', 'unittest', 'xmlrpc', 'pydoc',
    ],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WinPE_Studio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # Sem janela de console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,         # Solicita elevação UAC automaticamente
    icon=None,              # Adicione um .ico aqui se tiver
    version=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WinPE_Studio',    # Pasta de saída: dist/WinPE_Studio/
)
