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
            padding-top: 8px;
            background-color: #ffffff;
            color: #2c3e50;
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
        
        #SectionGroup {
            border: 2px solid #dee2e6;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa);
            border-radius: 12px;
            padding: 5px;
        }
        
        #DefaultSectionGroup {
            border: 3px solid #28a745;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d4edda, stop:1 #c3e6cb);
            border-radius: 12px;
            padding: 5px;
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
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0056b3, stop:1 #004085);
            color: #ffffff;
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #004085, stop:1 #002752);
            color: #ffffff;
        }
        
        /* === SPECIALIZED BUTTONS === */
        #ClearButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6c757d, stop:1 #495057);
        }
        #ClearButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #495057, stop:1 #343a40);
        }
        
        #RefreshButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #28a745, stop:1 #1e7e34);
        }
        #RefreshButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e7e34, stop:1 #155724);
        }
        
        #StopButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc3545, stop:1 #bd2130);
        }
        #StopButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #bd2130, stop:1 #a71e2a);
        }

        #ToggleConsoleButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007bff, stop:1 #0056b3);
        }
        #ToggleConsoleButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0056b3, stop:1 #004085);
        }
        
        /* === TEXT AREAS === */
        #Console {
            background-color: #1e1e1e;
            color: #ffffff;
            border: 2px solid #495057;
            border-radius: 8px;
            padding: 8px;
            font-family: "JetBrains Mono", "Consolas", monospace;
            selection-background-color: #007acc;
        }
        
        QTextEdit {
            background-color: #ffffff;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            color: #2c3e50;
            padding: 8px;
        }
        
        /* === SCROLL AREAS === */
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        #AvailableScrollArea, #SectionScrollArea, #SectionsScrollArea {
            border: 1px solid #e9ecef;
            border-radius: 8px;
            background-color: #ffffff;
        }
        
        /* === CARDS CONTAINER === */
        #CardsContainer {
            background-color: #ffffff;
            border-radius: 6px;
        }
        #SectionsContainer {
            background-color: transparent;
        }
        
        /* === CARDS === */
        #Card, #SelectedCard {
            border: 2px solid #e9ecef;
            border-radius: 10px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffffff, stop:1 #f8f9fa);
            margin: 2px;
            padding: 4px;
        }
        #Card:hover {
            border: 2px solid #007bff;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e3f2fd, stop:1 #bbdefb);
        }
        #SelectedCard {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #cce5ff, stop:1 #99d6ff);
            border: 2px solid #007bff;
        }
        
        /* === LABELS === */
        QLabel, #CardLabel {
            background-color: transparent;
            border: none;
            color: #2c3e50;
        }
        
        #SectionsTitle {
            color: #495057;
            font-size: 12pt;
            font-weight: bold;
        }
        
        #SectionTitle {
            color: #343a40;
            font-weight: bold;
            padding: 5px 10px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f8f9fa, stop:1 #e9ecef);
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        #SectionTitle:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e3f2fd, stop:1 #bbdefb);
            border: 1px solid #007bff;
        }
        
        /* === HEADERS === */
        #SectionsHeader {
            background-color: transparent;
            padding: 8px 0px;
            border-bottom: 1px solid #e9ecef;
        }
        
        #SectionHeader {
            background-color: transparent;
            padding: 2px 0px;
        }
        
        /* === MESSAGE BOXES === */
        QMessageBox {
            background-color: #ffffff;
            color: #2c3e50;
        }
        QMessageBox QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #007bff, stop:1 #0056b3);
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            min-width: 80px;
        }
        QMessageBox QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0056b3, stop:1 #004085);
        }
        
        /* === INPUT DIALOGS === */
        QInputDialog {
            background-color: #ffffff;
            color: #2c3e50;
        }
        QInputDialog QLineEdit {
            background-color: #ffffff;
            border: 2px solid #dee2e6;
            border-radius: 6px;
            padding: 8px;
            color: #2c3e50;
        }
        
        /* === SPLITTER === */
        QSplitter {
            background-color: #f8f9fa;
        }
        QSplitter::handle {
            background: transparent;
            border: none;
            margin: 0px;
        }
        QSplitter::handle:horizontal {
            width: 6px;
            border-radius: 0px;
        }
        QSplitter::handle:hover {
            background: rgba(0, 123, 255, 0.1);
            border: none;
        }        #MainSplitter {
            background-color: transparent;
        }
        
        /* === SCROLLBARS === */
        QScrollBar:vertical {
            background: #f8f9fa;
            width: 12px;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #adb5bd;
            min-height: 20px;
            border-radius: 5px;
            margin: 1px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        QScrollBar:horizontal {
            background: #f8f9fa;
            height: 12px;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background: #adb5bd;
            min-width: 20px;
            border-radius: 5px;
            margin: 1px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            border: none;
            background: none;
        }
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }
        
        /* === SCROLLBARS FOR NOTEBOOK LIST === */
        #AvailableScrollArea QScrollBar:vertical,
        #SectionScrollArea QScrollBar:vertical,
        #SectionsScrollArea QScrollBar:vertical {
            background: #f1f3f4;
            width: 10px;
            border: none;
            border-radius: 5px;
        }
        #AvailableScrollArea QScrollBar::handle:vertical,
        #SectionScrollArea QScrollBar::handle:vertical,
        #SectionsScrollArea QScrollBar::handle:vertical {
            background: #c1c7cd;
            border-radius: 5px;
            min-height: 20px;
            margin: 0px;
        }
        #AvailableScrollArea QScrollBar::add-line:vertical,
        #AvailableScrollArea QScrollBar::sub-line:vertical,
        #SectionScrollArea QScrollBar::add-line:vertical,
        #SectionScrollArea QScrollBar::sub-line:vertical,
        #SectionsScrollArea QScrollBar::add-line:vertical,
        #SectionsScrollArea QScrollBar::sub-line:vertical {
            border: none;
            background: none;
            height: 0px;
        }
        #AvailableScrollArea QScrollBar::add-page:vertical,
        #AvailableScrollArea QScrollBar::sub-page:vertical,
        #SectionScrollArea QScrollBar::add-page:vertical,
        #SectionScrollArea QScrollBar::sub-page:vertical,
        #SectionsScrollArea QScrollBar::add-page:vertical,
        #SectionsScrollArea QScrollBar::sub-page:vertical {
            background: none;
        }
    """
