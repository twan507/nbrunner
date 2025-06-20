"""
Module chứa các UI components tùy chỉnh cho ứng dụng NotebookRunner
"""

import os
import time
from PyQt6.QtWidgets import (
    QLabel,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QWidget,
    QGroupBox,
    QComboBox,
    QSpinBox,
    QTextEdit,
    QTimeEdit,
    QCheckBox,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QTime
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


class SectionNotebookCard(QFrame):
    """Widget chi tiết cho notebook trong section với đầy đủ chức năng điều khiển"""

    # Signals
    run_requested = pyqtSignal(str)  # (notebook_path)
    stop_requested = pyqtSignal(str)  # (notebook_path)
    remove_requested = pyqtSignal(str)  # (notebook_path)
    clear_log_requested = pyqtSignal(str)  # (notebook_path)

    def __init__(self, path, description, parent=None):
        super().__init__(parent)
        self.path = path
        self.description = description
        self.execution_mode = "continuous"  # "continuous" or "count"
        self.execution_count = 1
        self.current_status = "ready"  # "ready", "running", "success", "error"
        self.start_time = None
        self.elapsed_time = 0

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("SectionCard")

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # Timer để cập nhật đồng hồ
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        self.setup_ui()

    def setup_ui(self):
        """Thiết lập giao diện card"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Tiêu đề notebook
        title_label = QLabel(os.path.basename(self.path))
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Mô tả
        desc_label = QLabel(self.description)
        desc_label.setFont(QFont("Segoe UI", 8))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666666;")
        layout.addWidget(desc_label)

        # Phương pháp chạy
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Phương pháp:"))

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Liên tục", "Số lần"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)

        self.count_spin = QSpinBox()
        self.count_spin.setMinimum(1)
        self.count_spin.setMaximum(999)
        self.count_spin.setValue(1)
        self.count_spin.setVisible(False)
        self.count_spin.valueChanged.connect(self.on_count_changed)
        mode_layout.addWidget(self.count_spin)

        layout.addLayout(mode_layout)

        # Trạng thái và thời gian
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Trạng thái:"))

        self.status_label = QLabel("Sẵn sàng")
        self.status_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #008000;")  # Green
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.timer_label = QLabel("00:00:00")
        self.timer_label.setFont(QFont("JetBrains Mono", 9))
        status_layout.addWidget(self.timer_label)

        layout.addLayout(status_layout)

        # Nút điều khiển
        controls_layout = QHBoxLayout()

        self.run_btn = QPushButton("▶️ Chạy")
        self.run_btn.setObjectName("RunButton")
        self.run_btn.clicked.connect(self.run_notebook)
        controls_layout.addWidget(self.run_btn)

        self.stop_btn = QPushButton("⏹️ Dừng")
        self.stop_btn.setObjectName("StopButton")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_notebook)
        controls_layout.addWidget(self.stop_btn)

        self.remove_btn = QPushButton("🗑️ Xóa")
        self.remove_btn.setObjectName("RemoveButton")
        self.remove_btn.clicked.connect(self.remove_notebook)
        controls_layout.addWidget(self.remove_btn)

        self.clear_log_btn = QPushButton("🗑️ Xóa log")
        self.clear_log_btn.setObjectName("ClearLogButton")
        self.clear_log_btn.clicked.connect(self.clear_log)
        controls_layout.addWidget(self.clear_log_btn)

        layout.addLayout(controls_layout)

        # Console log riêng
        log_layout = QVBoxLayout()
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("Log:"))
        log_header.addStretch()

        log_layout.addLayout(log_header)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setFont(QFont("JetBrains Mono", 8))
        self.log_console.setMaximumHeight(120)
        self.log_console.setMinimumHeight(80)
        self.log_console.setObjectName("SectionConsole")
        log_layout.addWidget(self.log_console)

        layout.addLayout(log_layout)

        # THÊM DÒNG NÀY
        layout.addStretch() 

    def on_mode_changed(self, text):
        """Xử lý thay đổi phương pháp chạy"""
        if text == "Số lần":
            self.execution_mode = "count"
            self.count_spin.setVisible(True)
        else:
            self.execution_mode = "continuous"
            self.count_spin.setVisible(False)

    def on_count_changed(self, value):
        """Xử lý thay đổi số lần chạy"""
        self.execution_count = value

    def run_notebook(self):
        """Chạy notebook"""
        self.set_status("running")
        self.start_timer()
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.run_requested.emit(self.path)

    def stop_notebook(self):
        """Dừng notebook"""
        self.set_status("ready")
        self.stop_timer()
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.stop_requested.emit(self.path)

    def remove_notebook(self):
        """Xóa notebook khỏi section"""
        if self.current_status == "running":
            self.stop_notebook()
        self.remove_requested.emit(self.path)

    def clear_log(self):
        """Xóa log riêng"""
        self.log_console.clear()
        self.clear_log_requested.emit(self.path)

    def set_status(self, status):
        """Cập nhật trạng thái"""
        self.current_status = status
        status_map = {
            "ready": ("Sẵn sàng", "#008000"),  # Green
            "running": ("Đang chạy", "#FF8C00"),  # Orange
            "success": ("Thành công", "#008000"),  # Green
            "error": ("Lỗi", "#FF0000"),  # Red
        }

        if status in status_map:
            text, color = status_map[status]
            self.status_label.setText(text)
            self.status_label.setStyleSheet(f"color: {color};")

    def start_timer(self):
        """Bắt đầu đồng hồ"""
        self.start_time = time.time()
        self.timer.start(1000)  # Cập nhật mỗi giây

    def stop_timer(self):
        """Dừng đồng hồ"""
        self.timer.stop()

    def reset_timer(self):
        """Reset đồng hồ"""
        self.elapsed_time = 0
        self.timer_label.setText("00:00:00")

    def update_timer(self):
        """Cập nhật hiển thị thời gian"""
        if self.start_time:
            self.elapsed_time = int(time.time() - self.start_time)
            hours = self.elapsed_time // 3600
            minutes = (self.elapsed_time % 3600) // 60
            seconds = self.elapsed_time % 60
            self.timer_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def log_message(self, message):
        """Thêm message vào log riêng"""
        self.log_console.append(message)

    def on_execution_finished(self, success=True):
        """Xử lý khi execution kết thúc"""
        self.stop_timer()
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if success:
            self.set_status("success")
        else:
            self.set_status("error")


class SectionWidget(QGroupBox):
    """Widget độc lập để quản lý notebooks trong từng section với chức năng mở rộng"""

    # Signal để giao tiếp với NotebookRunner
    notebook_add_requested = pyqtSignal(object)  # (SectionWidget)
    notebook_remove_requested = pyqtSignal(object, list)  # (SectionWidget, paths)
    section_close_requested = pyqtSignal(object)  # (SectionWidget)

    def __init__(self, section_name, section_id, parent_runner=None):
        super().__init__(section_name)
        self.section_name = section_name
        self.section_id = section_id
        self.parent_runner = parent_runner

        self.notebook_cards = {}  # Dict chứa các SectionNotebookCard
        self.running_threads = {}  # Dict quản lý các thread đang chạy

        # Cài đặt hẹn giờ
        self.scheduled_run = False
        self.scheduled_stop = False
        self.run_time = None
        self.stop_time = None

        # Timer cho scheduled execution
        self.schedule_timer = QTimer()
        self.schedule_timer.timeout.connect(self.check_scheduled_actions)
        self.schedule_timer.start(1000)  # Check mỗi giây        self.setObjectName("SectionGroup")
        self.setMinimumWidth(config.SECTION_MIN_WIDTH)  # Section min width từ config
        self.setup_ui()

    def setup_ui(self):
        """Thiết lập giao diện cho section mới"""
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
        self.cards_layout.setSpacing(10)

        self.scroll_area.setWidget(self.cards_widget)
        layout.addWidget(self.scroll_area)

        # Khu vực điều khiển section (tách riêng giống cột notebooks)
        controls_frame = QFrame()
        controls_frame.setObjectName("SectionControlsFrame")
        controls_frame.setFrameShape(QFrame.Shape.StyledPanel)

        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(8, 8, 8, 8)
        controls_layout.setSpacing(8)  # Hàng 1: Thêm notebook
        manage_layout = QHBoxLayout()
        self.add_notebook_btn = QPushButton("➕ Thêm Notebook")
        self.add_notebook_btn.setObjectName("SectionControlButton")
        self.add_notebook_btn.clicked.connect(self.add_notebooks)
        manage_layout.addWidget(self.add_notebook_btn)

        # Hàng 2: Cài đặt hẹn giờ
        schedule_layout = QVBoxLayout()

        self.schedule_checkbox = QCheckBox("Hẹn giờ thực hiện")
        self.schedule_checkbox.stateChanged.connect(self.on_schedule_toggled)
        schedule_layout.addWidget(self.schedule_checkbox)

        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Chạy lúc:"))
        self.run_time_edit = QTimeEdit()
        self.run_time_edit.setEnabled(False)
        self.run_time_edit.setTime(QTime.currentTime())
        time_layout.addWidget(self.run_time_edit)

        time_layout.addWidget(QLabel("Dừng lúc:"))
        self.stop_time_edit = QTimeEdit()
        self.stop_time_edit.setEnabled(False)
        self.stop_time_edit.setTime(QTime.currentTime().addSecs(3600))  # +1 giờ
        time_layout.addWidget(self.stop_time_edit)

        schedule_layout.addLayout(time_layout)

        # Hàng 3: Chạy và dừng tất cả
        run_layout = QHBoxLayout()
        self.run_all_btn = QPushButton("▶️ Chạy cùng lúc")
        self.run_all_btn.setObjectName("SectionRunButton")
        self.run_all_btn.clicked.connect(self.run_all_simultaneously)
        run_layout.addWidget(self.run_all_btn)

        self.run_sequential_btn = QPushButton("▶️ Chạy lần lượt")
        self.run_sequential_btn.setObjectName("SectionRunButton")
        self.run_sequential_btn.clicked.connect(self.run_all_sequential)
        run_layout.addWidget(self.run_sequential_btn)

        # Hàng 4: Dừng và xóa
        stop_layout = QHBoxLayout()
        self.stop_all_btn = QPushButton("⏹️ Dừng tất cả")
        self.stop_all_btn.setObjectName("SectionStopButton")
        self.stop_all_btn.clicked.connect(self.stop_all_notebooks)
        stop_layout.addWidget(self.stop_all_btn)

        self.clear_all_logs_btn = QPushButton("🗑️ Xóa log")
        self.clear_all_logs_btn.setObjectName("SectionClearButton")
        self.clear_all_logs_btn.clicked.connect(self.clear_all_logs)
        stop_layout.addWidget(self.clear_all_logs_btn)

        # Hàng 5: Xóa section
        self.close_section_btn = QPushButton("❌ Xóa Section")
        self.close_section_btn.setObjectName("SectionRemoveButton")
        self.close_section_btn.clicked.connect(self.close_section)

        # Thêm tất cả vào controls layout
        controls_layout.addLayout(manage_layout)
        controls_layout.addLayout(schedule_layout)
        controls_layout.addLayout(run_layout)
        controls_layout.addLayout(stop_layout)
        controls_layout.addWidget(self.close_section_btn)

        # Thêm controls frame vào layout chính
        layout.addWidget(controls_frame)

    def on_schedule_toggled(self, checked):
        """Xử lý bật/tắt hẹn giờ"""
        self.scheduled_run = checked
        self.scheduled_stop = checked
        self.run_time_edit.setEnabled(checked)
        self.stop_time_edit.setEnabled(checked)

    def check_scheduled_actions(self):
        """Kiểm tra và thực hiện các hành động đã hẹn giờ"""
        if not (self.scheduled_run or self.scheduled_stop):
            return

        current_time = QTime.currentTime()

        # Kiểm tra thời gian chạy
        if self.scheduled_run and self.run_time_edit.time() == current_time:
            self.run_all_simultaneously()

        # Kiểm tra thời gian dừng
        if self.scheduled_stop and self.stop_time_edit.time() == current_time:
            self.stop_all_notebooks()

    def add_notebook_card(self, path, description):
        """Thêm một notebook card vào section này sử dụng SectionNotebookCard"""
        if path in self.notebook_cards:
            return  # Notebook đã tồn tại

        card = SectionNotebookCard(path, description)
        # Connect signals từ card
        card.run_requested.connect(self.on_card_run_requested)
        card.stop_requested.connect(self.on_card_stop_requested)
        card.remove_requested.connect(self.on_card_remove_requested)
        card.clear_log_requested.connect(self.on_card_clear_log_requested)

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

        # Dừng thread nếu đang chạy
        if path in self.running_threads:
            del self.running_threads[path]

    def on_card_run_requested(self, path):
        """Xử lý khi card yêu cầu chạy"""
        if self.parent_runner:
            self.parent_runner.log_message(f"[{self.section_name}] Chạy notebook: {os.path.basename(path)}")
            self.run_notebook(path)

    def on_card_stop_requested(self, path):
        """Xử lý khi card yêu cầu dừng"""
        if self.parent_runner:
            self.parent_runner.log_message(f"[{self.section_name}] Dừng notebook: {os.path.basename(path)}")
            if path in self.running_threads:
                del self.running_threads[path]

    def on_card_remove_requested(self, path):
        """Xử lý khi card yêu cầu xóa"""
        paths_to_remove = [path]
        self.notebook_remove_requested.emit(self, paths_to_remove)

    def on_card_clear_log_requested(self, path):
        """Xử lý khi card yêu cầu xóa log"""
        if self.parent_runner:
            self.parent_runner.log_message(f"[{self.section_name}] Xóa log của: {os.path.basename(path)}")

    def add_notebooks(self):
        """Yêu cầu thêm notebooks từ danh sách tổng vào section này"""
        self.notebook_add_requested.emit(self)

    def run_all_simultaneously(self):
        """Chạy cùng lúc tất cả notebooks trong section"""
        if not self.notebook_cards:
            functions.show_no_notebooks_selected_message(self, "Không có notebook nào trong section này.")
            return

        if self.parent_runner:
            self.parent_runner.log_message(f"[{self.section_name}] Chạy cùng lúc tất cả {len(self.notebook_cards)} notebooks...")
            for path, card in self.notebook_cards.items():
                card.run_notebook()

    def run_all_sequential(self):
        """Chạy lần lượt tất cả notebooks trong section"""
        if not self.notebook_cards:
            functions.show_no_notebooks_selected_message(self, "Không có notebook nào trong section này.")
            return

        if self.parent_runner:
            self.parent_runner.log_message(
                f"[{self.section_name}] Chạy lần lượt tất cả {len(self.notebook_cards)} notebooks..."
            )  # TODO: Implement sequential execution logic
            for path, card in self.notebook_cards.items():
                card.run_notebook()

    def run_notebook(self, notebook_path):
        """Chạy một notebook trong context của section này"""
        if self.parent_runner:
            # Sử dụng function với individual logging để cập nhật trạng thái card
            section_card = self.notebook_cards.get(notebook_path)
            functions.run_notebook_with_individual_logging(notebook_path, self.running_threads, section_card, self.section_name)

    def stop_all_notebooks(self):
        """Dừng tất cả notebooks trong section"""
        if not self.running_threads and not any(card.current_status == "running" for card in self.notebook_cards.values()):
            functions.show_no_running_notebooks_message(self, "Không có notebook nào đang chạy trong section này.")
            return

        if self.parent_runner:
            self.parent_runner.log_message(f"[{self.section_name}] Dừng tất cả notebooks...")

        # Dừng tất cả cards
        for card in self.notebook_cards.values():
            if card.current_status == "running":
                card.stop_notebook()

        self.running_threads.clear()

    def clear_all_logs(self):
        """Xóa log của tất cả notebooks trong section"""
        if not self.notebook_cards:
            return

        for card in self.notebook_cards.values():
            card.clear_log()

        if self.parent_runner:
            self.parent_runner.log_message(f"[{self.section_name}] Đã xóa log của tất cả notebooks")

    def close_section(self):
        """Đóng section này"""
        if not functions.confirm_section_close(self, self.section_name, len(self.notebook_cards)):
            return

        # Dừng tất cả notebooks đang chạy
        if self.running_threads or any(card.current_status == "running" for card in self.notebook_cards.values()):
            self.stop_all_notebooks()

        # Emit signal để NotebookRunner xử lý cleanup
        self.section_close_requested.emit(self)

    def cleanup(self):
        """Dọn dẹp tài nguyên khi đóng section"""
        # Dừng timer
        if hasattr(self, "schedule_timer"):
            self.schedule_timer.stop()

        # Dừng tất cả threads
        self.running_threads.clear()

        # Dừng tất cả cards
        for card in self.notebook_cards.values():
            if card.current_status == "running":
                card.stop_notebook()

        # Trả tất cả notebooks về danh sách tổng
        if self.notebook_cards and self.parent_runner:
            paths_to_return = list(self.notebook_cards.keys())
            self.notebook_remove_requested.emit(self, paths_to_return)
