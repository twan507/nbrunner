"""
Đây là điểm vào (entry-point) cho tiến trình kernel.
File này sẽ được build thành một file .exe riêng (có console).
"""
import sys
import os

def initialize_kernel_environment():
    """
    Thiết lập môi trường cho kernel, đặc biệt là sys.path.
    """
    if getattr(sys, "frozen", False):
        # Khi đã đóng gói, thư mục gốc là nơi chứa file .exe
        root_dir = os.path.dirname(sys.executable)
        # Thư mục modules nằm cùng cấp với kernel_launcher.exe
        modules_dir = os.path.join(root_dir, "modules")
    else:
        # Khi chạy ở môi trường dev
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        modules_dir = os.path.join(project_root, "app", "modules")

    if os.path.exists(modules_dir) and modules_dir not in sys.path:
        sys.path.insert(0, modules_dir)

    # Thiết lập chính sách event loop cho Windows
    if sys.platform == "win32":
        try:
            from asyncio import WindowsSelectorEventLoopPolicy, set_event_loop_policy
            set_event_loop_policy(WindowsSelectorEventLoopPolicy())
        except ImportError:
            pass

if __name__ == '__main__':
    # Thiết lập môi trường trước
    initialize_kernel_environment()
    
    # Khởi chạy instance của ipykernel
    from ipykernel import kernelapp as app
    app.launch_new_instance()