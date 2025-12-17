# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'gamdl',
        'gamdl.api',
        'gamdl.downloader', 
        'gamdl.interface',
        'gamdl.cli',
        'gamdl.cli.cli',
        'gamdl.cli.constants',
        'gamdl.cli.utils',
        'gamdl.downloader.constants',
        'gamdl.downloader.downloader_base',
        'gamdl.downloader.downloader_music_video',
        'gamdl.downloader.downloader_song',
        'gamdl.downloader.downloader_uploaded_video',
        'gamdl.downloader.enums',
        'gamdl.downloader.hardcoded_wvd',
        'gamdl.interface.types',
        'gamdl.utils',
        'async_lru',
        'httpx',
        'm3u8',
        'mutagen',
        'PIL',
        'pywidevine',
        'yt_dlp',
        'tkinter',
        'asyncio',
        'threading',
        'pathlib',
        'sys',
        'os',
        'logging',
        'json',
        'subprocess',
        'uuid',
        're',
        'shutil',
        'io',
        'typing',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Gamdl-GUI-ZH',
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Gamdl-GUI-ZH',
)