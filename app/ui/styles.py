"""Tema escuro moderno — JRDEV1 PXE (identidade visual JRDEV1)."""

# Paleta JRDEV1: azul marinho escuro + azul eletrico + branco
# #0D1B3E (fundo), #091428 (sidebar), #1A3A6B (cards), #2E6BE6 (accent)

DARK_THEME_QSS = """
* {
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
    color: #E8EDF5;
}

QMainWindow, QWidget {
    background-color: #0D1B3E;
}

#Sidebar {
    background-color: #091428;
    border-right: 2px solid #1A3A6B;
}

#SidebarLogo {
    font-size: 15px;
    font-weight: bold;
    color: #FFFFFF;
    padding: 0 10px;
    line-height: 1.4;
}

#SidebarInfo {
    font-size: 11px;
    color: #4A6FA5;
    padding: 0 14px 8px 14px;
}

#NavButton {
    background-color: transparent;
    border: none;
    text-align: left;
    padding: 10px 18px;
    margin: 2px 8px;
    border-radius: 6px;
    color: #7A9CC8;
    font-size: 13px;
}

#NavButton:hover {
    background-color: #1A3A6B;
    color: #E8EDF5;
}

#NavButton:checked {
    background-color: #2E6BE6;
    color: #FFFFFF;
    font-weight: bold;
}

#PageTitle {
    font-size: 22px;
    font-weight: bold;
    color: #E8EDF5;
}

#PageSubtitle {
    font-size: 13px;
    color: #4A6FA5;
    margin-top: -8px;
}

#BtnPrimary {
    background-color: #2E6BE6;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 13px;
}

#BtnPrimary:hover {
    background-color: #4A85F5;
}

#BtnPrimary:pressed {
    background-color: #1A52C0;
}

QPushButton {
    background-color: #1A3A6B;
    color: #E8EDF5;
    border: 1px solid #2A4A7B;
    border-radius: 5px;
    padding: 6px 14px;
}

QPushButton:hover {
    background-color: #2A4A8B;
    border-color: #2E6BE6;
}

QPushButton:pressed {
    background-color: #0D2A5A;
}

QPushButton:disabled {
    background-color: #0D1B3E;
    color: #2A4A7B;
    border-color: #1A3A6B;
}

#StatusCard {
    background-color: #1A3A6B;
    border: 1px solid #2A4A7B;
    border-radius: 10px;
}

#CardLabel {
    font-size: 11px;
    color: #4A6FA5;
    text-transform: uppercase;
}

#CardValue {
    font-size: 13px;
    font-weight: bold;
    color: #E8EDF5;
}

QLineEdit {
    background-color: #1A3A6B;
    border: 1px solid #2A4A7B;
    border-radius: 5px;
    padding: 6px 10px;
    color: #E8EDF5;
}

QLineEdit:focus {
    border-color: #2E6BE6;
}

QLineEdit:read-only {
    color: #4A6FA5;
}

QGroupBox {
    border: 1px solid #2A4A7B;
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 16px 16px 16px;
    color: #7A9CC8;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    top: -8px;
    padding: 0 6px;
    background-color: #0D1B3E;
    color: #2E6BE6;
}

QTreeView {
    background-color: #091428;
    border: 1px solid #1A3A6B;
    border-radius: 6px;
    alternate-background-color: #0D1B3E;
    show-decoration-selected: 1;
}

QTreeView::item {
    padding: 4px 2px;
}

QTreeView::item:hover {
    background-color: #1A3A6B;
}

QTreeView::item:selected {
    background-color: #2E6BE6;
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #091428;
    color: #4A6FA5;
    border: none;
    border-bottom: 1px solid #1A3A6B;
    padding: 6px 8px;
    font-size: 11px;
    text-transform: uppercase;
}

#LogArea {
    background-color: #060E1F;
    border: 1px solid #1A3A6B;
    border-radius: 6px;
    color: #5DADE2;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px;
    padding: 8px;
}

#GlobalProgress {
    background-color: #1A3A6B;
    border: none;
    border-radius: 0px;
}

#GlobalProgress::chunk {
    background-color: #2E6BE6;
    border-radius: 0px;
}

QProgressBar {
    background-color: #1A3A6B;
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: #E8EDF5;
}

QProgressBar::chunk {
    background-color: #2E6BE6;
    border-radius: 4px;
}

QStatusBar {
    background-color: #091428;
    border-top: 1px solid #1A3A6B;
    color: #4A6FA5;
    font-size: 12px;
    padding: 2px 8px;
}

QScrollBar:vertical {
    background: #0D1B3E;
    width: 8px;
    border: none;
}

QScrollBar::handle:vertical {
    background: #2A4A7B;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #2E6BE6;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #0D1B3E;
    height: 8px;
    border: none;
}

QScrollBar::handle:horizontal {
    background: #2A4A7B;
    border-radius: 4px;
}

QMenu {
    background-color: #0D1B3E;
    border: 1px solid #2A4A7B;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 20px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #1A3A6B;
    color: #E8EDF5;
}

QMenu::separator {
    height: 1px;
    background: #2A4A7B;
    margin: 4px 8px;
}

QMessageBox {
    background-color: #0D1B3E;
}

QMessageBox QLabel {
    color: #E8EDF5;
}

QDialog {
    background-color: #0D1B3E;
}

QComboBox {
    background-color: #1A3A6B;
    border: 1px solid #2A4A7B;
    border-radius: 5px;
    padding: 6px 10px;
    color: #E8EDF5;
}

QComboBox:focus {
    border-color: #2E6BE6;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #1A3A6B;
    border: 1px solid #2A4A7B;
    selection-background-color: #2E6BE6;
    color: #E8EDF5;
}

QCheckBox {
    color: #E8EDF5;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #2A4A7B;
    border-radius: 3px;
    background-color: #1A3A6B;
}

QCheckBox::indicator:checked {
    background-color: #2E6BE6;
    border-color: #2E6BE6;
}

QCheckBox::indicator:disabled {
    background-color: #0D1B3E;
    border-color: #1A3A6B;
}
"""
