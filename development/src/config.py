import os
import sys


def get_root_dir():
    """
    Lấy thư mục gốc của dự án.
    Xử lý cả trường hợp chạy từ source code và từ file .exe đã build.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        development_dir = os.path.dirname(current_file_dir)
        project_root = os.path.dirname(development_dir)
        return project_root

ROOT_DIR = get_root_dir()
DEBUG = False
APP_NAME = "Notebook Runner"
EXE_FILE_NAME = "nbrunner.exe"
ICON_PATH = os.path.join(ROOT_DIR, "development", "logo.ico")

if getattr(sys, "frozen", False):
    MODULES_DIR = os.path.join(ROOT_DIR, "modules")
    NOTEBOOKS_DIR = os.path.join(ROOT_DIR, "notebooks")
else:
    MODULES_DIR = os.path.join(ROOT_DIR, "app", "modules")
    NOTEBOOKS_DIR = os.path.join(ROOT_DIR, "app", "notebooks")

APP_BUILD_DIR = os.path.join(ROOT_DIR, "app")

# ===== CÀI ĐẶT KÍCH THƯỚC UI =====
WINDOW_MIN_HEIGHT = 800
WINDOW_INITIAL_WIDTH = 600
WINDOW_INITIAL_HEIGHT = 800
CONSOLE_MIN_WIDTH = 300
CONSOLE_INITIAL_WIDTH = 300
NOTEBOOK_LIST_INITIAL_WIDTH = 300
NOTEBOOK_LIST_MIN_WIDTH = 300
SECTION_MIN_WIDTH = 300
SECTION_DISPLAY_WIDTH = 300
SPLITTER_INITIAL_SIZES = [CONSOLE_INITIAL_WIDTH, NOTEBOOK_LIST_INITIAL_WIDTH]