# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['intrinsic_gui.py'],
    pathex=['./modules/'],
    binaries=[],
    datas=[],
    hiddenimports=['wx', 'wx._xml', 'matplotlib.backends.backend_wxagg'],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['FixTk', 'tcl', '_tkinter', 'tkinter', 'Tkinter', 'tk', 'win32com', 'pywin32', 'pubsub', 'smokesignal', 'tornado', 'jedi', 'numba'],
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
    name='intrinsic_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='intrinsic_gui',
)
