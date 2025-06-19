import sys
import os
import queue
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

# Import các module tùy chỉnh
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))
try:
    import config
    import functions
    import styles
except ImportError as e:
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    QMessageBox.critical(None, "Lỗi Import", f"Không thể import module cần thiết: {e}")
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
        self.base_path, self.modules_path, self.notebooks_path = functions.setup_paths()

        self.output_queue = queue.Queue()
        self.running_threads = {}

        self.setup_ui()
        # Thử enable lại stylesheet
        self.apply_stylesheet()

        # --- Timer để kiểm tra output queue ---
        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self.check_output_queue)
        self.queue_timer.start(100)

        # --- Cập nhật kích thước cửa sổ ban đầu ---
        self._update_window_size(initial=True)

    def set_window_icon(self):
        try:
            icon_path = functions.get_resource_path("logo.ico") if getattr(sys, "frozen", False) else config.ICON_PATH
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
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setObjectName("MainSplitter")
        self.main_splitter.setHandleWidth(8)

        # --- 1. Cột Log (bên trái) ---
        self.log_group = QGroupBox("📊 Console Log")
        self.log_group.setObjectName("LogGroup")
        log_layout = QVBoxLayout(self.log_group)
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
        self.log_group.setMinimumWidth(300)  # Giảm minimum width
        self.main_splitter.addWidget(self.log_group)

        # Ẩn console mặc định
        self.log_group.hide()
        self.console_visible = False

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

        # Nút toggle console
        self.toggle_console_button = QPushButton("📟 Hiện Console")
        self.toggle_console_button.setObjectName("ToggleConsoleButton")
        self.toggle_console_button.clicked.connect(self.toggle_console)

        refresh_button = QPushButton("🔄 Làm Mới Danh Sách")
        refresh_button.setObjectName("RefreshButton")
        refresh_button.clicked.connect(self.refresh_notebook_list)

        run_selected_button = QPushButton("▶️ Chạy Notebooks Đã Chọn")
        run_selected_button.setObjectName("RunSelectedButton")
        run_selected_button.clicked.connect(self.run_selected_notebooks)

        stop_all_button = QPushButton("⏹️ Dừng Tất Cả")
        stop_all_button.setObjectName("StopButton")
        stop_all_button.clicked.connect(self.stop_all_notebooks)

        controls_layout.addWidget(self.toggle_console_button)
        controls_layout.addWidget(refresh_button)
        controls_layout.addWidget(run_selected_button)
        controls_layout.addWidget(stop_all_button)

        available_container_layout.addWidget(available_group)
        available_container_layout.addWidget(controls_group)

        available_container.setMinimumWidth(300)  # Giảm minimum width
        self.main_splitter.addWidget(available_container)

        # Thiết lập tỷ lệ ban đầu cho splitter (console ẩn nên để size [0, 800])
        self.main_splitter.setSizes([0, 800])  # Console ẩn, available chiếm toàn bộ
        self.main_splitter.setStretchFactor(0, 1)  # Console có thể stretch
        self.main_splitter.setStretchFactor(1, 1)  # Available có thể stretch
        main_layout.addWidget(self.main_splitter)

        # Khởi tạo danh sách notebook ngay lập tức
        self.refresh_notebook_list()

        # Force update UI
        self.update()
        QApplication.processEvents()

    def apply_stylesheet(self):
        """Áp dụng stylesheet từ module styles"""
        self.setStyleSheet(styles.get_stylesheet())

    def _create_card_in_list(self, path, parent_layout, card_dict):
        description = functions.get_notebook_description(path)
        card = NotebookCard(path, description)
        card.clicked.connect(self._on_card_click)  # Connect signal
        parent_layout.addWidget(card)
        card_dict[path] = card

    def _on_card_click(self, path):
        functions.handle_card_click(path, self.available_notebook_cards, self.highlighted_available)

    def refresh_notebook_list(self):
        functions.refresh_notebook_list(
            self.notebooks_path,
            self.available_cards_layout,
            self.available_notebook_cards,
            self.highlighted_available,
            self._create_card_in_list,
        )

    def run_selected_notebooks(self):
        """Chạy các notebooks đã được chọn trong danh sách có sẵn."""
        functions.run_selected_notebooks(self.highlighted_available, self.log_message, self.run_notebook)

    def run_notebook(self, notebook_path):
        functions.run_notebook(notebook_path, self.running_threads, self.output_queue)

    def stop_all_notebooks(self):
        functions.stop_all_notebooks(self.running_threads, self.log_message)

    def log_message(self, message):
        functions.log_message(message, self.output_queue)

    def check_output_queue(self):
        functions.check_output_queue(self.output_queue, self.output_console)

    def toggle_console(self):
        """Ẩn/hiện console log"""
        if self.console_visible:
            self.log_group.hide()
            self.toggle_console_button.setText("📟 Hiện Console")
            self.console_visible = False
            # Cập nhật lại size của splitter để console không chiếm chỗ
            current_sizes = self.main_splitter.sizes()
            self.main_splitter.setSizes([0, current_sizes[0] + current_sizes[1]])
        else:
            self.log_group.show()
            self.toggle_console_button.setText("📟 Ẩn Console")
            self.console_visible = True
            # Chia đôi không gian cho console và available
            total_width = self.main_splitter.width()
            self.main_splitter.setSizes([total_width // 2, total_width // 2])

    def clear_console(self):
        self.output_console.clear()

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if functions.handle_close_event(self.running_threads):
            if a0:
                a0.accept()
        else:
            if a0:
                a0.ignore()


def main():
    app = QApplication(sys.argv)
    window = NotebookRunner()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
