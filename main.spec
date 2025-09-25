# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
    ('./Resource/gspreadAPI_teemo.json', './Resource'),
    ('./Common/*', './Common'),
    ('./Function/*', './Function'),
    ('./Service/*', './Service'),
    ('./Resource/*', './Resource'),
    ('.env', '.'),
    ],
    hiddenimports=['netifaces'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CAU061',
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
    icon=['Resource\\icon.ico'],
)
