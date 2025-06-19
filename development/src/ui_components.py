"""
Module chứa các UI components tùy chỉnh cho ứng dụng NotebookRunner
"""

import os
from PyQt6.QtWidgets import QLabel, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, QWidget, QGroupBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QMouseEvent
import config
import functions


class ClickableLabel(QLabel):
    """Label có thể double-click"""

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


class SectionWidget(QGroupBox):
    """Widget độc lập để quản lý notebooks trong từng section"""

    # Signal để giao tiếp với NotebookRunner
    notebook_add_requested = pyqtSignal(object)  # (SectionWidget)
    notebook_remove_requested = pyqtSignal(object, list)  # (SectionWidget, paths)
    section_close_requested = pyqtSignal(object)  # (SectionWidget)

    def __init__(self, section_name, section_id, parent_runner=None):
        super().__init__(section_name)
        self.section_name = section_name
        self.section_id = section_id
        self.parent_runner = parent_runner

        # Trạng thái độc lập của section
        self.notebook_cards = {}  # Dict chứa các card notebook
        self.highlighted_notebooks = set()  # Set chứa các path notebook đang được chọn
        self.running_threads = {}  # Dict quản lý các thread đang chạy        self.setObjectName("SectionGroup")
        self.setMinimumWidth(config.SECTION_MIN_WIDTH)  # Section min width từ config
        self.setup_ui()

    def setup_ui(self):
        """Thiết lập giao diện cho section"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(8)

        # Scroll area cho danh sách notebooks
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("SectionScrollArea")

        self.cards_widget = QWidget()
        self.cards_widget.setObjectName("CardsContainer")
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cards_layout.setSpacing(6)

        self.scroll_area.setWidget(self.cards_widget)
        layout.addWidget(self.scroll_area)

        # Bộ nút điều khiển
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(6)

        # Hàng đầu: Thêm/Bỏ notebook
        manage_layout = QHBoxLayout()
        self.add_notebook_btn = QPushButton("➕ Thêm Notebook")
        self.add_notebook_btn.setObjectName("RefreshButton")
        self.add_notebook_btn.clicked.connect(self.add_notebooks)

        self.remove_notebook_btn = QPushButton("➖ Bỏ Notebook")
        self.remove_notebook_btn.setObjectName("StopButton")
        self.remove_notebook_btn.clicked.connect(self.remove_notebooks)

        manage_layout.addWidget(self.add_notebook_btn)
        manage_layout.addWidget(self.remove_notebook_btn)

        # Hàng thứ hai: Chạy notebook
        run_layout = QHBoxLayout()
        self.run_all_btn = QPushButton("▶️ Chạy Tất Cả")
        self.run_all_btn.clicked.connect(self.run_all_notebooks)

        self.run_selected_btn = QPushButton("▶️ Chạy Đã Chọn")
        self.run_selected_btn.clicked.connect(self.run_selected_notebooks)

        run_layout.addWidget(self.run_all_btn)
        run_layout.addWidget(self.run_selected_btn)

        # Hàng thứ ba: Dừng notebook
        stop_layout = QHBoxLayout()
        self.stop_selected_btn = QPushButton("⏹️ Dừng Đã Chọn")
        self.stop_selected_btn.setObjectName("StopButton")
        self.stop_selected_btn.clicked.connect(self.stop_selected_notebooks)

        self.stop_all_btn = QPushButton("⏹️ Dừng Tất Cả")
        self.stop_all_btn.setObjectName("StopButton")
        self.stop_all_btn.clicked.connect(self.stop_all_notebooks)

        stop_layout.addWidget(self.stop_selected_btn)
        stop_layout.addWidget(self.stop_all_btn)

        # Hàng cuối: Xóa section
        self.close_section_btn = QPushButton("❌ Xóa Section")
        self.close_section_btn.setObjectName("StopButton")
        self.close_section_btn.clicked.connect(self.close_section)

        controls_layout.addLayout(manage_layout)
        controls_layout.addLayout(run_layout)
        controls_layout.addLayout(stop_layout)
        controls_layout.addWidget(self.close_section_btn)

        layout.addLayout(controls_layout)

    def add_notebook_card(self, path, description):
        """Thêm một notebook card vào section này"""
        if path in self.notebook_cards:
            return  # Notebook đã tồn tại

        card = NotebookCard(path, description)
        card.clicked.connect(self._on_card_click)
        self.cards_layout.addWidget(card)
        self.notebook_cards[path] = card

    def remove_notebook_card(self, path):
        """Xóa một notebook card khỏi section này"""
        if path not in self.notebook_cards:
            return

        card = self.notebook_cards[path]
        self.cards_layout.removeWidget(card)
        card.deleteLater()
        del self.notebook_cards[path]

        if path in self.highlighted_notebooks:
            self.highlighted_notebooks.remove(path)

    def _on_card_click(self, path):
        """Xử lý sự kiện click trên card notebook trong section"""
        functions.handle_card_click(path, self.notebook_cards, self.highlighted_notebooks)

    def add_notebooks(self):
        """Yêu cầu thêm notebooks từ danh sách tổng vào section này"""
        self.notebook_add_requested.emit(self)

    def remove_notebooks(self):
        """Yêu cầu trả notebooks về danh sách tổng"""
        if not self.highlighted_notebooks:
            functions.show_no_notebooks_selected_message(self, "Vui lòng chọn ít nhất một notebook để bỏ.")
            return

        paths_to_remove = list(self.highlighted_notebooks)
        self.notebook_remove_requested.emit(self, paths_to_remove)

    def run_all_notebooks(self):
        """Chạy tất cả notebooks trong section"""
        if not self.notebook_cards:
            functions.show_no_notebooks_selected_message(self, "Không có notebook nào trong section này.")
            return

        if self.parent_runner:
            self.parent_runner.log_message(f"[{self.section_name}] Chạy tất cả {len(self.notebook_cards)} notebooks...")
            for path in self.notebook_cards.keys():
                self.run_notebook(path)

    def run_selected_notebooks(self):
        """Chạy các notebooks đã chọn trong section"""
        if not self.highlighted_notebooks:
            functions.show_no_notebooks_selected_message(self, "Vui lòng chọn ít nhất một notebook để chạy.")
            return

        if self.parent_runner:
            self.parent_runner.log_message(f"[{self.section_name}] Chạy {len(self.highlighted_notebooks)} notebooks đã chọn...")
            for path in list(self.highlighted_notebooks):
                self.run_notebook(path)

    def run_notebook(self, notebook_path):
        """Chạy một notebook trong context của section này"""
        if self.parent_runner:
            # Sử dụng function với section_name để log có prefix
            functions.run_notebook_with_section(notebook_path, self.running_threads, self.parent_runner.output_queue, self.section_name)

    def stop_selected_notebooks(self):
        """Dừng các notebooks đã chọn"""
        if not self.highlighted_notebooks:
            functions.show_no_notebooks_selected_message(self, "Vui lòng chọn ít nhất một notebook để dừng.")
            return

        selected_running = [path for path in self.highlighted_notebooks if path in self.running_threads]
        if not selected_running:
            functions.show_no_running_notebooks_message(self, "Không có notebook đang chạy trong các notebook đã chọn.")
            return

        if self.parent_runner:
            self.parent_runner.log_message(f"[{self.section_name}] Dừng {len(selected_running)} notebooks đã chọn...")

        for path in selected_running:
            if path in self.running_threads:
                del self.running_threads[path]

    def stop_all_notebooks(self):
        """Dừng tất cả notebooks trong section"""
        if not self.running_threads:
            functions.show_no_running_notebooks_message(self, "Không có notebook nào đang chạy trong section này.")
            return

        if self.parent_runner:
            self.parent_runner.log_message(f"[{self.section_name}] Dừng tất cả {len(self.running_threads)} notebooks...")

        self.running_threads.clear()

    def close_section(self):
        """Đóng section này"""
        if not functions.confirm_section_close(self, self.section_name, len(self.notebook_cards)):
            return

        # Dừng tất cả notebooks đang chạy
        if self.running_threads:
            self.stop_all_notebooks()

        # Emit signal để NotebookRunner xử lý cleanup
        self.section_close_requested.emit(self)

    def cleanup(self):
        """Dọn dẹp tài nguyên khi đóng section"""
        # Dừng tất cả threads
        self.running_threads.clear()

        # Trả tất cả notebooks về danh sách tổng
        if self.notebook_cards and self.parent_runner:
            paths_to_return = list(self.notebook_cards.keys())
            self.notebook_remove_requested.emit(self, paths_to_return)
