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


def _create_desktop_shortcut():
    """
    Cria atalho na Área de Trabalho com flag 'Executar como Administrador'.
    Executado uma vez na primeira inicialização.
    """
    import subprocess
    import sys
    import base64
    from pathlib import Path

    try:
        if not getattr(sys, 'frozen', False):
            return  # Só cria atalho no .exe empacotado

        exe_path = sys.executable
        desktop = Path.home() / "Desktop"
        shortcut_path = str(desktop / "JRDEV1 PXE.lnk")
        work_dir = str(Path(exe_path).parent)

        # Já existe — não recria
        if Path(shortcut_path).exists():
            return

        # Script PowerShell usando variáveis para evitar problemas com aspas
        ps_script = (
            f'$e="{exe_path}"; '
            f'$l="{shortcut_path}"; '
            f'$w="{work_dir}"; '
            '$s=New-Object -COM WScript.Shell; '
            '$k=$s.CreateShortcut($l); '
            '$k.TargetPath=$e; '
            '$k.WorkingDirectory=$w; '
            '$k.Description="JRDEV1 PXE - WinPE Studio Pro"; '
            '$k.Save(); '
            '$b=[System.IO.File]::ReadAllBytes($l); '
            '$b[21]=$b[21] -bor 0x20; '
            '[System.IO.File]::WriteAllBytes($l,$b)'
        )

        # Codifica em UTF-16 LE base64 (formato -EncodedCommand do PowerShell)
        encoded = base64.b64encode(ps_script.encode('utf-16-le')).decode('ascii')

        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-EncodedCommand", encoded],
            capture_output=True, timeout=15
        )

    except Exception:
        pass  # Silencioso — não crítico


def main() -> None:
    setup_logger()

    # Cria atalho na Área de Trabalho na primeira execução
    _create_desktop_shortcut()

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
