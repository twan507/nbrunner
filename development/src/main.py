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
    if sys.platform == "win32" and getattr(sys, "frozen", False) and win32console and win32gui:
        try:
            window = win32console.GetConsoleWindow()
            if window:
                win32gui.ShowWindow(window, 0)
        except Exception as e:
            print(f"Error hiding console: {e}")


def _initialize_environment():
    if getattr(sys, "frozen", False):
        root_dir = os.path.dirname(sys.executable)
        modules_dir = os.path.join(root_dir, "modules")
    else:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        modules_dir = os.path.join(project_root, "app", "modules")

    if os.path.exists(modules_dir) and modules_dir not in sys.path:
        sys.path.insert(0, modules_dir)


def _launch_kernel():
    from ipykernel import kernelapp as app

    app.launch_new_instance()


def main():
    from PyQt6.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QPushButton,
        QScrollArea,
        QGroupBox,
        QSplitter,
    )
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QCloseEvent
    import time

    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))
    import config
    import functions
    import styles
    from ui_components import NotebookCard, SectionWidget

    class NotebookRunner(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(config.APP_NAME)
            self.notebooks_path = config.NOTEBOOKS_DIR
            self.modules_path = config.MODULES_DIR
            self.available_notebook_cards = {}
            self.highlighted_available = []
            self.sections = {}
            self.section_counter = 0
            self.available_container = None
            self.set_window_icon()
            self.running_processes = {}
            self.setup_ui()
            self.apply_stylesheet()
            self._update_window_minimum_size()

        def set_window_icon(self):
            functions.setup_window_icon(self)

        def _calculate_minimum_window_size(self):
            min_width = config.NOTEBOOK_LIST_MIN_WIDTH
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
            main_layout.addWidget(self.main_splitter)
            self.refresh_notebook_list()
            self._update_window_minimum_size()
            self.update()
            QApplication.processEvents()
            self.create_new_section()

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

        def clear_all_selections(self):
            """Bỏ chọn tất cả notebook cards"""
            for path in list(self.highlighted_available):
                if path in self.available_notebook_cards:
                    self.available_notebook_cards[path].set_highlighted(False)
            self.highlighted_available.clear()

        def mousePressEvent(self, a0):
            """Xử lý click chuột - nếu click ra ngoài card thì bỏ chọn tất cả"""
            if not a0:
                return

            # Lấy widget tại vị trí click
            widget_at_pos = self.childAt(a0.pos())

            # Kiểm tra xem có click vào notebook card nào không
            clicked_on_card = False
            if widget_at_pos:
                # Duyệt lên các parent để tìm NotebookCard
                current_widget = widget_at_pos
                while current_widget:
                    if hasattr(current_widget, "__class__") and current_widget.__class__.__name__ == "NotebookCard":
                        clicked_on_card = True
                        break
                    current_widget = current_widget.parent()

            # Nếu không click vào card nào, bỏ chọn tất cả
            if not clicked_on_card:
                self.clear_all_selections()

            # Gọi method gốc
            super().mousePressEvent(a0)

        def refresh_notebook_list(self):
            functions.refresh_notebook_list(
                self.notebooks_path,
                self.available_cards_layout,
                self.available_notebook_cards,
                self.highlighted_available,
                self._create_card_in_list,
            )

        def log_message_to_cmd(self, message, is_block=False):
            """
            MODIFIED: Handles both simple messages and formatted blocks.
            """
            if is_block:
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}]")
                print(message)
            else:
                functions.log_message(message)

        def closeEvent(self, a0: QCloseEvent | None) -> None:
            total_running = sum(len(s.running_processes) for s in self.sections.values())
            reply = functions.handle_close_event(total_running, self)
            if reply:
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
            self.log_message_to_cmd(f"Đã tạo section mới: {section_name}")

        def move_notebooks_to_section(self, section_widget, paths_to_move):
            for path in paths_to_move:
                if path in self.available_notebook_cards:
                    old_card = self.available_notebook_cards[path]
                    description = old_card.desc_label.text()
                    self.available_cards_layout.removeWidget(old_card)
                    old_card.deleteLater()
                    del self.available_notebook_cards[path]
                    section_widget.add_notebook_card(path, description)

                    nb_name = os.path.basename(path)
                    self.log_message_to_cmd(f"Đã thêm notebook '{nb_name}' vào section '{section_widget.section_name}'.")

            self.highlighted_available.clear()

        def remove_notebooks_from_section(self, section_widget, paths):
            for path in paths:
                if path in section_widget.notebook_cards:
                    section_widget.remove_notebook_card(path)
                    self._create_card_in_list(path, self.available_cards_layout, self.available_notebook_cards)

                    nb_name = os.path.basename(path)
                    self.log_message_to_cmd(f"Đã loại bỏ notebook '{nb_name}' khỏi section '{section_widget.section_name}'.")

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
            self.log_message_to_cmd(f"Đã đóng section: {section_widget.section_name}")

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
    _hide_console_window_on_windows()
    _initialize_environment()

    if "-f" in sys.argv:
        _launch_kernel()
    else:
        try:
            main()
        except Exception as e:
            import traceback

            print("=" * 60)
            print("LỖI KHỞI ĐỘNG ỨNG DỤNG:")
            print("=" * 60)
            print(f"Lỗi: {str(e)}")
            print("\nChi tiết lỗi:")
            print(traceback.format_exc())
            print("=" * 60)
            input("Nhấn Enter để thoát...")
