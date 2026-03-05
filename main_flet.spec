# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['d:/Projects/Programacion/ResumeCabinet/main_flet.py'],
    pathex=[],
    binaries=[],
    datas=[('images', 'images'), ('model', 'model'), ('utils', 'utils'), ('view_flet', 'view_flet'), ('controller', 'controller'), ('references', 'references'), ('templates', 'templates')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='main_flet',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main_flet',
)
