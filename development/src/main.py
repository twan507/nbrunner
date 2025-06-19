import sys
import os
import threading
import queue
import time
import io
import traceback
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QScrollArea,
    QLabel,
    QFrame,
    QGroupBox,
    QMessageBox,
    QSplitter,
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QCloseEvent, QMouseEvent

# Import thư viện xử lý notebook
try:
    import nbformat
except ImportError:
    # Hiển thị lỗi bằng một cửa sổ đơn giản nếu PyQt chưa sẵn sàng
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    QMessageBox.critical(None, "Lỗi Import", "Không thể import nbformat. Vui lòng cài đặt thư viện cần thiết.")
    sys.exit(1)

# Import config
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))
try:
    import config
except ImportError:
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    QMessageBox.critical(None, "Lỗi Config", "Không thể import config.py. Vui lòng đảm bảo file config.py tồn tại.")
    sys.exit(1)


class ClickableLabel(QLabel):
    doubleClicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mouseDoubleClickEvent(self, a0: QMouseEvent | None) -> None:
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(a0)


class NotebookCard(QFrame):
    """Widget tùy chỉnh cho mỗi card notebook."""

    clicked = pyqtSignal(str)  # Signal to emit the path on click

    def __init__(self, path, description, parent=None):
        super().__init__(parent)
        self.path = path
        self.is_highlighted = False
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("Card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        self.filename_label = QLabel(os.path.basename(path))
        self.filename_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.filename_label.setObjectName("CardLabel")
        self.filename_label.setWordWrap(True)

        self.desc_label = QLabel(description)
        self.desc_label.setFont(QFont("Segoe UI", 9))
        self.desc_label.setObjectName("CardLabel")
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #666666;")

        layout.addWidget(self.filename_label)
        layout.addWidget(self.desc_label)

    def mousePressEvent(self, a0: QMouseEvent | None) -> None:
        self.clicked.emit(self.path)
        super().mousePressEvent(a0)

    def set_highlighted(self, highlighted):
        self.is_highlighted = highlighted
        if highlighted:
            self.setObjectName("SelectedCard")
        else:
            self.setObjectName("Card")
        # Re-polish to apply new style
        style = self.style()
        if style:
            style.unpolish(self)
            style.polish(self)


class NotebookRunner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.APP_NAME)
        self.setMinimumSize(800, 600)  # Giảm minimum size để linh hoạt hơn

        # --- Cấu trúc dữ liệu ---
        self.available_notebook_cards = {}
        self.highlighted_available = set()

        self.set_window_icon()

        # --- Thiết lập đường dẫn và queue ---
        self.base_path = config.ROOT_DIR
        self.modules_path = config.MODULES_DIR
        self.notebooks_path = config.NOTEBOOKS_DIR
        if os.path.exists(self.modules_path) and self.modules_path not in sys.path:
            sys.path.insert(0, self.modules_path)

        self.output_queue = queue.Queue()
        self.running_threads = {}

        self.setup_ui()
        self.apply_stylesheet()

        self.refresh_notebook_list()

        # --- Timer để kiểm tra output queue ---
        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self.check_output_queue)
        self.queue_timer.start(100)

        # --- Cập nhật kích thước cửa sổ ban đầu ---
        self._update_window_size(initial=True)

    def get_resource_path(self, relative_path):
        if getattr(sys, "frozen", False):
            base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
            return os.path.join(base_path, relative_path)
        return os.path.join(config.ROOT_DIR, relative_path)

    def set_window_icon(self):
        try:
            icon_path = self.get_resource_path("logo.ico") if getattr(sys, "frozen", False) else config.ICON_PATH
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"[ERROR] Không thể thiết lập icon: {e}")

    def _update_window_size(self, initial=False):
        """Cập nhật kích thước cửa sổ - chỉ set minimum size."""
        if initial:
            # Thiết lập kích thước ban đầu hợp lý
            self.resize(1000, 700)

    def setup_ui(self):
        """Thiết lập giao diện đơn giản với log và danh sách notebooks."""
        main_widget = QWidget()
        main_widget.setObjectName("MainWidget")
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Tạo QSplitter để có thể kéo thả resize các cột
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setObjectName("MainSplitter")
        main_splitter.setHandleWidth(8)

        # --- 1. Cột Log (bên trái) ---
        log_group = QGroupBox("📊 Console Log")
        log_group.setObjectName("LogGroup")
        log_layout = QVBoxLayout(log_group)
        log_layout.setSpacing(8)
        log_layout.setContentsMargins(12, 20, 12, 12)

        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setFont(QFont("JetBrains Mono", 9))
        self.output_console.setObjectName("Console")

        clear_log_button = QPushButton("🗑️ Xóa Console")
        clear_log_button.setObjectName("ClearButton")
        clear_log_button.clicked.connect(self.clear_console)

        log_layout.addWidget(self.output_console)
        log_layout.addWidget(clear_log_button)
        log_group.setMinimumWidth(300)  # Giảm minimum width
        main_splitter.addWidget(log_group)

        # --- 2. Cột Notebooks có sẵn & Điều khiển ---
        available_container = QWidget()
        available_container_layout = QVBoxLayout(available_container)
        available_container_layout.setContentsMargins(0, 0, 0, 0)
        available_container_layout.setSpacing(10)

        available_group = QGroupBox("📚 Notebooks có sẵn")
        available_group.setObjectName("AvailableGroup")
        available_layout = QVBoxLayout(available_group)
        available_layout.setContentsMargins(12, 20, 12, 12)
        available_layout.setSpacing(8)

        self.available_scroll_area = QScrollArea()
        self.available_scroll_area.setWidgetResizable(True)
        self.available_scroll_area.setObjectName("AvailableScrollArea")
        self.available_cards_widget = QWidget()
        self.available_cards_widget.setObjectName("CardsContainer")
        self.available_cards_layout = QVBoxLayout(self.available_cards_widget)
        self.available_cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.available_cards_layout.setSpacing(6)
        self.available_scroll_area.setWidget(self.available_cards_widget)
        available_layout.addWidget(self.available_scroll_area)

        # Các nút điều khiển
        controls_group = QGroupBox("⚙️ Điều khiển")
        controls_group.setObjectName("ControlsGroup")
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setContentsMargins(12, 20, 12, 12)
        controls_layout.setSpacing(8)

        refresh_button = QPushButton("🔄 Làm Mới Danh Sách")
        refresh_button.setObjectName("RefreshButton")
        refresh_button.clicked.connect(self.refresh_notebook_list)

        run_selected_button = QPushButton("▶️ Chạy Notebooks Đã Chọn")
        run_selected_button.setObjectName("RunSelectedButton")
        run_selected_button.clicked.connect(self.run_selected_notebooks)

        stop_all_button = QPushButton("⏹️ Dừng Tất Cả")
        stop_all_button.setObjectName("StopButton")
        stop_all_button.clicked.connect(self.stop_all_notebooks)

        controls_layout.addWidget(refresh_button)
        controls_layout.addWidget(run_selected_button)
        controls_layout.addWidget(stop_all_button)

        available_container_layout.addWidget(available_group)
        available_container_layout.addWidget(controls_group)
        available_container.setMinimumWidth(300)  # Giảm minimum width
        main_splitter.addWidget(available_container)

        # Thiết lập tỷ lệ ban đầu cho splitter
        main_splitter.setSizes([400, 400])  # Giảm size ban đầu
        main_splitter.setStretchFactor(0, 1)  # Console có thể stretch
        main_splitter.setStretchFactor(1, 1)  # Available có thể stretch

        main_layout.addWidget(main_splitter)

    def apply_stylesheet(self):
        stylesheet = """
            /* === MAIN WINDOW === */
            QMainWindow, #MainWidget {
                background-color: #f8f9fa;
                color: #2c3e50;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            
            /* === GROUP BOXES === */
            QGroupBox {
                font-family: "Segoe UI";
                font-size: 11pt;
                font-weight: bold;
                border: 2px solid #e9ecef;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: #ffffff;
                color: #2c3e50;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                left: 15px;
                color: #495057;
                background-color: #ffffff;
            }
            
            #LogGroup, #AvailableGroup, #ControlsGroup, #SectionGroup {
                border: 2px solid #dee2e6;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa);
            }
            
            #SectionGroup {
                border: 2px solid #dee2e6;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa);
                border-radius: 12px;
                padding: 5px;
            }
            
            #DefaultSectionGroup {
                border: 3px solid #28a745;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d4edda, stop:1 #c3e6cb);
                border-radius: 12px;
                padding: 5px;
            }
            
            /* === BUTTONS === */
            QPushButton {
                font-family: "Segoe UI";
                font-size: 10pt;
                font-weight: 500;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007bff, stop:1 #0056b3);
                color: #ffffff;
                border: none;
                padding: 10px 16px;
                border-radius: 8px;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0056b3, stop:1 #004085);
                color: #ffffff;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #004085, stop:1 #002752);
                color: #ffffff;
            }
            
            /* === SPECIALIZED BUTTONS === */
            #ClearButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6c757d, stop:1 #495057);
            }
            #ClearButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #495057, stop:1 #343a40);
            }
            
            #RefreshButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #28a745, stop:1 #1e7e34);
            }
            #RefreshButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e7e34, stop:1 #155724);
            }
            
            #StopButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc3545, stop:1 #bd2130);
            }            #StopButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #bd2130, stop:1 #a71e2a);
            }

            /* === TEXT AREAS === */
            #Console {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 2px solid #495057;
                border-radius: 8px;
                padding: 8px;
                font-family: "JetBrains Mono", "Consolas", monospace;
                selection-background-color: #007acc;
            }
            
            QTextEdit {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                color: #2c3e50;
                padding: 8px;
            }
            
            /* === SCROLL AREAS === */
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            #AvailableScrollArea, #SectionScrollArea, #SectionsScrollArea {
                border: 1px solid #e9ecef;
                border-radius: 8px;
                background-color: #ffffff;
            }
            
            /* === CARDS CONTAINER === */
            #CardsContainer {
                background-color: #ffffff;
                border-radius: 6px;
            }
            #SectionsContainer {
                background-color: transparent;
            }
            
            /* === CARDS === */
            #Card, #SelectedCard {
                border: 2px solid #e9ecef;
                border-radius: 10px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa);
                margin: 2px;
                padding: 4px;
            }
            #Card:hover {
                border: 2px solid #007bff;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e3f2fd, stop:1 #bbdefb);
            }
            #SelectedCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #cce5ff, stop:1 #99d6ff);
                border: 2px solid #007bff;
            }
            
            /* === LABELS === */
            QLabel, #CardLabel {
                background-color: transparent;
                border: none;
                color: #2c3e50;
            }
            
            #SectionsTitle {
                color: #495057;
                font-size: 12pt;
                font-weight: bold;
            }
            
            #SectionTitle {
                color: #343a40;
                font-weight: bold;
                padding: 5px 10px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f8f9fa, stop:1 #e9ecef);
                border-radius: 8px;
                border: 1px solid #dee2e6;
            }
            #SectionTitle:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e3f2fd, stop:1 #bbdefb);
                border: 1px solid #007bff;
            }
            
            /* === HEADERS === */
            #SectionsHeader {
                background-color: transparent;
                padding: 8px 0px;
                border-bottom: 1px solid #e9ecef;
            }
            
            #SectionHeader {
                background-color: transparent;
                padding: 2px 0px;
            }
            
            /* === MESSAGE BOXES === */
            QMessageBox {
                background-color: #ffffff;
                color: #2c3e50;
            }
            QMessageBox QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007bff, stop:1 #0056b3);
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0056b3, stop:1 #004085);
            }
            
            /* === INPUT DIALOGS === */
            QInputDialog {
                background-color: #ffffff;
                color: #2c3e50;
            }
            QInputDialog QLineEdit {
                background-color: #ffffff;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                padding: 8px;
                color: #2c3e50;
            }
              /* === SPLITTER === */
            QSplitter {
                background-color: #f8f9fa;
            }
            QSplitter::handle {
                background: transparent;
                border: none;
                margin: 0px;
            }
            QSplitter::handle:horizontal {
                width: 6px;
                border-radius: 0px;
            }
            QSplitter::handle:hover {
                background: rgba(0, 123, 255, 0.1);
                border: none;
            }
            #MainSplitter {
                background-color: transparent;
            }

            // ...existing code...
        """
        self.setStyleSheet(stylesheet)

    def _create_card_in_list(self, path, parent_layout, card_dict):
        description = self.get_notebook_description(path)
        card = NotebookCard(path, description)
        card.clicked.connect(self._on_card_click)  # Connect signal
        parent_layout.addWidget(card)
        card_dict[path] = card

    def _on_card_click(self, path):
        # Xác định card và list chứa nó (chỉ có available notebooks bây giờ)
        if path not in self.available_notebook_cards:
            return

        card_list = self.available_notebook_cards
        selection_set = self.highlighted_available

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

    def refresh_notebook_list(self):
        # Xóa các card cũ
        for i in reversed(range(self.available_cards_layout.count())):
            item = self.available_cards_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
        self.available_notebook_cards.clear()
        self.highlighted_available.clear()

        try:
            if not os.path.exists(self.notebooks_path):
                raise FileNotFoundError(f"Thư mục không tồn tại: {self.notebooks_path}")

            notebook_files = sorted([f for f in os.listdir(self.notebooks_path) if f.endswith(".ipynb")])

            if not notebook_files:
                no_files_label = QLabel("Không tìm thấy notebook.")
                no_files_label.setWordWrap(True)
                self.available_cards_layout.addWidget(no_files_label)
            else:
                for filename in notebook_files:
                    path = os.path.join(self.notebooks_path, filename)
                    self._create_card_in_list(path, self.available_cards_layout, self.available_notebook_cards)

        except Exception as e:
            error_label = QLabel(f"Lỗi: {e}")
            error_label.setWordWrap(True)
            self.available_cards_layout.addWidget(error_label)

    def get_notebook_description(self, path):
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

    def run_selected_notebooks(self):
        """Chạy các notebooks đã được chọn trong danh sách có sẵn."""
        if not self.highlighted_available:
            QMessageBox.information(self, "Thông báo", "Vui lòng chọn ít nhất một notebook để chạy.", QMessageBox.StandardButton.Ok)
            return

        self.log_message(f"--- Chạy {len(self.highlighted_available)} notebooks đã chọn ---")
        for path in list(self.highlighted_available):
            self.run_notebook(path)

    def run_notebook(self, notebook_path):
        notebook_name = os.path.basename(notebook_path)
        if notebook_path in self.running_threads:
            self.log_message(f"[{notebook_name}] Đang chạy, bỏ qua.")
            return
        thread = threading.Thread(target=self._run_notebook_thread, args=(notebook_path,))
        thread.daemon = True
        self.running_threads[notebook_path] = thread
        thread.start()

    def _run_notebook_thread(self, notebook_path):
        notebook_name = os.path.basename(notebook_path)
        try:
            self.output_queue.put(f"[{notebook_name}] Bắt đầu...")
            with open(notebook_path, "r", encoding="utf-8") as f:
                notebook = nbformat.read(f, as_version=4)

            python_code = self.convert_notebook_to_python(notebook)
            notebook_globals = {"__name__": f"nb_{notebook_name}", "__file__": notebook_path}

            old_stdout, old_stderr = sys.stdout, sys.stderr
            captured_output = io.StringIO()
            try:
                sys.stdout = sys.stderr = captured_output
                exec(python_code, notebook_globals)
                output = captured_output.getvalue()
                if output.strip():
                    self.output_queue.put(f"[{notebook_name}] Output:\n{output}")
                self.output_queue.put(f"[{notebook_name}] Hoàn thành!")
            except Exception as e:
                self.output_queue.put(f"[{notebook_name}] Lỗi: {e}\n{traceback.format_exc()}")
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr
        except Exception as e:
            self.output_queue.put(f"[{notebook_name}] Lỗi đọc file: {e}")
        finally:
            if notebook_path in self.running_threads:
                del self.running_threads[notebook_path]

    def stop_all_notebooks(self):
        if not self.running_threads:
            self.log_message("Không có notebook nào đang chạy.")
            return

        # Lưu ý: Việc dừng thread một cách an toàn trong Python là phức tạp.
        # Cách tiếp cận này chỉ ngăn các thread mới bắt đầu và xóa tham chiếu.
        # Các thread đang chạy sẽ tiếp tục cho đến khi hoàn thành.
        self.log_message(f"Gửi yêu cầu dừng {len(self.running_threads)} notebooks...")
        self.running_threads.clear()
        QMessageBox.information(self, "Dừng Notebooks", "Đã gửi yêu cầu dừng tất cả notebooks. Các tác vụ đang chạy sẽ hoàn thành.")

    def log_message(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.output_queue.put(f"[{timestamp}] {message}")

    def check_output_queue(self):
        while not self.output_queue.empty():
            message = self.output_queue.get_nowait()
            self.output_console.append(message)
            scrollbar = self.output_console.verticalScrollBar()
            if scrollbar:
                scrollbar.setValue(scrollbar.maximum())

    def clear_console(self):
        self.output_console.clear()

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if self.running_threads:
            reply = QMessageBox.question(
                self,
                "Thoát",
                "Notebook đang chạy, bạn chắc chắn muốn thoát?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if a0:
                if reply == QMessageBox.StandardButton.Yes:
                    a0.accept()
                else:
                    a0.ignore()
        elif a0:
            a0.accept()

    def convert_notebook_to_python(self, notebook):
        lines = []
        for cell in notebook.cells:
            if cell.cell_type == "code":
                # Bỏ qua các magic command không thể thực thi trực tiếp
                source_lines = [line for line in cell.source.split("\n") if not line.strip().startswith("%")]
                lines.append("\n".join(source_lines))
        return "\n\n".join(lines)


def main():
    app = QApplication(sys.argv)
    window = NotebookRunner()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
