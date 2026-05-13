"""
Ponto de entrada do WinPE Studio.
Execute com: python -m app.main  (dentro da pasta WinPE_Studio)
"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from app.core.logger import setup_logger
from app.controllers.main_controller import MainController
from app.utils.admin_check import require_admin


def main() -> None:
    setup_logger()
    
    # O .bat agora cuida de tudo.
    # require_admin()

    # High DPI automático (PySide6 já habilita por padrão no Qt6)
    app = QApplication(sys.argv)
    app.setApplicationName("WinPE Studio")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("WinPEForge")

    controller = MainController()
    controller.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
