"""
Module chứa các hàm xử lý chức năng cho ứng dụng NotebookRunner
"""

import os
import sys
import io
import traceback
import time
import nbformat
from multiprocessing import Process, Queue, Event

from PyQt6.QtWidgets import QMessageBox, QApplication, QInputDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from nbconvert.preprocessors import ExecutePreprocessor
# SỬA LỖI 1: Sửa đường dẫn import cho CellExecutionError
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

def create_section_dialog(parent, default_name):
    section_name, ok = QInputDialog.getText(parent, "Tạo Section Mới", "Nhập tên cho section:", text=default_name)
    if ok and section_name.strip():
        return section_name.strip()
    return None

def confirm_section_close(parent, section_name, notebook_count):
    if notebook_count > 0:
        reply = QMessageBox.question(
            parent, "Xác Nhận Đóng Section",
            f"Section '{section_name}' có {notebook_count} notebooks. "
            "Các notebooks sẽ được trả về danh sách tổng. Bạn có chắc chắn muốn đóng?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes
    return True

def handle_card_click(path, available_notebook_cards, highlighted_available):
    if path not in available_notebook_cards: return
    card_list = available_notebook_cards
    selection_set = highlighted_available
    is_ctrl_pressed = QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier
    card = card_list[path]
    is_highlighted = card.is_highlighted
    if not is_ctrl_pressed:
        for p in list(selection_set):
            if p in card_list: card_list[p].set_highlighted(False)
        selection_set.clear()
        card.set_highlighted(True)
        selection_set.add(path)
    else:
        card.set_highlighted(not is_highlighted)
        if card.is_highlighted: selection_set.add(path)
        else: selection_set.remove(path)

def refresh_notebook_list(notebooks_path, available_cards_layout, available_notebook_cards, highlighted_available, create_card_callback):
    if available_cards_layout is None: return
    try:
        while available_cards_layout.count() > 0:
            item = available_cards_layout.takeAt(0)
            if item and item.widget(): item.widget().deleteLater()
    except RuntimeError: return
    available_notebook_cards.clear()
    highlighted_available.clear()
    try:
        if not os.path.exists(notebooks_path): raise FileNotFoundError(f"Thư mục không tồn tại: {notebooks_path}")
        notebook_files = sorted([f for f in os.listdir(notebooks_path) if f.endswith(".ipynb")])
        if not notebook_files:
            from PyQt6.QtWidgets import QLabel
            available_cards_layout.addWidget(QLabel("Không tìm thấy notebook."))
        else:
            for filename in notebook_files:
                path = os.path.join(notebooks_path, filename)
                try: create_card_callback(path, available_cards_layout, available_notebook_cards)
                except RuntimeError: return
    except Exception as e:
        from PyQt6.QtWidgets import QLabel
        available_cards_layout.addWidget(QLabel(f"Lỗi: {e}"))

def log_message(message, output_queue):
    timestamp = time.strftime("%H:%M:%S")
    output_queue.put(f"[{timestamp}] {message}")

def check_output_queue(output_queue, output_console):
    while not output_queue.empty():
        message = output_queue.get_nowait()
        output_console.append(message)
        scrollbar = output_console.verticalScrollBar()
        if scrollbar: scrollbar.setValue(scrollbar.maximum())

def handle_close_event(running_threads):
    if running_threads:
        reply = QMessageBox.question(
            None, "Thoát", "Notebook đang chạy, bạn chắc chắn muốn thoát?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    return True

def setup_paths():
    base_path, modules_path, notebooks_path = config.ROOT_DIR, config.MODULES_DIR, config.NOTEBOOKS_DIR
    if os.path.exists(modules_path) and modules_path not in sys.path:
        sys.path.insert(0, modules_path)
    return base_path, modules_path, notebooks_path

def get_notebook_description(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)
        for cell in notebook.cells:
            if cell.cell_type == "markdown":
                for line in cell.source.split("\n"):
                    if line.strip().startswith("# "): return line.strip()[2:].strip()
        return "Không có mô tả"
    except Exception:
        return "Không thể đọc mô tả."

# SỬA LỖI 3: Thêm lại hàm này để main.py không báo lỗi,
# mặc dù nó không còn được sử dụng trong logic chính của các section
def run_notebook(notebook_path, running_threads, output_queue):
    """Chạy một notebook (phiên bản cũ cho console log)."""
    log_message(f"Lệnh `run_notebook` không còn được hỗ trợ trong logic Section. Sử dụng các nút trong Section.", output_queue)


# --- LÕI THỰC THI NOTEBOOK (SỬA LỖI VÀ HOÀN THIỆN) ---

def _execute_notebook_process(notebook_path, log_queue, stop_event, execution_mode, execution_count):
    """
    Hàm này chạy trong một tiến trình (Process) riêng biệt để thực thi notebook.
    Điều này đảm bảo an toàn và cho phép dừng tiến trình một cách triệt để.
    """
    notebook_name = os.path.basename(notebook_path)
    notebook_dir = os.path.dirname(notebook_path)

    def log(message):
        log_queue.put(message)

    def run_single_notebook():
        """Thực thi notebook một lần duy nhất bằng ExecutePreprocessor."""
        nb = None
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                nb = nbformat.read(f, as_version=4)
            
            # SỬA LỖI: Bỏ tham số kernel_name='python3'
            # Để nbconvert tự động sử dụng kernel của môi trường hiện tại.
            ep = ExecutePreprocessor(timeout=3600)
            
            log(f"Bắt đầu thực thi '{notebook_name}'...")
            ep.preprocess(nb, {'metadata': {'path': notebook_dir}})
            log(f"'{notebook_name}' đã thực thi thành công.")
            return True, nb
        except CellExecutionError:
            log(f"LỖI: '{notebook_name}' thất bại tại một cell.")
            return False, nb
        except Exception as e:
            log(f"LỖI KHÔNG MONG MUỐN khi chạy '{notebook_name}': {e}\n{traceback.format_exc()}")
            return False, nb
    
    # Vòng lặp điều khiển dựa trên chế độ chạy
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
            iteration += 1
            # ĐÃ XÓA 2 DÒNG time.sleep(1) VÀ log TẠI ĐÂY
            
    else: # Chế độ "count"
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


def run_notebook_with_individual_logging(notebook_path, running_processes, card, execution_mode, execution_count):
    if notebook_path in running_processes:
        if card: card.log_message(f"Notebook đã đang chạy: {os.path.basename(notebook_path)}")
        return

    log_queue = Queue()
    stop_event = Event()
    process = Process(target=_execute_notebook_process, args=(notebook_path, log_queue, stop_event, execution_mode, execution_count), daemon=True)
    running_processes[notebook_path] = {'process': process, 'stop_event': stop_event, 'queue': log_queue}
    
    if card: card.start_log_listener(log_queue)
    process.start()