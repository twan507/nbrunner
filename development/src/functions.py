"""
Module chứa các hàm xử lý chức năng cho ứng dụng NotebookRunner
"""

import os
import sys
import traceback
import time
import nbformat
from multiprocessing import Process, Queue, Event

from PyQt6.QtWidgets import QMessageBox, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from nbconvert.preprocessors import ExecutePreprocessor
from nbclient.exceptions import CellExecutionError

import config


# --- CÁC HÀM TIỆN ÍCH (KHÔNG THAY ĐỔI) ---
def get_resource_path(relative_path):
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        return os.path.join(base_path, relative_path)
    return os.path.join(config.ROOT_DIR, relative_path)


def setup_window_icon(window):
    try:
        icon_path = get_resource_path("logo.ico") if getattr(sys, "frozen", False) else config.ICON_PATH
        if os.path.exists(icon_path):
            window.setWindowIcon(QIcon(icon_path))
    except Exception as e:
        print(f"[ERROR] Không thể thiết lập icon: {e}")


def setup_application_icon(app):
    if hasattr(config, "ICON_PATH") and os.path.exists(config.ICON_PATH):
        app.setWindowIcon(QIcon(config.ICON_PATH))


def handle_card_click(path, available_notebook_cards, highlighted_available):
    """
    MODIFIED: Logic được viết lại để phù hợp với việc xử lý sự kiện
    ở cả mousePress và mouseRelease, giải quyết vấn đề UX.
    """
    if path not in available_notebook_cards:
        return

    card = available_notebook_cards[path]
    is_ctrl_pressed = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier)

    if is_ctrl_pressed:
        # Nếu giữ Ctrl, logic không đổi: thêm/bớt lựa chọn
        if card.is_highlighted:
            card.set_highlighted(False)
            if path in highlighted_available:
                highlighted_available.remove(path)
        else:
            card.set_highlighted(True)
            if path not in highlighted_available:
                highlighted_available.append(path)
    else:
        # Nếu KHÔNG giữ Ctrl:
        if not card.is_highlighted:
            # Nếu click vào một mục CHƯA được chọn -> đây là hành động chọn mới.
            # Bỏ chọn tất cả các mục khác và chỉ chọn mục này.
            for p in list(highlighted_available):
                if p in available_notebook_cards:
                    available_notebook_cards[p].set_highlighted(False)

            highlighted_available.clear()
            highlighted_available.append(path)
            card.set_highlighted(True)
        else:
            # Nếu click vào một mục ĐÃ được chọn -> không làm gì cả ở sự kiện press.
            # Việc này để giữ nguyên danh sách lựa chọn cho thao tác KÉO THẢ.
            # Hành động "bỏ chọn các mục khác" sẽ được xử lý ở mouseReleaseEvent.
            pass


def refresh_notebook_list(notebooks_path, available_cards_layout, available_notebook_cards, highlighted_available, create_card_callback):
    if available_cards_layout is None:
        return
    try:
        while available_cards_layout.count() > 0:
            item = available_cards_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
    except RuntimeError:
        return
    available_notebook_cards.clear()
    highlighted_available.clear()
    try:
        if not os.path.exists(notebooks_path):
            raise FileNotFoundError(f"Thư mục không tồn tại: {notebooks_path}")
        notebook_files = sorted([f for f in os.listdir(notebooks_path) if f.endswith(".ipynb")])
        if not notebook_files:
            from PyQt6.QtWidgets import QLabel

            available_cards_layout.addWidget(QLabel("Không tìm thấy notebook."))
        else:
            for filename in notebook_files:
                path = os.path.join(notebooks_path, filename)
                try:
                    create_card_callback(path, available_cards_layout, available_notebook_cards)
                except RuntimeError:
                    return
    except Exception as e:
        from PyQt6.QtWidgets import QLabel

        available_cards_layout.addWidget(QLabel(f"Lỗi: {e}"))


def log_message(message):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def handle_close_event(running_threads):
    if running_threads:
        reply = QMessageBox.question(
            None,
            "Thoát",
            "Notebook đang chạy, bạn chắc chắn muốn thoát?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes
    return True


def get_notebook_description(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)
        for cell in notebook.cells:
            if cell.cell_type == "markdown":
                for line in cell.source.split("\n"):
                    if line.strip().startswith("# "):
                        return line.strip()[2:].strip()
        return "Không có mô tả"
    except Exception:
        return "Không thể đọc mô tả."


def _execute_notebook_process(notebook_path, log_queue, stop_event, execution_mode, execution_count, execution_delay, modules_path):
    notebook_name = os.path.basename(notebook_path)
    notebook_dir = os.path.dirname(notebook_path)

    def log(message):
        log_queue.put(message)

    code_to_inject = f"""
import sys
import os
modules_path = {repr(modules_path)}
if os.path.exists(modules_path) and modules_path not in sys.path:
    sys.path.insert(0, modules_path)
    print(f"NBRunner: Added '{{modules_path}}' to path.")
"""

    def run_single_notebook():
        nb = None
        try:
            with open(notebook_path, "r", encoding="utf-8") as f:
                nb = nbformat.read(f, as_version=4)
            injected_cell = nbformat.v4.new_code_cell(code_to_inject)
            nb.cells.insert(0, injected_cell)
            kernel_name = "nbrunner-venv"
            ep = ExecutePreprocessor(timeout=3600, kernel_name=kernel_name)
            log(f"Bắt đầu thực thi '{notebook_name}'...")
            ep.preprocess(nb, {"metadata": {"path": notebook_dir}})
            log(f"'{notebook_name}' đã thực thi thành công.")
            return True, nb
        except CellExecutionError as e:
            log(f"LỖI: '{notebook_name}' thất bại tại một cell.")
            log(f"Error Type: {e.ename}")
            log(f"Error Value: {e.evalue}")
            return False, nb
        except Exception as e:
            log(f"LỖI KHÔNG MONG MUỐN khi chạy '{notebook_name}': {e}\\n{traceback.format_exc()}")
            return False, nb

    if execution_mode == "continuous":
        iteration = 1
        while not stop_event.is_set():
            log(f"--- Bắt đầu lần lặp thứ {iteration} ---")
            log_queue.put(("reset_timer", None))
            success, final_nb = run_single_notebook()
            log_queue.put(("outputs", final_nb))
            if not success:
                log_queue.put(("finished", False))
                return
            if stop_event.is_set():
                break
            if execution_delay > 0:
                log(f"Nghỉ {execution_delay} giây trước lần lặp tiếp theo...")
                time.sleep(execution_delay)
            iteration += 1
    else:
        for i in range(execution_count):
            if stop_event.is_set():
                log("Đã nhận tín hiệu dừng, hủy bỏ các lần chạy còn lại.")
                break
            log(f"--- Bắt đầu lần chạy {i + 1}/{execution_count} ---")
            log_queue.put(("reset_timer", None))
            success, final_nb = run_single_notebook()
            log_queue.put(("outputs", final_nb))
            if not success:
                log_queue.put(("finished", False))
                return
    log_queue.put(("finished", True))


def run_notebook_with_individual_logging(
    notebook_path, running_processes, card, execution_mode, execution_count, execution_delay, modules_path
):
    if notebook_path in running_processes:
        if card:
            card.log_message(f"Notebook đã đang chạy: {os.path.basename(notebook_path)}")
        return

    log_queue = Queue()
    stop_event = Event()
    process_args = (notebook_path, log_queue, stop_event, execution_mode, execution_count, execution_delay, modules_path)
    process = Process(target=_execute_notebook_process, args=process_args, daemon=True)
    running_processes[notebook_path] = {"process": process, "stop_event": stop_event, "queue": log_queue}

    if card:
        card.start_log_listener(log_queue)
    process.start()
