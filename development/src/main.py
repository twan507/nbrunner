import sys
import os
from multiprocessing import freeze_support

# Them import cho viec an console
if sys.platform == "win32":
    try:
        import win32gui
        import win32console
    except ImportError:
        # Neu khong co pywin32, bo qua de khong gay loi khi chay tren he dieu hanh khac
        win32gui = None
        win32console = None


# Fix for zmq warning on Windows: "Proactor event loop does not implement add_reader"
if sys.platform == "win32":
    try:
        from asyncio import WindowsSelectorEventLoopPolicy, set_event_loop_policy

        set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    except ImportError:
        pass


def _hide_console_window_on_windows():
    """
    Tim va an cua so console cua tien trinh hien tai.
    Chi hoat dong tren Windows va khi duoc build thanh file .exe.
    """
    if sys.platform == "win32" and getattr(sys, "frozen", False) and win32console and win32gui:
        try:
            window = win32console.GetConsoleWindow()
            if window:
                win32gui.ShowWindow(window, 0)  # 0 = SW_HIDE
        except Exception as e:
            # In ra de biet neu co loi, mac du nguoi dung se khong thay
            print(f"Error hiding console: {e}")


def _initialize_environment():
    """
    Thiet lap cac duong dan va moi truong can thiet.
    """
    if getattr(sys, "frozen", False):
        root_dir = os.path.dirname(sys.executable)
        modules_dir = os.path.join(root_dir, "modules")
    else:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        modules_dir = os.path.join(project_root, "app", "modules")

    if os.path.exists(modules_dir) and modules_dir not in sys.path:
        sys.path.insert(0, modules_dir)


def _launch_kernel():
    """Ham rieng biet chi de khoi chay kernel."""
    from ipykernel import kernelapp as app

    app.launch_new_instance()


def main():
    """Ham chinh de chay ung dung GUI."""
    import queue
    from PyQt6.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QPushButton,
        QTextEdit,
        QScrollArea,
        QGroupBox,
        QSplitter,
    )
    from PyQt6.QtCore import QTimer, Qt
    from PyQt6.QtGui import QFont, QCloseEvent

    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))
    import config
    import functions
    import styles
    from ui_components import NotebookCard, SectionWidget

    # --- Lop NotebookRunner va cac phuong thuc giu nguyen ---
    class NotebookRunner(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(config.APP_NAME)
            self.notebooks_path = config.NOTEBOOKS_DIR
            self.modules_path = config.MODULES_DIR
            self.available_notebook_cards = {}
            self.highlighted_available = set()
            self.sections = {}
            self.section_counter = 0
            self.available_container = None
            self.set_window_icon()
            self.output_queue = queue.Queue()
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


if __name__ == "__main__":
    freeze_support()

    # *** THAY DOI QUAN TRONG NHAT O DAY ***
    # An cua so console di ngay khi ung dung .exe khoi dong
    _hide_console_window_on_windows()

    _initialize_environment()

    if "-f" in sys.argv:
        _launch_kernel()
    else:
        main()
