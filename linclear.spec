# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Linclear.

NOTE: upx and strip are disabled on purpose (UPX corrupts Qt libraries).
"""

hiddenimports = [
    'app',
    'app.version',
    'app.models',
    'app.backends',
    'app.cleanup',
    'app.safety',
    'app.privileged',
    'app.workers',
    'app.ui',
    'app.ui.theme',
    'app.ui.main_window',
    'app.ui.appimage_dialog',
    'app.ui.leftovers_dialog',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('linclear.desktop', '.'),
        ('linclear.svg', '.'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='linclear',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='linclear',
)