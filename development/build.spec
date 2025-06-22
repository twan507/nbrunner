# -*- mode: python ; coding: utf-8 -*-

# =============================================================================
#  File build.spec de build ung dung theo kieu ONE-FOLDER (mot thu muc)
# =============================================================================

import multiprocessing
import sys
from os.path import join
import os
import re

# Su dung hook 'collect_all' de thu thap toan bo du lieu cua cac goi phuc tap
from PyInstaller.utils.hooks import collect_all

sys.path.append(join(SPECPATH, 'src'))
import config

multiprocessing.freeze_support()

# <<< BẮT ĐẦU ĐOẠN CODE MỚI: TỰ ĐỘNG THÊM THƯ VIỆN TỪ REQUIREMENTS.TXT >>>
# =============================================================================
print("--- Dang tu dong them thu vien tu requirements.txt ---")
requirements_path = join(SPECPATH, '..', 'development', 'requirements.txt')

# Cac goi nay khong can them vao hidden-imports
ignore_list = {
    'setuptools', 'wheel', 'pywin32', 'PyQt6-sip', 'send2trash', 
    'python-dotenv', 'pyyaml', 'tabulate', 'python-dateutil', 'traitlets',
    'pyinstaller', 'nbformat', 'debugpy' # nbformat va debugpy da duoc xu ly boi collect_all
}

imports_from_reqs = []
try:
    with open(requirements_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        package_name = re.split(r'[=<>~]', line)[0].strip()
        if package_name and package_name not in ignore_list:
            print(f"  -> Phat hien va them: {package_name}")
            imports_from_reqs.append(package_name)
except FileNotFoundError:
    print(f"WARNING: Khong tim thay file '{requirements_path}'. Bo qua buoc them tu dong.")
print("--- Hoan thanh them thu vien tu dong ---\n")
# =============================================================================
# <<< KẾT THÚC ĐOẠN CODE MỚI >>>


block_cipher = None

# --- THU THAP CAC GOI CAN THIET ---

# 1. Thu thap toan bo du lieu va module an cua nbformat
nbformat_datas, nbformat_binaries, nbformat_hiddenimports = collect_all('nbformat')

# *** SỬA LỖI: Them buoc thu thap toan bo goi 'debugpy' ***
debugpy_datas, debugpy_binaries, debugpy_hiddenimports = collect_all('debugpy')

# 2. Dinh nghia cac module an can thiet khac mot cach chinh xac
required_hiddenimports = [
    'xml.parsers.expat',
    'xml.etree.ElementTree',
    'plistlib',
    'pkg_resources'
]

# 3. Tong hop lai cac thong tin
# <<< THAY ĐỔI: Thêm `imports_from_reqs` vào danh sách tổng >>>
all_hiddenimports = required_hiddenimports + nbformat_hiddenimports + debugpy_hiddenimports + imports_from_reqs

all_datas = [('logo.ico', '.')] + nbformat_datas + debugpy_datas
all_binaries = nbformat_binaries + debugpy_binaries


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
    console=True,
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