"""
Module chứa các UI components tùy chỉnh cho ứng dụng NotebookRunner
"""

import os
import time
import threading
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
    QMessageBox,
    QApplication,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QTime, QMimeData, QPoint, QRect

# MODIFIED: Thêm các import cần thiết cho việc vẽ ảnh động
from PyQt6.QtGui import (
    QFont,
    QMouseEvent,
    QDrag,
    QDropEvent,
    QDragEnterEvent,
    QPixmap,
    QPainter,
    QColor,
    QBrush,
    QPen,
)
import config
import functions


class ClickableLabel(QLabel):
    doubleClicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mouseDoubleClickEvent(self, a0: QMouseEvent | None) -> None:
        if not a0:
            return
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(a0)


class ClickableLink(QLabel):
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("QLabel { color: #cc0000; } QLabel:hover { text-decoration: underline; }")

    def mousePressEvent(self, ev: QMouseEvent | None) -> None:
        if not ev:
            return
        self.clicked.emit()
        super().mousePressEvent(ev)


class NotebookCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, path, description, parent_runner, parent=None):
        super().__init__(parent)
        self.path, self.is_highlighted, self.parent_runner = path, False, parent_runner
        self.press_pos: QPoint | None = None
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
        if not a0:
            return
        self.press_pos = a0.pos()
        self.clicked.emit(self.path)

    def create_transparent_drag_pixmap(self):
        """
        Hàm hỗ trợ: Tạo ảnh của MỘT card với nền trong suốt.
        """
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.transparent)

        original_autofill = self.autoFillBackground()
        self.setAutoFillBackground(False)

        # Sử dụng cờ DrawChildren để vẽ viền và chữ, bỏ qua nền
        self.render(pixmap, flags=QWidget.RenderFlag.DrawChildren)

        self.setAutoFillBackground(original_autofill)
        return pixmap

    def create_stacked_pixmap(self, selected_paths):
        """
        MODIFIED: Xóa bỏ hoàn toàn lớp phủ tối màu cho các card bên dưới.
        """
        all_cards = self.parent_runner.available_notebook_cards
        selected_cards = [all_cards[p] for p in selected_paths if p in all_cards]

        if not selected_cards:
            return self.create_transparent_drag_pixmap()

        max_cards_to_show = 4
        offset_x, offset_y = 8, 8

        base_size = selected_cards[0].size()
        card_width, card_height = base_size.width(), base_size.height()

        num_cards_in_stack = min(len(selected_cards), max_cards_to_show)

        total_width = card_width + (offset_x * (num_cards_in_stack - 1))
        total_height = card_height + (offset_y * (num_cards_in_stack - 1))

        final_pixmap = QPixmap(total_width, total_height)
        final_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(final_pixmap)
        
        for i in range(num_cards_in_stack):
            index = num_cards_in_stack - 1 - i
            card_to_draw = selected_cards[index]
            
            card_pixmap = card_to_draw.create_transparent_drag_pixmap()

            # Khối lệnh if dùng để vẽ lớp phủ đã được XÓA BỎ tại đây.
            
            painter.drawPixmap(offset_x * index, offset_y * index, card_pixmap)

        # Phần vẽ huy hiệu đếm số không thay đổi
        if len(selected_cards) > max_cards_to_show:
            badge_size = 22
            badge_rect = QRect(total_width - badge_size - 2, 2, badge_size, badge_size)
            
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QBrush(QColor("#0d6efd")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(badge_rect)
            
            painter.setPen(QPen(Qt.GlobalColor.white))
            font = QFont("Segoe UI", 8, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, f"+{len(selected_cards) - max_cards_to_show + 1}")

        painter.end()
        return final_pixmap

    def mouseMoveEvent(self, a0: QMouseEvent | None) -> None:
        """
        MODIFIED: Phục hồi logic chọn giữa ảnh đơn và ảnh xếp chồng.
        """
        if not a0 or a0.buttons() != Qt.MouseButton.LeftButton or not self.is_highlighted:
            return

        selected_paths = self.parent_runner.highlighted_available
        if not selected_paths:
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText("\n".join(selected_paths))
        drag.setMimeData(mime_data)

        # Quyết định dùng ảnh nào dựa trên số lượng lựa chọn
        if len(selected_paths) <= 1:
            # Nếu chỉ chọn 1, dùng ảnh trong suốt của card đó
            pixmap = self.create_transparent_drag_pixmap()
        else:
            # Nếu chọn nhiều, dùng ảnh xếp chồng trong suốt
            pixmap = self.create_stacked_pixmap(selected_paths)

        drag.setPixmap(pixmap)
        drag.setHotSpot(a0.pos())
        drag.exec(Qt.DropAction.MoveAction)

    def mouseReleaseEvent(self, a0: QMouseEvent | None) -> None:
        if not a0 or self.press_pos is None:
            return

        moved_distance = (a0.pos() - self.press_pos).manhattanLength()
        if moved_distance >= QApplication.startDragDistance():
            return

        is_ctrl_pressed = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier)

        if not is_ctrl_pressed and self.is_highlighted and len(self.parent_runner.highlighted_available) > 1:
            other_selected_paths = list(self.parent_runner.highlighted_available)
            for p in other_selected_paths:
                if p != self.path and p in self.parent_runner.available_notebook_cards:
                    self.parent_runner.available_notebook_cards[p].set_highlighted(False)

            self.parent_runner.highlighted_available.clear()
            self.parent_runner.highlighted_available.append(self.path)

    def set_highlighted(self, highlighted):
        self.is_highlighted = highlighted
        self.setObjectName("SelectedCard" if highlighted else "Card")
        style = self.style()
        if style:
            style.unpolish(self)
            style.polish(self)


# ======================================================================
# CÁC CLASS KHÁC (SectionNotebookCard, SectionWidget) KHÔNG THAY ĐỔI
# ======================================================================


class SectionNotebookCard(QFrame):
    run_requested = pyqtSignal(object)
    stop_requested = pyqtSignal(str)
    remove_requested = pyqtSignal(str)
    clear_log_requested = pyqtSignal(str)

    def __init__(self, path, description, parent=None):
        super().__init__(parent)
        self.path, self.description = path, description
        self.execution_mode, self.execution_count, self.execution_delay, self.current_status, self.start_time = (
            "continuous",
            1,
            0,
            "ready",
            None,
        )
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setObjectName("SectionCard")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.timeout.connect(self.update_elapsed_timer)
        self.log_queue_timer = QTimer(self)
        self.log_queue = None
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
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Chạy liên tục", "Chạy hữu hạn"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo, 1)

        self.delay_label = QLabel("Nghỉ (s):")
        self.delay_spin = QSpinBox()
        self.delay_spin.setStyleSheet(
            "QSpinBox{background-color:#f0f0f0;border:1px solid #ccc;border-radius:4px;padding:3px 0px;color:black;}"
        )
        self.delay_spin.setMinimum(0)
        self.delay_spin.setMaximum(999)
        self.delay_spin.setValue(0)
        self.delay_spin.setFixedWidth(40)
        self.delay_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.delay_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.delay_spin.valueChanged.connect(self.on_delay_changed)
        mode_layout.addWidget(self.delay_label)
        mode_layout.addWidget(self.delay_spin)

        self.count_label = QLabel("Số lần:")
        self.count_spin = QSpinBox()
        self.count_spin.setStyleSheet(
            "QSpinBox{background-color:#f0f0f0;border:1px solid #ccc;border-radius:4px;padding:3px 0px;color:black;}"
        )
        self.count_spin.setMinimum(1)
        self.count_spin.setMaximum(99)
        self.count_spin.setValue(1)
        self.count_spin.setFixedWidth(40)
        self.count_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.count_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setVisible(False)
        self.count_spin.setVisible(False)
        self.count_spin.valueChanged.connect(self.on_count_changed)
        mode_layout.addWidget(self.count_label)
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
        self.clear_log_btn = QPushButton("Xóa Log")
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
        is_count_mode = text == "Chạy hữu hạn"
        self.execution_mode = "count" if is_count_mode else "continuous"
        self.count_label.setVisible(is_count_mode)
        self.count_spin.setVisible(is_count_mode)
        self.delay_label.setVisible(not is_count_mode)
        self.delay_spin.setVisible(not is_count_mode)

    def on_count_changed(self, value):
        self.execution_count = value

    def on_delay_changed(self, value):
        self.execution_delay = value

    def run_notebook(self):
        self.set_status("running")
        self.start_elapsed_timer()
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.mode_combo.setEnabled(False)
        self.count_spin.setEnabled(False)
        self.delay_spin.setEnabled(False)
        self.run_requested.emit(self)

    def stop_notebook(self):
        self.set_status("stopping")
        self.stop_btn.setEnabled(False)
        self.stop_log_listener()
        self.stop_requested.emit(self.path)

    def remove_notebook(self):
        if self.current_status == "running":
            self.stop_notebook()
        self.remove_requested.emit(self.path)

    def clear_log(self):
        self.log_console.clear()
        self.clear_log_requested.emit(self.path)

    def on_execution_finished(self, success):
        self.set_status("success" if success else "error")
        self.stop_elapsed_timer()
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.mode_combo.setEnabled(True)
        self.count_spin.setEnabled(True)
        self.delay_spin.setEnabled(True)
        self.stop_log_listener()

    def set_status(self, status, message=None):
        self.current_status = status
        status_map = {
            "ready": ("Sẵn sàng", "#008000"),
            "running": ("Đang chạy", "#FF8C00"),
            "success": ("Thành công", "#008000"),
            "error": ("Lỗi", "#FF0000"),
            "stopping": ("Đang dừng...", "#fd7e14"),
            "stopped": ("Đã dừng", "#6c757d"),
            "waiting": ("Đang chờ...", "#007bff"),
        }
        if status in status_map:
            text, color = status_map[status]
            final_text = f"{text}: {message}" if message else text
            self.status_label.setText(final_text)
            self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def start_elapsed_timer(self):
        self.start_time = time.time()
        self.elapsed_timer.start(10)

    def stop_elapsed_timer(self):
        self.elapsed_timer.stop()

    def update_elapsed_timer(self):
        if self.start_time:
            elapsed = time.time() - self.start_time
            total_ms = int(elapsed * 1000)
            minutes = total_ms // 60000
            seconds = (total_ms % 60000) // 1000
            hundredths = (total_ms % 1000) // 10
            self.timer_label.setText(f"{minutes:02d}:{seconds:02d}:{hundredths:02d}")

    def start_log_listener(self, queue):
        self.log_queue = queue
        self.log_queue_timer.timeout.connect(self.process_log_queue)
        self.log_queue_timer.start(100)

    def stop_log_listener(self):
        self.log_queue_timer.stop()
        self.log_queue = None

    def process_log_queue(self):
        local_queue = self.log_queue
        if local_queue is None:
            return
        while not local_queue.empty():
            try:
                message = local_queue.get_nowait()
                if isinstance(message, tuple) and len(message) == 2:
                    msg_type, content = message
                    if msg_type == "finished":
                        self.on_execution_finished(success=content)
                    elif msg_type == "outputs":
                        self._process_notebook_outputs(content)
                    elif msg_type == "reset_timer":
                        self.start_elapsed_timer()
                else:
                    self.log_message(str(message))
            except Exception:
                pass

    def _process_notebook_outputs(self, nb_object):
        if nb_object is None:
            return
        for cell in nb_object.cells:
            if "outputs" in cell:
                for output in cell.outputs:
                    if output.output_type == "stream":
                        self.log_message(output.text.strip())
                    elif output.output_type == "error":
                        self.log_message(f"LỖI: {''.join(output.traceback)}")

    def log_message(self, message):
        self.log_console.append(message)
        scrollbar = self.log_console.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())


class SectionWidget(QWidget):
    notebooks_dropped = pyqtSignal(object, list)
    notebook_remove_requested = pyqtSignal(object, list)
    section_close_requested = pyqtSignal(object)

    def __init__(self, section_name, section_id, parent_runner=None):
        super().__init__()
        self.section_name, self.section_id, self.parent_runner = section_name, section_id, parent_runner
        self.notebook_cards, self.running_processes, self.schedules = {}, {}, []
        self.schedule_counter, self.is_sequence_running = 0, False
        self.schedule_timer = QTimer(self)
        self.schedule_timer.timeout.connect(self.check_scheduled_actions)
        self.schedule_timer.start(1000)
        self.setMinimumWidth(config.SECTION_MIN_WIDTH)
        self.setAcceptDrops(True)
        self.setup_ui()

    def dragEnterEvent(self, a0: QDragEnterEvent | None) -> None:
        if a0:
            mime_data = a0.mimeData()
            if mime_data and mime_data.hasText():
                a0.acceptProposedAction()
            else:
                a0.ignore()

    def dropEvent(self, a0: QDropEvent | None) -> None:
        if a0:
            mime_data = a0.mimeData()
            if mime_data and mime_data.hasText():
                self.notebooks_dropped.emit(self, mime_data.text().split("\n"))
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
        self.schedule_time_edit.setStyleSheet(
            "QTimeEdit{background-color:#f0f0f0;border:1px solid #ccc;border-radius:4px;padding:3px 5px;color:black;}"
        )
        add_schedule_layout.addWidget(self.schedule_time_edit)
        self.add_schedule_btn = QPushButton("Thêm")
        self.add_schedule_btn.setObjectName("SetScheduleButton")
        self.add_schedule_btn.clicked.connect(self.add_schedule)
        add_schedule_layout.addWidget(self.add_schedule_btn)
        schedule_main_layout.addLayout(add_schedule_layout)
        scroll_schedules = QScrollArea()
        scroll_schedules.setWidgetResizable(True)
        scroll_schedules.setStyleSheet("QScrollArea{border:1px solid #dee2e6;border-radius:4px;}")
        scroll_schedules.setFixedHeight(60)
        self.schedule_list_widget = QWidget()
        self.schedule_list_widget.setObjectName("ScheduleListContainer")
        self.schedule_list_widget.setStyleSheet("QWidget#ScheduleListContainer{background-color:white;}")
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
        self.run_sequential_btn.clicked.connect(self.run_all_sequential_wrapper)
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
        action_map = {
            "Chạy đồng thời": "run_all_simultaneously",
            "Chạy lần lượt": "run_all_sequential_wrapper",
            "Dừng tất cả": "stop_all_notebooks",
        }
        action_key = action_map.get(action_text)
        self.schedules.append({"id": schedule_id, "action_key": action_key, "action_text": action_text, "time": schedule_time})
        self.update_schedule_display()
        if self.parent_runner:
            functions.log_message(f"[{self.section_name}] Đã thêm lịch hẹn: '{action_text}' lúc {schedule_time.toString('HH:mm')}")

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
            placeholder.setStyleSheet("color:#888;")
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
                if hasattr(self, schedule["action_key"]):
                    getattr(self, schedule["action_key"])()
                if self.parent_runner:
                    functions.log_message(f"[{self.section_name}] Thực thi hẹn giờ: {schedule['action_text']}")
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
            self.notebook_cards.pop(path).deleteLater()
        if path in self.running_processes:
            del self.running_processes[path]

    def on_card_run_requested(self, card):
        self.run_notebook(card)

    def on_card_stop_requested(self, path):
        if self.parent_runner:
            functions.log_message(f"[{self.section_name}] Gửi tín hiệu dừng: {os.path.basename(path)}")
        if path in self.running_processes:
            proc_info = self.running_processes[path]
            proc_info["stop_event"].set()
            proc_info["process"].join(timeout=2.0)
            if proc_info["process"].is_alive():
                proc_info["process"].terminate()
                if self.parent_runner:
                    functions.log_message(f"[{self.section_name}] Buộc dừng: {os.path.basename(path)}")
            card = self.notebook_cards.get(path)
            if card:
                card.on_execution_finished(success=False)
                card.set_status("stopped")
            if path in self.running_processes:
                del self.running_processes[path]

    def on_card_remove_requested(self, path):
        self.notebook_remove_requested.emit(self, [path])

    def on_card_clear_log_requested(self, path):
        pass

    def run_notebook(self, card):
        if self.parent_runner:
            modules_path = self.parent_runner.modules_path
            functions.run_notebook_with_individual_logging(
                card.path,
                self.running_processes,
                card,
                card.execution_mode,
                card.execution_count,
                card.execution_delay,
                modules_path,
            )

    def run_all_simultaneously(self):
        if not self.notebook_cards:
            return
        if self.parent_runner:
            functions.log_message(f"[{self.section_name}] Bắt đầu chạy đồng thời...")
        for card in self.notebook_cards.values():
            if card.path not in self.running_processes:
                card.run_notebook()

    def run_all_sequential_wrapper(self):
        if self.is_sequence_running:
            if self.parent_runner:
                functions.log_message(f"[{self.section_name}] Một chuỗi tuần tự đã đang chạy.")
            return
        threading.Thread(target=self._run_all_sequential_task, daemon=True).start()

    def _run_all_sequential_task(self):
        if not self.notebook_cards:
            return
        self.is_sequence_running = True
        self.run_all_btn.setEnabled(False)
        self.run_sequential_btn.setEnabled(False)
        if self.parent_runner:
            functions.log_message(f"[{self.section_name}] Bắt đầu chạy lần lượt...")

        ordered_cards = []
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item:
                widget = item.widget()
                if isinstance(widget, SectionNotebookCard):
                    ordered_cards.append(widget)

        for card in ordered_cards:
            if not self.is_sequence_running:
                if self.parent_runner:
                    functions.log_message(f"[{self.section_name}] Chuỗi tuần tự đã bị dừng.")
                break
            if card.path in self.running_processes:
                continue
            card.set_status("waiting")
            card.run_notebook()
            if card.path in self.running_processes:
                proc_info = self.running_processes[card.path]
                proc_info["process"].join()
                if card.path in self.running_processes:
                    del self.running_processes[card.path]

        if self.parent_runner:
            functions.log_message(f"[{self.section_name}] Đã hoàn thành chạy lần lượt.")
        self.is_sequence_running = False
        self.run_all_btn.setEnabled(True)
        self.run_sequential_btn.setEnabled(True)

    def stop_all_notebooks(self):
        self.is_sequence_running = False
        if any(p["process"].is_alive() for p in self.running_processes.values()):
            if self.parent_runner:
                functions.log_message(f"[{self.section_name}] Dừng tất cả...")
            for path in list(self.running_processes.keys()):
                self.on_card_stop_requested(path)

    def close_section(self):
        reply = QMessageBox.question(
            self,
            "Xác nhận đóng Section",
            f"Bạn có chắc muốn đóng section '{self.section_name}' không? "
            f"Có {len(self.notebook_cards)} notebook(s) sẽ được trả về danh sách.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.stop_all_notebooks()
            self.section_close_requested.emit(self)

    def cleanup(self):
        if hasattr(self, "schedule_timer"):
            self.schedule_timer.stop()
        self.stop_all_notebooks()
        if self.notebook_cards and self.parent_runner:
            self.notebook_remove_requested.emit(self, list(self.notebook_cards.keys()))
