"""
Module chứa các hàm xử lý chức năng cho ứng dụng NotebookRunner
"""

import os
import sys
import threading
import time
import io
import traceback
import nbformat
from PyQt6.QtWidgets import QMessageBox, QApplication, QInputDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import config


def get_resource_path(relative_path):
    """Lấy đường dẫn tài nguyên cho ứng dụng"""
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        return os.path.join(base_path, relative_path)
    return os.path.join(config.ROOT_DIR, relative_path)


def setup_window_icon(window):
    """Thiết lập icon cho cửa sổ"""
    try:
        icon_path = get_resource_path("logo.ico") if getattr(sys, "frozen", False) else config.ICON_PATH
        if os.path.exists(icon_path):
            window.setWindowIcon(QIcon(icon_path))
    except Exception as e:
        print(f"[ERROR] Không thể thiết lập icon: {e}")


def setup_application_icon(app):
    """Thiết lập icon cho ứng dụng"""
    if hasattr(config, "ICON_PATH") and os.path.exists(config.ICON_PATH):
        app.setWindowIcon(QIcon(config.ICON_PATH))


def update_window_size_for_section(window, section_added=True, section_width=None):
    """Cập nhật kích thước cửa sổ khi thêm/xóa section"""
    if section_width is None:
        section_width = config.SECTION_DISPLAY_WIDTH

    current_width = window.width()
    current_height = window.height()

    if section_added:
        # Tăng chiều rộng window để chứa section mới
        new_width = current_width + section_width
        max_width = 1920  # Full HD width
        new_width = min(new_width, max_width)
    else:
        # Giảm chiều rộng window
        new_width = current_width - section_width
        # Đảm bảo không nhỏ hơn kích thước tối thiểu
        base_width = 800
        console_width = 300 if hasattr(window, "console_visible") and window.console_visible else 0
        min_width = base_width + console_width
        new_width = max(new_width, min_width)

    window.resize(new_width, current_height)


def create_section_dialog(parent, default_name):
    """Hiển thị dialog để tạo section mới"""
    section_name, ok = QInputDialog.getText(parent, "Tạo Section Mới", "Nhập tên cho section:", text=default_name)

    if ok and section_name.strip():
        return section_name.strip()
    return None


def confirm_section_close(parent, section_name, notebook_count):
    """Hiển thị dialog xác nhận đóng section"""
    if notebook_count > 0:
        reply = QMessageBox.question(
            parent,
            "Xác Nhận Đóng Section",
            f"Section '{section_name}' có {notebook_count} notebooks. "
            "Các notebooks sẽ được trả về danh sách tổng. Bạn có chắc chắn muốn đóng?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes
    return True


def show_no_notebooks_selected_message(parent, message="Vui lòng chọn ít nhất một notebook."):
    """Hiển thị thông báo khi không có notebook nào được chọn"""
    QMessageBox.information(parent, "Thông báo", message)


def show_no_running_notebooks_message(parent, message="Không có notebook nào đang chạy."):
    """Hiển thị thông báo khi không có notebook nào đang chạy"""
    QMessageBox.information(parent, "Thông báo", message)


def move_notebooks_to_section(notebook_paths, available_cards, available_layout, section_widget, highlighted_set):
    """Di chuyển notebooks từ danh sách tổng vào section"""
    moved_count = 0

    for path in notebook_paths:
        if path in available_cards:
            # Lấy thông tin notebook
            description = get_notebook_description(path)

            # Thêm vào section
            section_widget.add_notebook_card(path, description)

            # Xóa khỏi danh sách tổng
            card = available_cards[path]
            available_layout.removeWidget(card)
            card.deleteLater()
            del available_cards[path]
            highlighted_set.discard(path)
            moved_count += 1

    return moved_count


def move_notebooks_from_section(notebook_paths, section_widget, available_layout, available_cards, create_card_callback):
    """Di chuyển notebooks từ section về danh sách tổng"""
    moved_count = 0

    for path in notebook_paths:
        if path in section_widget.notebook_cards:
            # Xóa khỏi section
            section_widget.remove_notebook_card(path)

            # Thêm lại vào danh sách tổng
            create_card_callback(path, available_layout, available_cards)
            moved_count += 1

    return moved_count


def calculate_window_size_for_sections(base_width, section_count, section_width, console_visible, console_width):
    """Tính toán kích thước cửa sổ dựa trên số lượng sections"""
    total_width = base_width + (section_count * section_width)
    if console_visible:
        total_width += console_width

    # Giới hạn chiều rộng tối đa
    max_width = 1920
    return min(total_width, max_width)


def get_notebook_description(path):
    """Lấy mô tả từ notebook"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)
        for cell in notebook.cells:
            if cell.cell_type == "markdown":
                source = "".join(cell.source)
                for line in source.split("\n"):
                    if line.strip().startswith("# "):
                        return line.strip()[2:].strip()
        return "Không có mô tả"
    except Exception:
        return "Không thể đọc mô tả."


def convert_notebook_to_python(notebook):
    """Chuyển đổi notebook thành mã Python"""
    lines = []
    for cell in notebook.cells:
        if cell.cell_type == "code":
            # Bỏ qua các magic command không thể thực thi trực tiếp
            source_lines = [line for line in cell.source.split("\n") if not line.strip().startswith("%")]
            lines.append("\n".join(source_lines))
    return "\n\n".join(lines)


def handle_card_click(path, available_notebook_cards, highlighted_available):
    """Xử lý sự kiện click trên card notebook"""
    # Xác định card và list chứa nó (chỉ có available notebooks bây giờ)
    if path not in available_notebook_cards:
        return

    card_list = available_notebook_cards
    selection_set = highlighted_available

    # Can't get event here directly, so we check modifiers from QApplication
    is_ctrl_pressed = QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier
    card = card_list[path]
    is_highlighted = card.is_highlighted

    if not is_ctrl_pressed:
        # Bỏ chọn tất cả trong list hiện tại
        current_selection = list(selection_set)
        for p in current_selection:
            if p in card_list:
                card_list[p].set_highlighted(False)
        selection_set.clear()
        # Chọn card mới
        card.set_highlighted(True)
        selection_set.add(path)
    else:
        # Toggle chọn với Ctrl
        card.set_highlighted(not is_highlighted)
        if card.is_highlighted:
            selection_set.add(path)
        else:
            selection_set.remove(path)


def refresh_notebook_list(notebooks_path, available_cards_layout, available_notebook_cards, highlighted_available, create_card_callback):
    """Làm mới danh sách notebook"""  # Kiểm tra layout có hợp lệ không
    if available_cards_layout is None:
        return

    try:
        # Test layout có hoạt động không bằng cách truy cập thuộc tính
        if hasattr(available_cards_layout, "count"):
            available_cards_layout.count()
        else:
            return
    except RuntimeError:
        return
    except Exception:
        return  # Xóa các card cũ một cách an toàn
    try:
        while available_cards_layout.count() > 0:
            item = available_cards_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
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

            no_files_label = QLabel("Không tìm thấy notebook.")
            no_files_label.setWordWrap(True)
            try:
                available_cards_layout.addWidget(no_files_label)
            except RuntimeError:
                return
        else:
            for filename in notebook_files:
                path = os.path.join(notebooks_path, filename)
                try:
                    create_card_callback(path, available_cards_layout, available_notebook_cards)
                except RuntimeError:
                    return
                except Exception:
                    pass

    except Exception as e:
        from PyQt6.QtWidgets import QLabel

        error_label = QLabel(f"Lỗi: {e}")
        error_label.setWordWrap(True)
        try:
            available_cards_layout.addWidget(error_label)
        except RuntimeError:
            return


def run_selected_notebooks(highlighted_available, log_callback, run_notebook_callback):
    """Chạy các notebooks đã được chọn"""
    if not highlighted_available:
        QMessageBox.information(None, "Thông báo", "Vui lòng chọn ít nhất một notebook để chạy.", QMessageBox.StandardButton.Ok)
        return

    log_callback(f"--- Chạy {len(highlighted_available)} notebooks đã chọn ---")
    for path in list(highlighted_available):
        run_notebook_callback(path)


def run_notebook_thread(notebook_path, output_queue, running_threads):
    """Thread để chạy notebook"""
    notebook_name = os.path.basename(notebook_path)
    try:
        output_queue.put(f"[{notebook_name}] Bắt đầu...")
        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)

        python_code = convert_notebook_to_python(notebook)
        notebook_globals = {"__name__": f"nb_{notebook_name}", "__file__": notebook_path}

        old_stdout, old_stderr = sys.stdout, sys.stderr
        captured_output = io.StringIO()
        try:
            sys.stdout = sys.stderr = captured_output
            exec(python_code, notebook_globals)
            output = captured_output.getvalue()
            if output.strip():
                output_queue.put(f"[{notebook_name}] Output:\n{output}")
            output_queue.put(f"[{notebook_name}] Hoàn thành!")
        except Exception as e:
            output_queue.put(f"[{notebook_name}] Lỗi: {e}\n{traceback.format_exc()}")
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
    except Exception as e:
        output_queue.put(f"[{notebook_name}] Lỗi đọc file: {e}")
    finally:
        if notebook_path in running_threads:
            del running_threads[notebook_path]


def run_notebook(notebook_path, running_threads, output_queue):
    """Chạy một notebook"""
    notebook_name = os.path.basename(notebook_path)
    if notebook_path in running_threads:
        output_queue.put(f"[{notebook_name}] Đang chạy, bỏ qua.")
        return
    thread = threading.Thread(target=run_notebook_thread, args=(notebook_path, output_queue, running_threads))
    thread.daemon = True
    running_threads[notebook_path] = thread
    thread.start()


def run_notebook_thread_with_section(notebook_path, output_queue, running_threads, section_name=None):
    """Thread để chạy notebook với thông tin section"""
    notebook_name = os.path.basename(notebook_path)
    prefix = f"[{section_name}][{notebook_name}]" if section_name else f"[{notebook_name}]"

    try:
        output_queue.put(f"{prefix} Bắt đầu...")
        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook = nbformat.read(f, as_version=4)

        python_code = convert_notebook_to_python(notebook)
        notebook_globals = {"__name__": f"nb_{notebook_name}", "__file__": notebook_path}

        old_stdout, old_stderr = sys.stdout, sys.stderr
        captured_output = io.StringIO()
        try:
            sys.stdout = sys.stderr = captured_output
            exec(python_code, notebook_globals)
            output = captured_output.getvalue()
            if output.strip():
                output_queue.put(f"{prefix} Output:\n{output}")
            output_queue.put(f"{prefix} Hoàn thành!")
        except Exception as e:
            output_queue.put(f"{prefix} Lỗi: {e}\n{traceback.format_exc()}")
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
    except Exception as e:
        output_queue.put(f"{prefix} Lỗi đọc file: {e}")
    finally:
        if notebook_path in running_threads:
            del running_threads[notebook_path]


def run_notebook_with_section(notebook_path, running_threads, output_queue, section_name=None):
    """Chạy một notebook với thông tin section"""
    notebook_name = os.path.basename(notebook_path)
    prefix = f"[{section_name}][{notebook_name}]" if section_name else f"[{notebook_name}]"

    if notebook_path in running_threads:
        output_queue.put(f"{prefix} Đang chạy, bỏ qua.")
        return
    thread = threading.Thread(target=run_notebook_thread_with_section, args=(notebook_path, output_queue, running_threads, section_name))
    thread.daemon = True
    running_threads[notebook_path] = thread
    thread.start()


def stop_all_notebooks(running_threads, log_callback):
    """Dừng tất cả notebooks"""
    if not running_threads:
        log_callback("Không có notebook nào đang chạy.")
        return

    # Lưu ý: Việc dừng thread một cách an toàn trong Python là phức tạp.
    # Cách tiếp cận này chỉ ngăn các thread mới bắt đầu và xóa tham chiếu.
    # Các thread đang chạy sẽ tiếp tục cho đến khi hoàn thành.
    log_callback(f"Gửi yêu cầu dừng {len(running_threads)} notebooks...")
    running_threads.clear()
    QMessageBox.information(None, "Dừng Notebooks", "Đã gửi yêu cầu dừng tất cả notebooks. Các tác vụ đang chạy sẽ hoàn thành.")


def log_message(message, output_queue):
    """Ghi log message"""
    timestamp = time.strftime("%H:%M:%S")
    output_queue.put(f"[{timestamp}] {message}")


def check_output_queue(output_queue, output_console):
    """Kiểm tra và hiển thị output từ queue"""
    while not output_queue.empty():
        message = output_queue.get_nowait()
        output_console.append(message)
        scrollbar = output_console.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())


def handle_close_event(running_threads):
    """Xử lý sự kiện đóng ứng dụng"""
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


def setup_paths():
    """Thiết lập các đường dẫn cần thiết"""
    base_path = config.ROOT_DIR
    modules_path = config.MODULES_DIR
    notebooks_path = config.NOTEBOOKS_DIR

    if os.path.exists(modules_path) and modules_path not in sys.path:
        sys.path.insert(0, modules_path)

    return base_path, modules_path, notebooks_path
