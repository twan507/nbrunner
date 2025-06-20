"""
Module chứa các style CSS cho ứng dụng NotebookRunner
"""


def get_stylesheet():
    """Trả về stylesheet CSS cho ứng dụng"""
    return """
        /* === MAIN WINDOW === */
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
            padding: 8px;
            background-color: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            left: 15px;
            color: #495057;
            background-color: #ffffff;
        }
        #LogGroup, #AvailableGroup, #ControlsGroup, #SectionGroup {
            border: 2px solid #dee2e6;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa);
        }
        
        #SectionGroup::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: -9999px; /* Hide the original title */
        }
        
        #SectionTitleLabel {
            font-size: 13pt;
            font-weight: bold;
            color: #0056b3;
            padding: 5px;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 5px;
        }
        #SectionTitleLabel:hover {
            background-color: #e3f2fd;
            border-radius: 5px;
        }
        
        /* === BUTTONS === */
        QPushButton {
            font-family: "Segoe UI";
            font-size: 10pt;
            font-weight: 500;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007bff, stop:1 #0056b3);
            color: #ffffff;
            border: none;
            padding: 10px 16px;
            border-radius: 8px;
            min-height: 20px;
        }
        QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0056b3, stop:1 #004085); }
        QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #004085, stop:1 #002752); }
        QPushButton:disabled { background-color: #adb5bd; color: #e9ecef; }

        /* === COMBOBOX === */
        QComboBox {
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 3px 5px;
            color: black;
        }
        QComboBox QAbstractItemView {
            background-color: white;
            border: 1px solid #ccc;
            selection-background-color: #007bff;
            color: black;
        }

        /* === DIALOGS & MESSAGE BOXES === */
        QMessageBox, QInputDialog { background-color: #ffffff; color: #2c3e50; }
        QMessageBox QPushButton, QInputDialog QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007bff, stop:1 #0056b3);
            color: #ffffff; border: none; padding: 8px 16px; border-radius: 6px; min-width: 80px;
        }
        QMessageBox QPushButton:hover, QInputDialog QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0056b3, stop:1 #004085); }
        QInputDialog QLineEdit {
            background-color: #ffffff; border: 2px solid #dee2e6; border-radius: 6px;
            padding: 8px; color: #2c3e50; font-size: 10pt;
        }

        /* === SCROLL & TEXT AREAS === */
        QScrollArea { border: none; background-color: transparent; }
        #AvailableScrollArea, #SectionScrollArea { border: 1px solid #e9ecef; border-radius: 8px; background-color: #ffffff; }
        #CardsContainer { background-color: #ffffff; border-radius: 6px; }
        
        /* === THAY ĐỔI Ở ĐÂY: Gộp style cho 2 console === */
        #Console, #SectionConsole {
            background-color: #1e1e1e; /* Màu nền giống nhau */
            color: #d4d4d4;           /* Màu chữ giống nhau */
            border: 1px solid #495057; /* Viền giống nhau */
            border-radius: 8px;
            padding: 8px;
            font-family: "JetBrains Mono", "Consolas", monospace;
        }
        
        QTextEdit { background-color: #ffffff; border: 2px solid #dee2e6; border-radius: 8px; color: #2c3e50; padding: 8px; }
        
        /* === CARDS === */
        #Card, #SelectedCard { border: 2px solid #e9ecef; border-radius: 10px; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa); margin: 2px; padding: 4px; }
        #Card:hover { border: 2px solid #007bff; background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e3f2fd, stop:1 #bbdefb); }
        #SelectedCard { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #cce5ff, stop:1 #99d6ff); border: 2px solid #007bff; }
        QLabel, #CardLabel { background-color: transparent; border: none; color: #2c3e50; }
        
        /* === SPLITTER === */
        QSplitter::handle { background: transparent; } QSplitter::handle:horizontal { width: 6px; } QSplitter::handle:hover { background: rgba(0, 123, 255, 0.1); }
        
        /* === NOTEBOOK CARD (IN SECTION) === */
        #SectionCard { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa); border: 1px solid #dee2e6; border-radius: 8px; margin: 5px; padding: 8px; }
        
        /* Style cũ của #SectionConsole đã được gộp vào #Console ở trên */
        
        #RunButton, #StopButton, #RemoveButton, #ClearLogButton { border: none; border-radius: 6px; padding: 4px 8px; font-weight: bold; font-size: 9pt; max-width: 70px; max-height: 25px; }
        #RunButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #28a745, stop:1 #1e7e34); color: white; }        #RunButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34ce57, stop:1 #28a745); }
        #RunButton:disabled { background: #6c757d; color: #adb5bd; }
        #StopButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fd7e14, stop:1 #e8590c); color: white; }
        #StopButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff9a3c, stop:1 #fd7e14); }
        #StopButton:disabled { background: #6c757d; color: #adb5bd; }
        #RemoveButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc3545, stop:1 #c82333); color: white; }
        #RemoveButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e4606d, stop:1 #dc3545); }        
        #ClearLogButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6f42c1, stop:1 #5a32a3); color: white; }
        #ClearLogButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8a63d2, stop:1 #6f42c1); }

        /* === SECTION CONTROL BUTTONS === */
        #SectionControlButton, #SectionRunButton, #SectionStopButton, #SectionRemoveButton, #SetScheduleButton, #CancelScheduleButton {
            color: white; border: none; border-radius: 6px; padding: 8px 12px; font-weight: 500; font-size: 10pt; min-height: 20px;
        }
        #SectionControlButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #17a2b8, stop:1 #138496); }
        #SectionControlButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #20c9e0, stop:1 #17a2b8); }
        #SectionRunButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #28a745, stop:1 #1e7e34); }
        #SectionRunButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34ce57, stop:1 #28a745); }
        #SectionStopButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fd7e14, stop:1 #e8590c); }
        #SectionStopButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ff9a3c, stop:1 #fd7e14); }
        #SectionRemoveButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc3545, stop:1 #c82333); }
        #SectionRemoveButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e4606d, stop:1 #dc3545); }
        
        /* STYLES FOR SCHEDULER */
        #SetScheduleButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #28a745, stop:1 #1e7e34); padding: 5px 10px; font-size: 9pt; }
        #SetScheduleButton:disabled { background-color: #a3d9b1; color: #d4edda; }
        #CancelScheduleButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc3545, stop:1 #c82333); padding: 5px 10px; font-size: 9pt; }
        #CancelScheduleButton:disabled { background-color: #f5c6cb; color: #f8d7da; }
    """
