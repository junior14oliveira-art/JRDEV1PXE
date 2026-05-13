"""Tema escuro moderno para o WinPE Studio (inspirado em VS Code + Windows 11)."""

DARK_THEME_QSS = """
/* ── Base ─────────────────────────────────────────────────────── */
* {
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
    color: #CDD6F4;
}

QMainWindow, QWidget {
    background-color: #1E1E2E;
}

/* ── Sidebar ──────────────────────────────────────────────────── */
#Sidebar {
    background-color: #181825;
    border-right: 1px solid #313244;
}

#SidebarLogo {
    font-size: 20px;
    font-weight: bold;
    color: #89B4FA;
    padding: 0 10px;
    line-height: 1.3;
}

#SidebarInfo {
    font-size: 11px;
    color: #6C7086;
    padding: 0 14px 8px 14px;
}

#NavButton {
    background-color: transparent;
    border: none;
    text-align: left;
    padding: 10px 18px;
    margin: 2px 8px;
    border-radius: 6px;
    color: #A6ADC8;
    font-size: 13px;
}

#NavButton:hover {
    background-color: #313244;
    color: #CDD6F4;
}

#NavButton:checked {
    background-color: #89B4FA;
    color: #11111B;
    font-weight: bold;
}

/* ── Títulos de páginas ───────────────────────────────────────── */
#PageTitle {
    font-size: 22px;
    font-weight: bold;
    color: #CDD6F4;
}

#PageSubtitle {
    font-size: 13px;
    color: #6C7086;
    margin-top: -8px;
}

/* ── Botão primário ───────────────────────────────────────────── */
#BtnPrimary {
    background-color: #89B4FA;
    color: #11111B;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 13px;
}

#BtnPrimary:hover {
    background-color: #B4D0FF;
}

#BtnPrimary:pressed {
    background-color: #6C9FE0;
}

/* ── Botões comuns ────────────────────────────────────────────── */
QPushButton {
    background-color: #313244;
    color: #CDD6F4;
    border: 1px solid #45475A;
    border-radius: 5px;
    padding: 6px 14px;
}

QPushButton:hover {
    background-color: #45475A;
}

QPushButton:pressed {
    background-color: #585B70;
}

QPushButton:disabled {
    background-color: #1E1E2E;
    color: #45475A;
    border-color: #313244;
}

/* ── Cards de status ──────────────────────────────────────────── */
#StatusCard {
    background-color: #313244;
    border: 1px solid #45475A;
    border-radius: 10px;
}

#CardLabel {
    font-size: 11px;
    color: #6C7086;
    text-transform: uppercase;
}

#CardValue {
    font-size: 13px;
    font-weight: bold;
    color: #CDD6F4;
}

/* ── Inputs ───────────────────────────────────────────────────── */
QLineEdit {
    background-color: #313244;
    border: 1px solid #45475A;
    border-radius: 5px;
    padding: 6px 10px;
    color: #CDD6F4;
}

QLineEdit:focus {
    border-color: #89B4FA;
}

QLineEdit:read-only {
    color: #6C7086;
}

/* ── GroupBox ─────────────────────────────────────────────────── */
QGroupBox {
    border: 1px solid #45475A;
    border-radius: 8px;
    margin-top: 14px;
    padding: 12px 16px 16px 16px;
    color: #A6ADC8;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    top: -8px;
    padding: 0 6px;
    background-color: #1E1E2E;
    color: #89B4FA;
}

/* ── TreeView ─────────────────────────────────────────────────── */
QTreeView {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    alternate-background-color: #1E1E2E;
    show-decoration-selected: 1;
}

QTreeView::item {
    padding: 4px 2px;
}

QTreeView::item:hover {
    background-color: #313244;
}

QTreeView::item:selected {
    background-color: #89B4FA;
    color: #11111B;
}

QHeaderView::section {
    background-color: #181825;
    color: #6C7086;
    border: none;
    border-bottom: 1px solid #313244;
    padding: 6px 8px;
    font-size: 11px;
    text-transform: uppercase;
}

/* ── Log area ─────────────────────────────────────────────────── */
#LogArea {
    background-color: #11111B;
    border: 1px solid #313244;
    border-radius: 6px;
    color: #A6E3A1;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 12px;
    padding: 8px;
}

/* ── ProgressBar global (fina, topo) ─────────────────────────── */
#GlobalProgress {
    background-color: #313244;
    border: none;
    border-radius: 0px;
}

#GlobalProgress::chunk {
    background-color: #89B4FA;
    border-radius: 0px;
}

/* ── ProgressBar normal ───────────────────────────────────────── */
QProgressBar {
    background-color: #313244;
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: #CDD6F4;
}

QProgressBar::chunk {
    background-color: #89B4FA;
    border-radius: 4px;
}

/* ── Status bar ───────────────────────────────────────────────── */
QStatusBar {
    background-color: #181825;
    border-top: 1px solid #313244;
    color: #6C7086;
    font-size: 12px;
    padding: 2px 8px;
}

/* ── Scrollbars ───────────────────────────────────────────────── */
QScrollBar:vertical {
    background: #1E1E2E;
    width: 8px;
    border: none;
}

QScrollBar::handle:vertical {
    background: #45475A;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #585B70;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #1E1E2E;
    height: 8px;
    border: none;
}

QScrollBar::handle:horizontal {
    background: #45475A;
    border-radius: 4px;
}

/* ── Menu de contexto ─────────────────────────────────────────── */
QMenu {
    background-color: #1E1E2E;
    border: 1px solid #45475A;
    border-radius: 6px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 20px;
    border-radius: 4px;
}

QMenu::item:selected {
    background-color: #313244;
    color: #CDD6F4;
}

QMenu::separator {
    height: 1px;
    background: #45475A;
    margin: 4px 8px;
}

/* ── MessageBox ───────────────────────────────────────────────── */
QMessageBox {
    background-color: #1E1E2E;
}

QMessageBox QLabel {
    color: #CDD6F4;
}
"""
