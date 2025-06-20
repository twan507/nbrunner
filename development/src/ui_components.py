"""
Module chứa các UI components tùy chỉnh cho ứng dụng NotebookRunner
"""

import os
import time
from functools import partial
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
    QSizePolicy,
    QInputDialog,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QTime, QMimeData
from PyQt6.QtGui import QFont, QMouseEvent, QDrag, QDropEvent, QDragEnterEvent
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


class ClickableLink(QLabel):
    """Một QLabel hoạt động như link, phát tín hiệu khi được click."""

    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QLabel { color: #cc0000; }
            QLabel:hover { text-decoration: underline; }
        """)

    def mousePressEvent(self, ev: QMouseEvent | None) -> None:
        self.clicked.emit()
        super().mousePressEvent(ev)


class NotebookCard(QFrame):
    """Widget tùy chỉnh cho mỗi card notebook."""

    clicked = pyqtSignal(str)

    # CHANGED: Thêm parent_runner để truy cập danh sách các item đã chọn
    def __init__(self, path, description, parent_runner, parent=None):
        super().__init__(parent)
        self.path = path
        self.is_highlighted = False
        self.parent_runner = parent_runner  # ADDED: Lưu tham chiếu đến cửa sổ chính
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("Card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
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

    # ADDED: Thêm sự kiện mouseMoveEvent để bắt đầu kéo
    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:
        if not a0:
            return
        # Chỉ bắt đầu kéo nếu nút chuột trái được nhấn và thẻ này đang được chọn
        if a0.buttons() != Qt.MouseButton.LeftButton or not self.is_highlighted:
            return

        drag = QDrag(self)
        mime_data = QMimeData()

        # Lấy tất cả các đường dẫn đã được chọn từ cửa sổ chính
        selected_paths = self.parent_runner.highlighted_available
        if not selected_paths:
            return

        # Đóng gói các đường dẫn vào mime_data, phân tách bằng ký tự xuống dòng
        mime_data.setText('\n'.join(selected_paths))
        drag.setMimeData(mime_data)

        # Tạo một ảnh xem trước của card đang được kéo
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(a0.pos())

        # Bắt đầu hành động kéo
        drag.exec(Qt.DropAction.MoveAction)


    def set_highlighted(self, highlighted):
        self.is_highlighted = highlighted
        self.setObjectName("SelectedCard" if highlighted else "Card")
        style = self.style()
        if style:
            style.unpolish(self)
            style.polish(self)


class SectionNotebookCard(QFrame):
    run_requested = pyqtSignal(str)
    stop_requested = pyqtSignal(str)
    remove_requested = pyqtSignal(str)
    clear_log_requested = pyqtSignal(str)
    execution_finished_signal = pyqtSignal(bool)

    def __init__(self, path, description, parent=None):
        super().__init__(parent)
        self.path, self.description, self.execution_mode, self.execution_count, self.current_status, self.start_time, self.elapsed_time = (
            path,
            description,
            "continuous",
            1,
            "ready",
            None,
            0,
        )
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("SectionCard")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.execution_finished_signal.connect(self.on_execution_finished)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        title_label = QLabel(os.path.basename(self.path))
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        desc_label = QLabel(self.description)
        desc_label.setFont(QFont("Segoe UI", 8))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666666;")
        layout.addWidget(desc_label)
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Phương pháp:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Liên tục", "Số lần"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo)

        self.count_spin = QSpinBox()
        self.count_spin.setStyleSheet("""
                QSpinBox {
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    padding: 3px 0px; 
                    color: black;
                }
            """)
        self.count_spin.setMinimum(1)
        self.count_spin.setMaximum(9)
        self.count_spin.setValue(1)
        self.count_spin.setFixedWidth(30)
        self.count_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.count_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.count_spin.setVisible(False)
        self.count_spin.valueChanged.connect(self.on_count_changed)
        mode_layout.addWidget(self.count_spin)

        layout.addLayout(mode_layout)
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Trạng thái:"))
        self.status_label = QLabel("Sẵn sàng")
        self.status_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #008000;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setFont(QFont("JetBrains Mono", 9))
        status_layout.addWidget(self.timer_label)
        layout.addLayout(status_layout)
        log_layout = QVBoxLayout()
        log_header = QHBoxLayout()
        log_header.addStretch()
        log_layout.addLayout(log_header)
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setObjectName("SectionConsole")
        self.log_console.setFixedHeight(80)
        log_layout.addWidget(self.log_console)
        layout.addLayout(log_layout)
        controls_layout = QHBoxLayout()
        self.run_btn = QPushButton("Chạy")
        self.run_btn.setObjectName("RunButton")
        self.run_btn.clicked.connect(self.run_notebook)
        controls_layout.addWidget(self.run_btn)
        self.stop_btn = QPushButton("Dừng")
        self.stop_btn.setObjectName("StopButton")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_notebook)
        controls_layout.addWidget(self.stop_btn)
        self.clear_log_btn = QPushButton("Xóa")
        self.clear_log_btn.setObjectName("ClearLogButton")
        self.clear_log_btn.clicked.connect(self.clear_log)
        controls_layout.addWidget(self.clear_log_btn)
        self.remove_btn = QPushButton("Đóng")
        self.remove_btn.setObjectName("RemoveButton")
        self.remove_btn.clicked.connect(self.remove_notebook)
        controls_layout.addWidget(self.remove_btn)
        layout.addLayout(controls_layout)
        layout.addStretch()

    def on_mode_changed(self, text):
        self.execution_mode = "count" if text == "Số lần" else "continuous"
        self.count_spin.setVisible(text == "Số lần")

    def on_count_changed(self, value):
        self.execution_count = value

    def run_notebook(self):
        self.set_status("running")
        self.start_timer()
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.run_requested.emit(self.path)

    def stop_notebook(self):
        self.set_status("ready")
        self.stop_timer()
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.stop_requested.emit(self.path)

    def remove_notebook(self):
        if self.current_status == "running":
            self.stop_notebook()
        self.remove_requested.emit(self.path)

    def clear_log(self):
        self.log_console.clear()
        self.clear_log_requested.emit(self.path)

    def set_status(self, status):
        self.current_status = status
        status_map = {
            "ready": ("Sẵn sàng", "#008000"),
            "running": ("Đang chạy", "#FF8C00"),
            "success": ("Thành công", "#008000"),
            "error": ("Lỗi", "#FF0000"),
        }
        if status in status_map:
            text, color = status_map[status]
            self.status_label.setText(text)
            self.status_label.setStyleSheet(f"color: {color};")

    def start_timer(self):
        self.start_time = time.time()
        self.timer.start(10)

    def stop_timer(self):
        self.timer.stop()

    def update_timer(self):
        if self.start_time:
            elapsed = time.time() - self.start_time
            total_ms = int(elapsed * 1000)
            minutes = total_ms // 60000
            seconds = (total_ms % 60000) // 1000
            milliseconds = total_ms % 1000
            self.timer_label.setText(f"{minutes:02d}:{seconds:02d}:{milliseconds // 10:02d}")

    def log_message(self, message):
        self.log_console.append(message)

    def on_execution_finished(self, success=True):
        self.stop_timer()
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.set_status("success" if success else "error")


class SectionWidget(QWidget):
    # REMOVED: notebook_add_requested signal is no longer needed
    # ADDED: notebooks_dropped signal to handle drop events
    notebooks_dropped = pyqtSignal(object, list)
    notebook_remove_requested = pyqtSignal(object, list)
    section_close_requested = pyqtSignal(object)

    def __init__(self, section_name, section_id, parent_runner=None):
        super().__init__()
        self.section_name = section_name
        self.section_id = section_id
        self.parent_runner = parent_runner
        self.notebook_cards = {}
        self.running_threads = {}
        self.schedules = []
        self.schedule_counter = 0
        self.schedule_timer = QTimer()
        self.schedule_timer.timeout.connect(self.check_scheduled_actions)
        self.schedule_timer.start(1000)
        self.setMinimumWidth(config.SECTION_MIN_WIDTH)
        # ADDED: Kích hoạt chức năng nhận drop cho widget này
        self.setAcceptDrops(True)
        self.setup_ui()

    # ADDED: dragEnterEvent để kiểm tra xem dữ liệu kéo vào có hợp lệ không
    def dragEnterEvent(self, a0: QDragEnterEvent | None) -> None:
        if not a0:
            return
        mime_data = a0.mimeData()
        # Chỉ chấp nhận nếu dữ liệu là dạng text (chúng ta đã đóng gói đường dẫn thành text)
        if mime_data and mime_data.hasText():
            a0.acceptProposedAction()
        else:
            a0.ignore()

    # ADDED: dropEvent để xử lý khi người dùng thả notebook vào
    def dropEvent(self, a0: QDropEvent | None) -> None:
        if not a0:
            return
        mime_data = a0.mimeData()
        if mime_data and mime_data.hasText():
            # Lấy dữ liệu text và tách thành danh sách các đường dẫn
            paths = mime_data.text().split('\n')
            # Phát tín hiệu đến cửa sổ chính để xử lý việc di chuyển notebook
            self.notebooks_dropped.emit(self, paths)
            a0.acceptProposedAction()
        else:
            a0.ignore()


    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        notebooks_group = QGroupBox(f"📋 {self.section_name}")
        notebooks_group_layout = QVBoxLayout(notebooks_group)
        notebooks_group_layout.setContentsMargins(5, 10, 5, 5)
        notebooks_group_layout.setSpacing(8)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("SectionScrollArea")
        self.cards_widget = QWidget()
        self.cards_widget.setObjectName("CardsContainer")
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cards_layout.setSpacing(10)
        self.scroll_area.setWidget(self.cards_widget)
        notebooks_group_layout.addWidget(self.scroll_area)
        main_layout.addWidget(notebooks_group, 1)

        schedule_group = QGroupBox("⏰ Tác vụ hẹn giờ")
        schedule_main_layout = QVBoxLayout(schedule_group)
        schedule_main_layout.setContentsMargins(5, 10, 5, 5)
        schedule_main_layout.setSpacing(10)

        add_schedule_layout = QHBoxLayout()
        self.action_combo = QComboBox()
        self.action_combo.addItems(["Chạy đồng thời", "Chạy lần lượt", "Dừng tất cả"])
        self.action_combo.setFont(QFont("Segoe UI", 9))
        add_schedule_layout.addWidget(self.action_combo, 1)
        add_schedule_layout.addSpacing(5)
        self.schedule_time_edit = QTimeEdit()
        self.schedule_time_edit.setDisplayFormat("HH:mm")
        self.schedule_time_edit.setTime(QTime.currentTime().addSecs(60))
        self.schedule_time_edit.setFont(QFont("Segoe UI", 9))
        self.schedule_time_edit.setButtonSymbols(QTimeEdit.ButtonSymbols.NoButtons)
        self.schedule_time_edit.setFixedWidth(65)
        self.schedule_time_edit.setStyleSheet("""
            QTimeEdit {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 3px 5px;
                color: black;
            }
        """)
        add_schedule_layout.addWidget(self.schedule_time_edit)
        self.add_schedule_btn = QPushButton("Thêm")
        self.add_schedule_btn.setObjectName("SetScheduleButton")
        self.add_schedule_btn.clicked.connect(self.add_schedule)
        add_schedule_layout.addWidget(self.add_schedule_btn)
        schedule_main_layout.addLayout(add_schedule_layout)

        scroll_schedules = QScrollArea()
        scroll_schedules.setWidgetResizable(True)
        scroll_schedules.setStyleSheet("QScrollArea { border: 1px solid #dee2e6; border-radius: 4px; }")
        scroll_schedules.setFixedHeight(60)
        self.schedule_list_widget = QWidget()
        self.schedule_list_widget.setObjectName("ScheduleListContainer")
        self.schedule_list_widget.setStyleSheet("QWidget#ScheduleListContainer { background-color: white; }")
        self.schedule_list_layout = QVBoxLayout(self.schedule_list_widget)
        self.schedule_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.schedule_list_layout.setContentsMargins(5, 5, 5, 5)
        self.schedule_list_layout.setSpacing(5)
        scroll_schedules.setWidget(self.schedule_list_widget)
        schedule_main_layout.addWidget(scroll_schedules)
        main_layout.addWidget(schedule_group, 0)

        controls_group = QGroupBox("⚙️ Điều khiển chung")
        controls_group.setObjectName("SectionControlsGroup")
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setContentsMargins(5, 10, 5, 5)
        controls_layout.setSpacing(8)

        run_buttons_layout = QHBoxLayout()
        self.run_all_btn = QPushButton("Chạy đồng thời")
        self.run_all_btn.setObjectName("SectionRunButton")
        self.run_all_btn.clicked.connect(self.run_all_simultaneously)
        run_buttons_layout.addWidget(self.run_all_btn)
        self.run_sequential_btn = QPushButton("Chạy lần lượt")
        self.run_sequential_btn.setObjectName("SectionRunButton")
        self.run_sequential_btn.clicked.connect(self.run_all_sequential)
        run_buttons_layout.addWidget(self.run_sequential_btn)
        controls_layout.addLayout(run_buttons_layout)

        stop_close_layout = QHBoxLayout()
        self.close_section_btn = QPushButton("Đóng Section")
        self.close_section_btn.setObjectName("SectionRemoveButton")
        self.close_section_btn.clicked.connect(self.close_section)
        stop_close_layout.addWidget(self.close_section_btn)
        self.stop_all_btn = QPushButton("Dừng tất cả")
        self.stop_all_btn.setObjectName("SectionStopButton")
        self.stop_all_btn.clicked.connect(self.stop_all_notebooks)
        stop_close_layout.addWidget(self.stop_all_btn)
        controls_layout.addLayout(stop_close_layout)

        main_layout.addWidget(controls_group, 0)
        
        self.update_schedule_display()

    def add_schedule(self):
        self.schedule_counter += 1
        schedule_id = self.schedule_counter
        action_text = self.action_combo.currentText()
        schedule_time = self.schedule_time_edit.time()
        action_map = {"Chạy đồng thời": "run_all_simultaneously", "Chạy lần lượt": "run_all_sequential", "Dừng tất cả": "stop_all_notebooks"}
        action_key = action_map.get(action_text)
        new_schedule = {"id": schedule_id, "action_key": action_key, "action_text": action_text, "time": schedule_time}
        self.schedules.append(new_schedule)
        self.update_schedule_display()
        if self.parent_runner:
            self.parent_runner.log_message(f"[{self.section_name}] Đã thêm lịch hẹn: '{action_text}' lúc {schedule_time.toString('HH:mm')}")

    def remove_schedule(self, schedule_id):
        self.schedules = [s for s in self.schedules if s["id"] != schedule_id]
        self.update_schedule_display()

    def update_schedule_display(self):
        while self.schedule_list_layout.count():
            item = self.schedule_list_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        if not self.schedules:
            placeholder = QLabel("Chưa có lịch hẹn nào.")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #888;")
            self.schedule_list_layout.addWidget(placeholder)
            return

        for schedule in self.schedules:
            item_frame = QFrame()
            item_layout = QHBoxLayout(item_frame)
            item_layout.setContentsMargins(8, 2, 8, 2)

            label = QLabel(f"<b>{schedule['action_text']}</b> {schedule['time'].toString('HH:mm')}")
            item_layout.addWidget(label)
            item_layout.addStretch()

            remove_label = ClickableLink("Xóa")
            remove_label.clicked.connect(partial(self.remove_schedule, schedule["id"]))

            item_layout.addWidget(remove_label)
            self.schedule_list_layout.addWidget(item_frame)

    def check_scheduled_actions(self):
        now_str = QTime.currentTime().toString("HH:mm")
        executed_ids = []
        for schedule in self.schedules:
            if schedule["time"].toString("HH:mm") == now_str:
                action_method_name = schedule["action_key"]
                if hasattr(self, action_method_name):
                    getattr(self, action_method_name)()
                if self.parent_runner:
                    self.parent_runner.log_message(f"[{self.section_name}] Thực thi hẹn giờ: {schedule['action_text']}")
                executed_ids.append(schedule["id"])
        if executed_ids:
            self.schedules = [s for s in self.schedules if s["id"] not in executed_ids]
            self.update_schedule_display()

    def add_notebook_card(self, path, description):
        if path in self.notebook_cards:
            return
        card = SectionNotebookCard(path, description)
        card.run_requested.connect(self.on_card_run_requested)
        card.stop_requested.connect(self.on_card_stop_requested)
        card.remove_requested.connect(self.on_card_remove_requested)
        card.clear_log_requested.connect(self.on_card_clear_log_requested)
        self.cards_layout.addWidget(card)
        self.notebook_cards[path] = card

    def remove_notebook_card(self, path):
        if path in self.notebook_cards:
            card = self.notebook_cards.pop(path)
            card.deleteLater()
        if path in self.running_threads:
            del self.running_threads[path]

    def on_card_run_requested(self, path):
        self.run_notebook(path)

    def on_card_stop_requested(self, path):
        if self.parent_runner:
            self.parent_runner.log_message(f"[{self.section_name}] Dừng: {os.path.basename(path)}")
        if path in self.running_threads:
            del self.running_threads[path]

    def on_card_remove_requested(self, path):
        self.notebook_remove_requested.emit(self, [path])

    def on_card_clear_log_requested(self, path):
        pass

    def run_all_simultaneously(self):
        if self.notebook_cards:
            if self.parent_runner:
                self.parent_runner.log_message(f"[{self.section_name}] Chạy đồng thời...")
            [c.run_notebook() for c in self.notebook_cards.values()]

    def run_all_sequential(self):
        if self.notebook_cards:
            if self.parent_runner:
                self.parent_runner.log_message(f"[{self.section_name}] Chạy lần lượt...")
            [c.run_notebook() for c in self.notebook_cards.values()]

    def run_notebook(self, notebook_path):
        if self.parent_runner:
            card = self.notebook_cards.get(notebook_path)
            functions.run_notebook_with_individual_logging(notebook_path, self.running_threads, card, self.section_name)

    def stop_all_notebooks(self):
        if any(c.current_status == "running" for c in self.notebook_cards.values()):
            if self.parent_runner:
                self.parent_runner.log_message(f"[{self.section_name}] Dừng tất cả...")
            [c.stop_notebook() for c in self.notebook_cards.values() if c.current_status == "running"]
            self.running_threads.clear()

    def close_section(self):
        if functions.confirm_section_close(self, self.section_name, len(self.notebook_cards)):
            if any(c.current_status == "running" for c in self.notebook_cards.values()):
                self.stop_all_notebooks()
            self.section_close_requested.emit(self)

    def cleanup(self):
        if hasattr(self, "schedule_timer"):
            self.schedule_timer.stop()
        self.running_threads.clear()
        [c.stop_notebook() for c in self.notebook_cards.values() if c.current_status == "running"]
        if self.notebook_cards and self.parent_runner:
            self.notebook_remove_requested.emit(self, list(self.notebook_cards.keys()))