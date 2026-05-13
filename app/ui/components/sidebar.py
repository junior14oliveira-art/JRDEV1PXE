from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QSpacerItem, QSizePolicy
from PySide6.QtCore import Signal, Qt

class Sidebar(QWidget):
    # Sinal emitido quando um item do menu é clicado
    menu_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(250)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(5)

        # Título / Logo
        title_label = QLabel("WinPE Studio")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff; padding: 0 16px 20px 16px;")
        layout.addWidget(title_label)

        # Botões do Menu
        self.btn_dashboard = self.create_menu_btn("Dashboard", "dashboard", checked=True)
        self.btn_files = self.create_menu_btn("Arquivos do Sistema", "files")
        self.btn_apps = self.create_menu_btn("Programas & Portáteis", "apps")
        self.btn_visual = self.create_menu_btn("Tema e Visual", "visual")
        self.btn_drivers = self.create_menu_btn("Drivers e Registro", "drivers")
        self.btn_build = self.create_menu_btn("Gerar ISO", "build")

        layout.addWidget(self.btn_dashboard)
        layout.addWidget(self.btn_files)
        layout.addWidget(self.btn_apps)
        layout.addWidget(self.btn_visual)
        layout.addWidget(self.btn_drivers)
        layout.addWidget(self.btn_build)

        # Spacer para empurrar configurações para baixo
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Configurações na parte inferior
        self.btn_settings = self.create_menu_btn("Configurações", "settings")
        layout.addWidget(self.btn_settings)
        
        self.buttons = [
            self.btn_dashboard, self.btn_files, self.btn_apps, 
            self.btn_visual, self.btn_drivers, self.btn_build, self.btn_settings
        ]

    def create_menu_btn(self, text: str, page_id: str, checked=False) -> QPushButton:
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda checked=False, b=btn, p=page_id: self.on_btn_clicked(b, p))
        return btn

    def on_btn_clicked(self, clicked_btn: QPushButton, page_id: str):
        for btn in self.buttons:
            if btn != clicked_btn:
                btn.setChecked(False)
        clicked_btn.setChecked(True)
        self.menu_selected.emit(page_id)
