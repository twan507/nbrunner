# -*- mode: python ; coding: utf-8 -*-

# =============================================================================
#  File build.spec de build ung dung theo kieu ONE-FOLDER (mot thu muc)
# =============================================================================

import multiprocessing
import sys
from os.path import join

# Su dung hook 'collect_all' de thu thap toan bo du lieu cua cac goi phuc tap
from PyInstaller.utils.hooks import collect_all

sys.path.append(join(SPECPATH, 'src'))
import config

multiprocessing.freeze_support()

block_cipher = None

# --- THU THAP CAC GOI CAN THIET ---

# 1. Thu thap toan bo du lieu va module an cua nbformat
nbformat_datas, nbformat_binaries, nbformat_hiddenimports = collect_all('nbformat')

# *** SỬA LỖI: Them buoc thu thap toan bo goi 'debugpy' ***
# Day la phan con thieu khien kernel khong the khoi dong.
debugpy_datas, debugpy_binaries, debugpy_hiddenimports = collect_all('debugpy')

# 2. Dinh nghia cac module an can thiet khac mot cach chinh xac
required_hiddenimports = [
    'xml.parsers.expat',
    'xml.etree.ElementTree',
    'plistlib',
    'pkg_resources'
]

# 3. Tong hop lai cac thong tin
all_datas = [('logo.ico', '.')] + nbformat_datas + debugpy_datas
all_binaries = nbformat_binaries + debugpy_binaries
all_hiddenimports = required_hiddenimports + nbformat_hiddenimports + debugpy_hiddenimports


a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=all_binaries,
    datas=all_datas,
    hiddenimports=all_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name=config.EXE_FILE_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=config.APP_NAME,
)