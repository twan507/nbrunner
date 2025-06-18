import os
import sys


def get_root_dir():
    """
    Lấy thư mục gốc của dự án.
    Xử lý cả trường hợp chạy từ source code và từ file .exe đã build.
    """
    if getattr(sys, "frozen", False):
        # Khi chạy từ file .exe đã build bằng PyInstaller
        # sys.executable sẽ trỏ đến app.exe
        # Lấy thư mục chứa app.exe làm thư mục gốc
        return os.path.dirname(sys.executable)
    else:
        # Khi chạy từ source code
        # Từ development/src/config.py -> lên 2 cấp để đến thư mục gốc
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Lấy thư mục gốc
ROOT_DIR = get_root_dir()

# Tên ứng dụng sẽ hiển thị trên thanh tiêu đề và file .exe
APP_NAME = "Notebook Runner"

# Tên file .exe sẽ được tạo ra
EXE_FILE_NAME = "nbrunner.exe"

# Đường dẫn tuyệt đối đến file icon (cho PyInstaller build)
ICON_PATH = os.path.join(ROOT_DIR, "development", "logo.ico")

# Đường dẫn tuyệt đối đến thư mục chứa các modules
if getattr(sys, "frozen", False):
    # Khi chạy từ app.exe, modules nằm cùng cấp với app.exe
    MODULES_DIR = os.path.join(ROOT_DIR, "modules")
else:
    # Khi chạy từ source code
    MODULES_DIR = os.path.join(ROOT_DIR, "app", "modules")

# Đường dẫn tuyệt đối đến thư mục chứa các notebooks
if getattr(sys, "frozen", False):
    # Khi chạy từ app.exe, notebooks nằm cùng cấp với app.exe
    NOTEBOOKS_DIR = os.path.join(ROOT_DIR, "notebooks")
else:
    # Khi chạy từ source code
    NOTEBOOKS_DIR = os.path.join(ROOT_DIR, "app", "notebooks")

# Đường dẫn nơi app.exe sẽ được đặt sau khi build
APP_BUILD_DIR = os.path.join(ROOT_DIR, "app")


def get_pyinstaller_args():
    """
    Lấy các tham số PyInstaller cần thiết.
    Đã loại bỏ nbconvert vì không cần dùng PythonExporter nữa.
    """
    args = [
        "--hidden-import",
        "nbformat",
        "--collect-all",
        "nbformat",
    ]

    return args


# Các tham số PyInstaller bổ sung
PYINSTALLER_EXTRA_ARGS = get_pyinstaller_args()
