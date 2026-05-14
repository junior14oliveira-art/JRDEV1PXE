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
from app.core.license_service import check_license, LicenseStatus
from app.controllers.main_controller import MainController


def main() -> None:
    setup_logger()

    app = QApplication(sys.argv)
    app.setApplicationName("WinPE Studio")
    app.setApplicationVersion("2.1.0")
    app.setOrganizationName("WinPEForge")

    # ── Verificação de licença ────────────────────────────────────────── #
    status, info = check_license()

    if status != LicenseStatus.VALID:
        # Mostra tela de ativação — bloqueia o programa principal
        from app.ui.views.activation_view import ActivationView
        activation = ActivationView(status=status, info=info)
        activation.show()

        # Quando ativar com sucesso, abre o programa principal
        def _on_activated():
            activation.close()
            _launch_main(app, info=check_license()[1])

        activation.activated.connect(_on_activated)
    else:
        # Licença válida — avisa se estiver perto de expirar
        days_left = info.get("days_left", 999)
        if days_left <= 15:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                None,
                "Licença Expirando",
                f"⚠️ Sua licença expira em {days_left} dias.\n\n"
                "Entre em contato para renovar."
            )
        _launch_main(app, info=info)

    sys.exit(app.exec())


def _launch_main(app, info: dict = None):
    """Inicia o programa principal após licença validada."""
    controller = MainController()
    controller.start()
    # Passa info da licença para a janela principal mostrar na sidebar
    if info:
        try:
            controller.view.set_license_info(info)
        except Exception:
            pass


if __name__ == "__main__":
    main()
