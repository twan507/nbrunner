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
    QGroupBox,
    QMessageBox,
    QSplitter,
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont, QCloseEvent

# Import các module tùy chỉnh
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
        # Không set minimum size ở đây, sẽ tính dựa trên các cột

        # --- Cấu trúc dữ liệu ---
        self.available_notebook_cards = {}
        self.highlighted_available = set()  # --- Quản lý sections ---
        self.sections = {}  # Dict chứa các SectionWidget
        self.section_counter = 0  # Counter để tạo ID unique cho section
        self.available_container = None  # Sẽ được gán trong setup_ui

        # --- Quản lý console visibility ---
        self.console_visible = False
        # --- Lưu trữ size gốc của notebook list để luôn khôi phục đúng ---
        self.original_notebook_list_width = config.NOTEBOOK_LIST_INITIAL_WIDTH

        self.set_window_icon()
        # --- Thiết lập đường dẫn và queue ---
        self.base_path, self.modules_path, self.notebooks_path = functions.setup_paths()

        self.output_queue = queue.Queue()
        self.running_threads = {}

        self.setup_ui()
        # Thử enable lại stylesheet
        self.apply_stylesheet()  # --- Timer để kiểm tra output queue ---
        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self.check_output_queue)
        self.queue_timer.start(100)  # --- Cập nhật kích thước cửa sổ ban đầu ---
        self._update_window_size(initial=True)

    def set_window_icon(self):
        functions.setup_window_icon(self)

    def _calculate_minimum_window_size(self):
        """Tính toán kích thước minimum window dựa trên các cột đang hiển thị"""
        min_width = 0
        min_height = config.WINDOW_MIN_HEIGHT

        # Cột notebooks luôn hiển thị
        notebook_width = config.NOTEBOOK_LIST_MIN_WIDTH
        # Thêm padding nếu có nhiều notebooks (có thể có scrollbar)
        if hasattr(self, "available_notebook_cards") and len(self.available_notebook_cards) > 5:
            notebook_width += config.NOTEBOOK_LIST_SCROLLBAR_PADDING
        min_width += notebook_width

        # Cột console nếu đang hiển thị
        if hasattr(self, "console_visible") and self.console_visible:
            min_width += config.CONSOLE_MIN_WIDTH

        # Các cột sections
        if hasattr(self, "sections"):
            for section_widget in self.sections.values():
                section_width = config.SECTION_MIN_WIDTH
                # Thêm padding nếu section có nhiều notebooks (có thể có scrollbar)
                if hasattr(section_widget, "notebook_cards") and len(section_widget.notebook_cards) > 5:
                    section_width += config.SECTION_SCROLLBAR_PADDING
                min_width += section_width

        return min_width, min_height

    def _update_window_minimum_size(self):
        """Cập nhật minimum size của window"""
        min_width, min_height = self._calculate_minimum_window_size()
        print(f"DEBUG: Updating minimum size to {min_width}x{min_height}")
        self.setMinimumSize(min_width, min_height)
        print(f"DEBUG: Actual minimum size after setting: {self.minimumSize().width()}x{self.minimumSize().height()}")

    def _update_window_size(self, initial=False):
        """Cập nhật kích thước cửa sổ ban đầu"""
        if initial:
            # Thiết lập kích thước ban đầu: chỉ có cột notebooks
            self.resize(config.WINDOW_INITIAL_WIDTH, config.WINDOW_INITIAL_HEIGHT)
            self._update_window_minimum_size()

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
        self.log_group.setMinimumWidth(config.CONSOLE_MIN_WIDTH)  # Console min width
        self.main_splitter.addWidget(self.log_group)

        # Ẩn console mặc định
        self.log_group.hide()
        self.console_visible = False

        # --- 2. Cột Notebooks có sẵn & Điều khiển ---
        self.available_container = QWidget()
        available_container_layout = QVBoxLayout(self.available_container)
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
        # Đặt minimum width để luôn có đủ chỗ cho scrollbar
        self.available_scroll_area.setMinimumWidth(config.NOTEBOOK_LIST_MIN_WIDTH)

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
        refresh_button.clicked.connect(self.refresh_notebook_list)  # Nút thêm section mới
        add_section_button = QPushButton("➕ Thêm Section Mới")
        add_section_button.setObjectName("RefreshButton")
        add_section_button.clicked.connect(self.create_new_section)

        controls_layout.addWidget(self.toggle_console_button)
        controls_layout.addWidget(refresh_button)
        controls_layout.addWidget(add_section_button)

        available_container_layout.addWidget(available_group)
        available_container_layout.addWidget(controls_group)

        self.available_container.setMinimumWidth(config.NOTEBOOK_LIST_MIN_WIDTH)  # Notebook list min width
        self.main_splitter.addWidget(self.available_container)

        # Thiết lập tỷ lệ ban đầu cho splitter (console ẩn, chỉ có notebook list)
        self.main_splitter.setSizes(config.SPLITTER_INITIAL_SIZES)  # Console ẩn, available chiếm initial width
        self.main_splitter.setStretchFactor(0, 1)  # Console có thể stretch
        self.main_splitter.setStretchFactor(1, 1)  # Available có thể stretch
        main_layout.addWidget(self.main_splitter)  # Khởi tạo danh sách notebook ngay lập tức
        self.refresh_notebook_list()

        # Cập nhật minimum size sau khi setup UI hoàn tất
        self._update_window_minimum_size()

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
        """Ẩn/hiện console log và cập nhật minimum size của window"""
        console_display_width = config.CONSOLE_DISPLAY_WIDTH  # Độ rộng hiển thị của console

        if self.console_visible:
            # Ẩn console
            self.log_group.hide()
            self.toggle_console_button.setText("📟 Hiện Console")
            self.console_visible = False  # Lưu kích thước hiện tại của các cột (trừ console)
            current_sizes = self.main_splitter.sizes()
            if len(current_sizes) > 1:
                # Đảm bảo notebook list giữ kích thước gốc, đặt console = 0
                new_sizes = [0] + current_sizes[1:]
                # Notebook list bây giờ ở vị trí index 1
                if len(new_sizes) > 1:
                    new_sizes[1] = self.original_notebook_list_width
                    print(f"DEBUG: Toggle console OFF - Original notebook list width: {self.original_notebook_list_width}")
                    print(f"DEBUG: Toggle console OFF - New sizes: {new_sizes}")
                self.main_splitter.setSizes(new_sizes)

            # Giảm kích thước window
            current_width = self.width()
            new_width = current_width - console_display_width
            self.resize(new_width, self.height())

            # Cập nhật minimum size
            self._update_window_minimum_size()

        else:
            # Hiện console
            self.log_group.show()
            self.toggle_console_button.setText("📟 Ẩn Console")
            self.console_visible = True  # Lưu kích thước hiện tại của notebook list và sections
            current_sizes = self.main_splitter.sizes()
            if len(current_sizes) > 0:
                # Chèn console vào đầu, đảm bảo notebook list giữ kích thước gốc
                new_sizes = [console_display_width] + current_sizes[1:]
                # Notebook list bây giờ ở vị trí index 1
                if len(new_sizes) > 1:
                    new_sizes[1] = self.original_notebook_list_width
                    print(f"DEBUG: Toggle console ON - Original notebook list width: {self.original_notebook_list_width}")
                    print(f"DEBUG: Toggle console ON - New sizes: {new_sizes}")
                self.main_splitter.setSizes(new_sizes)

            # Tăng kích thước window để chứa console
            current_width = self.width()
            new_width = current_width + console_display_width
            self.resize(new_width, self.height())

            # Cập nhật minimum size
            self._update_window_minimum_size()

    def clear_console(self):
        self.output_console.clear()

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if functions.handle_close_event(self.running_threads):
            if a0:
                a0.accept()
        else:
            if a0:
                a0.ignore()

    # === METHODS ĐỂ QUẢN LÝ SECTIONS ===

    def create_new_section(self):
        """Tạo một section mới"""
        section_name = functions.create_section_dialog(self, f"Section {self.section_counter + 1}")

        if not section_name:
            return

        self.section_counter += 1
        section_id = f"section_{self.section_counter}"

        # Tạo SectionWidget
        section_widget = SectionWidget(section_name, section_id, self)  # Kết nối signals
        section_widget.notebook_add_requested.connect(self.add_notebooks_to_section)
        section_widget.notebook_remove_requested.connect(self.remove_notebooks_from_section)
        section_widget.section_close_requested.connect(self.close_section)

        # Lưu kích thước hiện tại của tất cả các cột TRƯỚC khi thêm
        current_sizes = self.main_splitter.sizes()
        print(f"DEBUG: Tạo section - Current sizes before: {current_sizes}")

        # Thêm vào splitter
        self.main_splitter.addWidget(section_widget)
        self.sections[section_id] = section_widget  # Sử dụng QTimer để đảm bảo widget đã được thêm hoàn toàn trước khi set sizes

        # Tăng kích thước window để chứa section mới
        current_width = self.width()
        new_width = current_width + config.SECTION_DISPLAY_WIDTH
        self.resize(new_width, self.height())

        self.log_message(f"Đã tạo section mới: {section_name}")

    def add_notebooks_to_section(self, section_widget):
        """Thêm notebooks đã chọn từ danh sách tổng vào section"""
        if not self.highlighted_available:
            functions.show_no_notebooks_selected_message(self, "Vui lòng chọn ít nhất một notebook từ danh sách có sẵn.")
            return

        paths_to_move = list(self.highlighted_available)
        moved_count = functions.move_notebooks_to_section(
            paths_to_move, self.available_notebook_cards, self.available_cards_layout, section_widget, self.highlighted_available
        )

        self.log_message(f"Đã di chuyển {moved_count} notebooks vào {section_widget.section_name}")

    def remove_notebooks_from_section(self, section_widget, paths):
        """Trả notebooks từ section về danh sách tổng"""
        moved_count = functions.move_notebooks_from_section(
            paths, section_widget, self.available_cards_layout, self.available_notebook_cards, self._create_card_in_list
        )

        self.log_message(f"Đã trả {moved_count} notebooks từ {section_widget.section_name} về danh sách tổng")

    def close_section(self, section_widget):
        """Đóng một section"""
        section_id = section_widget.section_id
        
        # Trả tất cả notebooks về danh sách tổng
        if section_widget.notebook_cards:
            paths_to_return = list(section_widget.notebook_cards.keys())
            self.remove_notebooks_from_section(section_widget, paths_to_return)
        
        # Lưu kích thước hiện tại và tìm vị trí của section cần xóa
        current_sizes = self.main_splitter.sizes()
        section_index = -1
        for i in range(self.main_splitter.count()):
            if self.main_splitter.widget(i) == section_widget:
                section_index = i
                break
        
        print(f"DEBUG: Close section - Current sizes: {current_sizes}")
        print(f"DEBUG: Close section - Section index: {section_index}")
        
        # Lấy kích thước section sẽ bị xóa để điều chỉnh window
        section_width = 0
        if section_index >= 0 and section_index < len(current_sizes):
            section_width = current_sizes[section_index]
          # Xóa section khỏi splitter trước
        section_widget.cleanup()
        # QSplitter không có removeWidget, cần dùng setParent(None) để xóa
        section_widget.setParent(None)
        section_widget.deleteLater()
        
        if section_id in self.sections:
            del self.sections[section_id]
        
        # Sử dụng QTimer để đảm bảo widget đã bị xóa hoàn toàn trước khi restore sizes
        def restore_sizes():
            # Tạo danh sách sizes mới với notebook list width được fix cứng
            splitter_count = self.main_splitter.count()
            print(f"DEBUG: Close section (delayed) - Splitter count: {splitter_count}")
            
            if splitter_count > 0:
                new_sizes = []
                
                # Xác định vị trí notebook list
                notebook_list_index = 1 if self.console_visible else 0
                
                # Tạo sizes mới
                for i in range(splitter_count):
                    if i == 0 and self.console_visible:
                        # Console column
                        new_sizes.append(config.CONSOLE_DISPLAY_WIDTH)
                    elif i == notebook_list_index:
                        # Notebook list column - luôn fix cứng về kích thước gốc
                        new_sizes.append(self.original_notebook_list_width)
                    else:
                        # Section columns - giữ kích thước hiện tại
                        new_sizes.append(config.SECTION_DISPLAY_WIDTH)
                
                print(f"DEBUG: Close section (delayed) - Setting new sizes: {new_sizes}")
                print(f"DEBUG: Close section (delayed) - Original notebook list width: {self.original_notebook_list_width}")
                
                # Set sizes và force update
                self.main_splitter.setSizes(new_sizes)
                
                # Double-check và force lại nếu cần
                actual_sizes = self.main_splitter.sizes()
                print(f"DEBUG: Close section (delayed) - Actual sizes after first set: {actual_sizes}")
                
                if len(actual_sizes) > notebook_list_index and actual_sizes[notebook_list_index] != self.original_notebook_list_width:
                    print("DEBUG: Close section (delayed) - Notebook list width incorrect, forcing again...")
                    new_sizes[notebook_list_index] = self.original_notebook_list_width
                    self.main_splitter.setSizes(new_sizes)
                    print(f"DEBUG: Close section (delayed) - Final sizes: {self.main_splitter.sizes()}")
        
        # Delay để đảm bảo widget đã bị xóa hoàn toàn
        QTimer.singleShot(50, restore_sizes)  # Tăng delay lên 50ms
        
        # Giảm kích thước window
        if section_width > 0:
            current_width = self.width()
            new_width = current_width - section_width
            self.resize(new_width, self.height())
        
        # Cập nhật minimum size sau khi xóa section
        self._update_window_minimum_size()
        
        self.log_message(f"Đã đóng section: {section_widget.section_name}")

if __name__ == "__main__":
    # Khởi tạo ứng dụng
    app = QApplication(sys.argv)

    # Thiết lập biểu tượng ứng dụng

    functions.setup_application_icon(app)

    # Tạo và hiển thị cửa sổ chính
    window = NotebookRunner()
    
    # --- Căn giữa và di chuyển lệch cửa sổ khi khởi động ---
    try:
        screen = app.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = window.frameGeometry()
            # Căn giữa trước
            window_geometry.moveCenter(screen_geometry.center())
            # Sau đó di chuyển lệch
            final_x = window_geometry.topLeft().x() - 500
            final_y = window_geometry.topLeft().y() - 50
            window.move(final_x, final_y)
    except Exception as e:
        # In ra lỗi nếu có vấn đề, nhưng không làm dừng chương trình
        print(f"Lỗi khi định vị cửa sổ: {e}")

    window.show()

    # Chạy vòng lặp sự kiện
    sys.exit(app.exec())
