import sys
import os
import queue

# THÊM DÒNG NÀY
from multiprocessing import freeze_support

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QScrollArea,
    QGroupBox,
    QMessageBox,
    QSplitter,
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QCloseEvent

# Áp dụng chính sách event loop cho Windows để tương thích với ZMQ
if sys.platform == "win32":
    try:
        from asyncio import WindowsSelectorEventLoopPolicy
        import asyncio

        asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    except ImportError:
        pass

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))
try:
    import config
    import functions
    import styles
    from ui_components import NotebookCard, SectionWidget
except ImportError as e:
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    QMessageBox.critical(None, "Lỗi Import", f"Không thể import module cần thiết: {e}")
    sys.exit(1)


class NotebookRunner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.APP_NAME)
        self.available_notebook_cards = {}
        self.highlighted_available = set()
        self.sections = {}
        self.section_counter = 0
        self.available_container = None
        self.original_notebook_list_width = config.NOTEBOOK_LIST_INITIAL_WIDTH
        self.set_window_icon()
        self.base_path, self.modules_path, self.notebooks_path = functions.setup_paths()
        self.output_queue = queue.Queue()
        # Đổi tên cho rõ ràng, vì chúng ta đang dùng Process
        self.running_processes = {}
        self.setup_ui()
        self.apply_stylesheet()
        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self.check_output_queue)
        self.queue_timer.start(100)
        self._update_window_minimum_size()

    def set_window_icon(self):
        functions.setup_window_icon(self)

    def _calculate_minimum_window_size(self):
        min_width = config.NOTEBOOK_LIST_MIN_WIDTH + config.CONSOLE_MIN_WIDTH
        min_height = config.WINDOW_MIN_HEIGHT
        if hasattr(self, "sections"):
            min_width += len(self.sections) * config.SECTION_MIN_WIDTH
        return (min_width + 50), min_height

    def _update_window_minimum_size(self):
        min_width, min_height = self._calculate_minimum_window_size()
        self.setMinimumSize(min_width, min_height)

    def setup_ui(self):
        main_widget = QWidget()
        main_widget.setObjectName("MainWidget")
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setObjectName("MainSplitter")
        self.main_splitter.setHandleWidth(8)
        self.log_group = QGroupBox("📊 Console Log")
        self.log_group.setObjectName("LogGroup")
        log_layout = QVBoxLayout(self.log_group)
        log_layout.setSpacing(8)
        log_layout.setContentsMargins(5, 10, 5, 5)
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setFont(QFont("JetBrains Mono", 9))
        self.output_console.setObjectName("Console")
        clear_log_button = QPushButton("Xóa Console")
        clear_log_button.setObjectName("ClearButton")
        clear_log_button.clicked.connect(self.clear_console)
        log_layout.addWidget(self.output_console)
        log_layout.addWidget(clear_log_button)
        self.log_group.setMinimumWidth(config.CONSOLE_MIN_WIDTH)
        self.main_splitter.addWidget(self.log_group)
        self.available_container = QWidget()
        available_container_layout = QVBoxLayout(self.available_container)
        available_container_layout.setContentsMargins(0, 0, 0, 0)
        available_container_layout.setSpacing(10)
        available_group = QGroupBox("📚 Danh sách Notebooks")
        available_group.setObjectName("AvailableGroup")
        available_layout = QVBoxLayout(available_group)
        available_layout.setContentsMargins(5, 10, 5, 5)
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
        controls_group = QGroupBox("⚙️ Điều khiển")
        controls_group.setObjectName("ControlsGroup")
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setContentsMargins(5, 10, 5, 5)
        controls_layout.setSpacing(8)
        refresh_button = QPushButton("Làm Mới Danh Sách")
        refresh_button.setObjectName("RefreshButton")
        refresh_button.clicked.connect(self.refresh_notebook_list)
        add_section_button = QPushButton("Thêm Section Mới")
        add_section_button.setObjectName("AddSectionButton")
        add_section_button.clicked.connect(self.create_new_section)
        controls_layout.addWidget(refresh_button)
        controls_layout.addWidget(add_section_button)
        available_container_layout.addWidget(available_group)
        available_container_layout.addWidget(controls_group)
        self.available_container.setMinimumWidth(config.NOTEBOOK_LIST_MIN_WIDTH)
        self.main_splitter.addWidget(self.available_container)
        self.main_splitter.setSizes(config.SPLITTER_INITIAL_SIZES)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 1)
        main_layout.addWidget(self.main_splitter)
        self.refresh_notebook_list()
        self._update_window_minimum_size()
        self.update()
        QApplication.processEvents()

    def apply_stylesheet(self):
        self.setStyleSheet(styles.get_stylesheet())

    def _create_card_in_list(self, path, parent_layout, card_dict):
        description = functions.get_notebook_description(path)
        card = NotebookCard(path, description, self)
        card.clicked.connect(self._on_card_click)
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

    def run_notebook(self, notebook_path):
        # Hàm này có thể để trống hoặc ghi log vì logic đã chuyển vào section
        functions.run_notebook(notebook_path, self.running_processes, self.output_queue)

    def log_message(self, message):
        functions.log_message(message, self.output_queue)

    def check_output_queue(self):
        functions.check_output_queue(self.output_queue, self.output_console)

    def clear_console(self):
        self.output_console.clear()

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if functions.handle_close_event(self.running_processes):
            if a0:
                a0.accept()
        else:
            if a0:
                a0.ignore()

    def create_new_section(self):
        self.section_counter += 1
        section_name = f"Section {self.section_counter}"
        section_id = f"section_{self.section_counter}"
        section_widget = SectionWidget(section_name, section_id, self)
        section_widget.notebooks_dropped.connect(self.move_notebooks_to_section)
        section_widget.notebook_remove_requested.connect(self.remove_notebooks_from_section)
        section_widget.section_close_requested.connect(self.close_section)
        self.main_splitter.addWidget(section_widget)
        self.sections[section_id] = section_widget
        self._update_window_minimum_size()
        self.log_message(f"Đã tạo section mới: {section_name}")

    def move_notebooks_to_section(self, section_widget, paths_to_move):
        moved_count = 0
        for path in paths_to_move:
            if path in self.available_notebook_cards:
                old_card = self.available_notebook_cards[path]
                description = old_card.desc_label.text()
                self.available_cards_layout.removeWidget(old_card)
                old_card.deleteLater()
                del self.available_notebook_cards[path]
                section_widget.add_notebook_card(path, description)
                moved_count += 1
        self.highlighted_available.clear()
        if moved_count > 0:
            self.log_message(f"Đã kéo thả {moved_count} notebooks vào '{section_widget.section_name}'")

    def remove_notebooks_from_section(self, section_widget, paths):
        moved_count = 0
        for path in paths:
            if path in section_widget.notebook_cards:
                section_widget.remove_notebook_card(path)
                self._create_card_in_list(path, self.available_cards_layout, self.available_notebook_cards)
                moved_count += 1
        self.log_message(f"Đã trả {moved_count} notebooks từ {section_widget.section_name} về danh sách tổng")

    def close_section(self, section_widget):
        section_id = section_widget.section_id
        if section_widget.notebook_cards:
            self.remove_notebooks_from_section(section_widget, list(section_widget.notebook_cards.keys()))
        section_widget.cleanup()
        section_widget.setParent(None)
        section_widget.deleteLater()
        if section_id in self.sections:
            del self.sections[section_id]
        self._update_window_minimum_size()
        self.log_message(f"Đã đóng section: {section_widget.section_name}")


if __name__ == "__main__":
    # THÊM DÒNG NÀY làm dòng đầu tiên
    # Đây là chỉ thị bắt buộc cho multiprocessing trên Windows khi đóng gói
    freeze_support()

    app = QApplication(sys.argv)
    functions.setup_application_icon(app)
    window = NotebookRunner()
    try:
        screen = app.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = window.frameGeometry()
            window_geometry.moveCenter(screen_geometry.center())
            final_x = max(0, window_geometry.topLeft().x())
            final_y = max(0, window_geometry.topLeft().y())
            window.move(final_x, final_y)
    except Exception as e:
        print(f"Lỗi khi định vị cửa sổ: {e}")
    window.show()
    sys.exit(app.exec())
