"""
Ponto de entrada do WinPE Studio.
Execute com: python -m app.main  (dentro da pasta WinPE_Studio)
"""
import sys
import os
from pathlib import Path


def _setup_base_path():
    """
    Quando empacotado pelo PyInstaller, os recursos ficam em sys._MEIPASS.
    Quando rodando direto, usa o diretório do script.
    """
    if getattr(sys, 'frozen', False):
        # Rodando como .exe empacotado
        base = Path(sys._MEIPASS)
    else:
        # Rodando como script Python normal
        base = Path(__file__).parent.parent

    # Adiciona ao sys.path para imports funcionarem
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

    return base


BASE_PATH = _setup_base_path()

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from app.core.logger import setup_logger
from app.controllers.main_controller import MainController


def main() -> None:
    setup_logger()

    app = QApplication(sys.argv)
    app.setApplicationName("WinPE Studio")
    app.setApplicationVersion("2.1.0")
    app.setOrganizationName("WinPEForge")

    controller = MainController()
    controller.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
