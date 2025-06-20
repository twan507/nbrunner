# Nội dung mới cho file: development/src/styles.py

def get_stylesheet():
    """Trả về stylesheet CSS đã được tổ chức lại cho ứng dụng"""
    return """
        /* === CỬA SỔ CHÍNH & WIDGET NỀN === */
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
            /* MODIFIED: Giảm padding mặc định của groupbox */
            padding: 2px;
            background-color: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            /* MODIFIED: Giảm padding và vị trí của title */
            padding: 0 2px;
            left: 10px;
            color: #495057;
            background-color: #ffffff;
        }
        #LogGroup, #AvailableGroup, #ControlsGroup, #SectionControlsGroup {
            border: 2px solid #dee2e6;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa);
        }

        /* === KHU VỰC CUỘN & VĂN BẢN === */
        QScrollArea { border: none; background-color: transparent; }
        #AvailableScrollArea, #SectionScrollArea { 
            border: 1px solid #e9ecef; 
            border-radius: 8px; 
            background-color: #ffffff; 
        }
        #CardsContainer { background-color: #ffffff; border-radius: 6px; }
        #Console, #SectionConsole {
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid #495057;
            border-radius: 8px;
            /* MODIFIED: Giảm padding của console */
            padding: 5px;
            font-family: "JetBrains Mono", "Consolas", monospace;
        }
        QTextEdit { 
            background-color: #ffffff; 
            border: 2px solid #dee2e6; 
            border-radius: 8px; 
            color: #2c3e50; 
            /* MODIFIED: Giảm padding của textedit */
            padding: 5px; 
        }
        QComboBox {
            background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 4px;
            padding: 3px 5px; color: black;
        }
        QComboBox QAbstractItemView {
            background-color: white; border: 1px solid #ccc;
            selection-background-color: #007bff; color: black;
        }

        /* === THANH CUỘN === */
        QScrollBar:vertical {
            background-color: #f1f1f1; width: 4px; border-radius: 2px; margin: 0px;
        }
        QScrollBar::handle:vertical {
            background-color: #c1c1c1; border-radius: 2px; min-height: 7px;
        }
        QScrollBar:horizontal {
            background-color: #f1f1f1; height: 4px; border-radius: 2px; margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background-color: #c1c1c1; border-radius: 2px; min-width: 7px;
        }
        QScrollBar::add-line, QScrollBar::sub-line { background: none; height: 0px; width: 0px; }
        QScrollBar::add-page, QScrollBar::sub-page { background: none; }
        
        /* === CARDS === */
        #Card, #SelectedCard { 
            border: 2px solid #e9ecef; border-radius: 10px; 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa); 
            margin: 2px; padding: 4px; 
        }
        #Card:hover { 
            border: 2px solid #007bff; 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e3f2fd, stop:1 #bbdefb); 
        }
        #SelectedCard { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #cce5ff, stop:1 #99d6ff); 
            border: 2px solid #007bff; 
        }
        #SectionCard { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa); 
            border: 1px solid #dee2e6; border-radius: 8px; margin: 5px; 
            /* MODIFIED: Giảm padding của card trong section */
            padding: 6px; 
        }
        QLabel, #CardLabel { background-color: transparent; border: none; color: #2c3e50; }

        /* === SPLITTER === */
        QSplitter::handle { background: transparent; } 
        QSplitter::handle:horizontal { width: 6px; } 
        QSplitter::handle:hover { background: rgba(0, 123, 255, 0.1); }
        
        /**********************************
         * STYLES CHO BUTTON              *
         **********************************/

        /* --- 1. BUTTON TIÊU CHUẨN (KÍCH THƯỚC ĐỒNG BỘ) --- */
        QPushButton {
            font-family: "Segoe UI";
            font-size: 10pt;
            font-weight: 500;
            color: #ffffff;
            border: none;
            /* MODIFIED: Giảm padding của button */
            padding: 6px 10px;
            border-radius: 8px;
            min-height: 22px;
        }
        
        /* Màu nền mặc định (xanh dương) cho QPushButton "Thêm Section" */
        #AddSectionButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007bff, stop:1 #0056b3);
        }
        #AddSectionButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0056b3, stop:1 #004085);
        }
        #AddSectionButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #004085, stop:1 #002752);
        }
        QPushButton:disabled {
            background-color: #adb5bd;
            color: #e9ecef;
        }

        /* Màu XANH LÁ cho các nút "Chạy", "Làm Mới", "Hẹn giờ" */
        #RefreshButton, #SectionRunButton, #SetScheduleButton { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #28a745, stop:1 #1e7e34); 
        }
        #RefreshButton:hover, #SectionRunButton:hover, #SetScheduleButton:hover { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34ce57, stop:1 #28a745); 
        }

        /* Màu CAM cho nút "Dừng" */
        #SectionStopButton { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fd7e14, stop:1 #e8590c); 
        }
        #SectionStopButton:hover { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff9a3c, stop:1 #fd7e14); 
        }

        /* Màu ĐỎ cho các nút "Xóa", "Đóng" */
        #SectionRemoveButton { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc3545, stop:1 #c82333); 
        }
        #SectionRemoveButton:hover { 
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e4606d, stop:1 #dc3545); 
        }

        /* Màu TÍM cho các nút "Xóa Log", "Xóa Console" */
        #ClearButton {
             background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6f42c1, stop:1 #5a32a3);
        }
        #ClearButton:hover {
             background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8a63d2, stop:1 #6f42c1);
        }
        
        /* --- 2. BUTTON NHỎ (TRONG NOTEBOOK CARD) --- */
        #RunButton, #StopButton, #RemoveButton, #ClearLogButton {
            border: none;
            border-radius: 6px;
            padding: 2px 4px;
            font-weight: bold;
            font-size: 8pt;
            color: white;
        }

        #SetScheduleButton {
            padding-top: 3px;
            padding-bottom: 3px;
        }

        #RunButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #28a745, stop:1 #1e7e34); }
        #RunButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34ce57, stop:1 #28a745); }
        #RunButton:disabled { background: #6c757d; }

        #StopButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fd7e14, stop:1 #e8590c); }
        #StopButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff9a3c, stop:1 #fd7e14); }
        #StopButton:disabled { background: #6c757d; }

        #RemoveButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc3545, stop:1 #c82333); }
        #RemoveButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e4606d, stop:1 #dc3545); }

        #ClearLogButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6f42c1, stop:1 #5a32a3); }
        #ClearLogButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8a63d2, stop:1 #6f42c1); }
    """
