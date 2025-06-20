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
        #LogGroup, #AvailableGroup, #ControlsGroup {
            border: 2px solid #dee2e6;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa);
        }
        
        #SectionGroup {
            border: 2px solid #007bff;
            background: #f0f8ff;
            padding: 5px;
            margin-top: 5px;
        }
        /* Bỏ title mặc định của SectionGroup để dùng ClickableLabel */
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
        #Console {
            background-color: #1e1e1e; color: #d4d4d4; border: 2px solid #495057;
            border-radius: 8px; padding: 8px; font-family: "JetBrains Mono", "Consolas", monospace;
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
        #SectionConsole { background-color: #2d3748; color: #e2e8f0; border: 1px solid #4a5568; border-radius: 6px; font-family: "JetBrains Mono", monospace; font-size: 8pt; padding: 6px; }
        
        #RunButton, #StopButton, #RemoveButton, #ClearLogButton { border: none; border-radius: 6px; padding: 4px 8px; font-weight: bold; font-size: 9pt; max-width: 70px; max-height: 25px; }
        #RunButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #28a745, stop:1 #218838); color: white; }
        #RunButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34ce57, stop:1 #28a745); }
        #RunButton:disabled { background: #6c757d; color: #adb5bd; }
        #StopButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc3545, stop:1 #bd2130); color: white; }
        #StopButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #bd2130, stop:1 #a71e2a); }
        #RemoveButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6f42c1, stop:1 #5a32a3); color: white; }
        #RemoveButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #865fcf, stop:1 #6f42c1); }
        #ClearLogButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6c757d, stop:1 #5a6268); color: white; }
        #ClearLogButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #7c858d, stop:1 #6c757d); }

        /* === SECTION CONTROL BUTTONS === */
        #SectionControlButton, #SectionRunButton, #SectionStopButton, #SectionRemoveButton, #SetScheduleButton, #CancelScheduleButton {
            color: white; border: none; border-radius: 6px; padding: 8px 12px; font-weight: 500; font-size: 10pt; min-height: 20px;
        }
        #SectionControlButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #17a2b8, stop:1 #138496); }
        #SectionRunButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #28a745, stop:1 #1e7e34); }
        #SectionStopButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fd7e14, stop:1 #e8590c); }
        #SectionRemoveButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc3545, stop:1 #c82333); }
        
        /* STYLES FOR SCHEDULER */
        #SetScheduleButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #28a745, stop:1 #1e7e34); padding: 5px 10px; font-size: 9pt; }
        #SetScheduleButton:disabled { background-color: #a3d9b1; color: #d4edda; }
        #CancelScheduleButton { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc3545, stop:1 #c82333); padding: 5px 10px; font-size: 9pt; }
        #CancelScheduleButton:disabled { background-color: #f5c6cb; color: #f8d7da; }
    """
