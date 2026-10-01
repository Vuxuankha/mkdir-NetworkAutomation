# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

ROOT = Path(SPECPATH)

datas = [
    (str(ROOT / 'templates'), 'templates'),
    (str(ROOT / 'tools'), 'tools'),
    (str(ROOT / 'VERSION.txt'), '.'),
]
# Libraries with plugin-style imports benefit from explicit collection.
datas += collect_data_files('pysnmp', include_py_files=False)
hiddenimports = []
hiddenimports += collect_submodules('pysnmp')
hiddenimports += collect_submodules('paramiko')
hiddenimports += collect_submodules('cryptography')

a = Analysis(
    ['main.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='NetworkAutomation',
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
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NetworkAutomation',
)
