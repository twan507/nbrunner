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
    if path not in available_notebook_cards:
        return

    card = available_notebook_cards[path]
    is_ctrl_pressed = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier)

    if is_ctrl_pressed:
        if card.is_highlighted:
            card.set_highlighted(False)
            if path in highlighted_available:
                highlighted_available.remove(path)
        else:
            card.set_highlighted(True)
            if path not in highlighted_available:
                highlighted_available.append(path)
    else:
        if not card.is_highlighted:
            for p in list(highlighted_available):
                if p in available_notebook_cards:
                    available_notebook_cards[p].set_highlighted(False)

            highlighted_available.clear()
            highlighted_available.append(path)
            card.set_highlighted(True)
        else:
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


def format_output_for_cmd(title, content, width=100):
    separator = "=" * width
    formatted_title = f" {title} ".center(width, "=")

    return f"""{formatted_title}
{content.strip()}
{separator}"""


def handle_close_event(running_count, parent_widget=None):
    if running_count > 0:
        msg_box = QMessageBox(parent_widget)
        msg_box.setWindowTitle("Xác nhận thoát ứng dụng")
        msg_box.setText(f"Bạn có chắc muốn thoát ứng dụng không?\nCó {running_count} notebook(s) đang chạy sẽ bị dừng.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        msg_box.setIcon(QMessageBox.Icon.Question)

        # Apply stylesheet if parent has one
        if parent_widget and hasattr(parent_widget, "styleSheet") and parent_widget.styleSheet():
            msg_box.setStyleSheet(parent_widget.styleSheet())

        reply = msg_box.exec()
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
    # notebook_name = os.path.basename(notebook_path)
    notebook_dir = os.path.dirname(notebook_path)

    code_to_inject = f"""
import sys
import os
modules_path = {repr(modules_path)}
if os.path.exists(modules_path) and modules_path not in sys.path:
    sys.path.insert(0, modules_path)
    print(f"NBRunner: Đã thêm '{{modules_path}}' vào sys.path.")
"""

    def run_single_notebook():
        nb = None
        try:
            with open(notebook_path, "r", encoding="utf-8") as f:
                nb = nbformat.read(f, as_version=4)
            injected_cell = nbformat.v4.new_code_cell(code_to_inject)
            nb.cells.insert(0, injected_cell)

            # *** SỬA ĐỔI CHÍNH ***
            # Bằng cách không chỉ định 'kernel_name', nbconvert sẽ sử dụng
            # môi trường Python hiện tại để chạy notebook.
            # Trong một ứng dụng đã được đóng gói, đây chính là môi trường
            # Python mà PyInstaller đã nhúng vào.
            ep = ExecutePreprocessor(timeout=3600)
            ep.preprocess(nb, {"metadata": {"path": notebook_dir}})

            for cell in nb.cells:
                if "outputs" in cell:
                    for output in cell.outputs:
                        if output.output_type == "stream" and output.text.strip():
                            log_queue.put(("NOTEBOOK_PRINT", output.text))
            return True, nb
        except CellExecutionError as e:
            error_details = f"Lỗi trong cell:\n{e.ename}: {e.evalue}\n--- Traceback ---\n{traceback.format_exc()}"
            log_queue.put(("EXECUTION_ERROR", {"details": error_details}))
            return False, nb
        except Exception as e:
            error_details = f"Lỗi không mong muốn: {e}\n{traceback.format_exc()}"
            log_queue.put(("EXECUTION_ERROR", {"details": error_details}))
            return False, nb

    if execution_mode == "continuous":
        iteration = 1
        while not stop_event.is_set():
            # MODIFIED: Gửi tín hiệu reset timer
            log_queue.put(("RESET_TIMER", None))
            log_queue.put(("ITERATION_START", {"iteration": iteration, "total": None}))
            start_time = time.time()
            success, final_nb = run_single_notebook()
            duration = time.time() - start_time
            log_queue.put(("ITERATION_END", {"iteration": iteration, "success": success, "duration": duration}))

            if not success:
                break
            if stop_event.is_set():
                break

            if execution_delay > 0:
                log_queue.put(("SECTION_LOG", f"Nghỉ {execution_delay}s..."))
                time.sleep(execution_delay)
            iteration += 1
    else:
        for i in range(execution_count):
            if stop_event.is_set():
                log_queue.put(("SECTION_LOG", "Đã hủy các lần chạy còn lại."))
                break

            # MODIFIED: Gửi tín hiệu reset timer
            log_queue.put(("RESET_TIMER", None))
            log_queue.put(("ITERATION_START", {"iteration": i + 1, "total": execution_count}))
            start_time = time.time()
            success, final_nb = run_single_notebook()
            duration = time.time() - start_time
            log_queue.put(("ITERATION_END", {"iteration": i + 1, "success": success, "duration": duration}))

            if not success:
                break

    log_queue.put(("EXECUTION_FINISHED", True))


def run_notebook_with_individual_logging(
    notebook_path, running_processes, card, execution_mode, execution_count, execution_delay, modules_path
):
    if notebook_path in running_processes:
        return

    log_queue = Queue()
    stop_event = Event()
    process_args = (notebook_path, log_queue, stop_event, execution_mode, execution_count, execution_delay, modules_path)
    process = Process(target=_execute_notebook_process, args=process_args, daemon=True)
    running_processes[notebook_path] = {"process": process, "stop_event": stop_event, "queue": log_queue, "card": card}

    process.start()


def clear_all_card_selections(available_notebook_cards, highlighted_available):
    """Bỏ chọn tất cả notebook cards"""
    for path in list(highlighted_available):
        if path in available_notebook_cards:
            available_notebook_cards[path].set_highlighted(False)
    highlighted_available.clear()
