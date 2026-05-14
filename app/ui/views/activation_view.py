"""
Tela de ativação de licença — exibida quando o programa não tem licença válida.
"""
from datetime import date
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QMessageBox, QFrame,
)
from app.core.license_service import (
    activate_license, check_license, LicenseStatus,
    get_machine_id_display,
)


class ActivationView(QWidget):
    """
    Tela de ativação exibida antes do programa principal.
    Emite `activated` quando a licença é validada com sucesso.
    """
    activated = Signal()

    def __init__(self, status: str = LicenseStatus.NOT_FOUND, info: dict = None):
        super().__init__()
        self._status = status
        self._info   = info or {}
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("WinPE Studio — Ativação")
        self.setFixedSize(520, 420)
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E2E;
                color: #CDD6F4;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #313244;
                border: 1px solid #45475A;
                border-radius: 6px;
                padding: 10px 14px;
                color: #CDD6F4;
                font-size: 15px;
                letter-spacing: 2px;
            }
            QLineEdit:focus {
                border: 1px solid #89B4FA;
            }
            QPushButton#BtnActivate {
                background-color: #89B4FA;
                color: #11111B;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton#BtnActivate:hover {
                background-color: #B4D0FF;
            }
            QPushButton#BtnActivate:disabled {
                background-color: #45475A;
                color: #6C7086;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(48, 40, 48, 40)
        root.setSpacing(0)

        # Logo / título
        lbl_logo = QLabel("WinPE Studio Pro")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_logo.setStyleSheet("font-size: 26px; font-weight: bold; color: #89B4FA;")
        root.addWidget(lbl_logo)

        root.addSpacing(6)

        lbl_sub = QLabel("Ativação de Licença")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet("color: #6C7086; font-size: 13px;")
        root.addWidget(lbl_sub)

        root.addSpacing(28)

        # Mensagem de status
        self._lbl_status = QLabel(self._status_message())
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_status.setWordWrap(True)
        self._lbl_status.setStyleSheet(
            f"color: {self._status_color()}; "
            "background: #313244; border-radius: 8px; padding: 10px;"
        )
        root.addWidget(self._lbl_status)

        root.addSpacing(24)

        # Campo da chave
        lbl_key = QLabel("Chave de Licença:")
        lbl_key.setStyleSheet("color: #A6ADC8; font-size: 13px;")
        root.addWidget(lbl_key)

        root.addSpacing(6)

        self._txt_key = QLineEdit()
        self._txt_key.setPlaceholderText("KIRO-XXXX-XXXX-XXXX-XXXX")
        self._txt_key.setMaxLength(24)
        self._txt_key.textChanged.connect(self._on_key_changed)
        root.addWidget(self._txt_key)

        root.addSpacing(20)

        # Botão ativar
        self._btn_activate = QPushButton("🔑  Ativar Licença")
        self._btn_activate.setObjectName("BtnActivate")
        self._btn_activate.setEnabled(False)
        self._btn_activate.clicked.connect(self._do_activate)
        root.addWidget(self._btn_activate)

        root.addStretch()

        # Rodapé
        lbl_footer = QLabel(
            "Precisa de uma licença? Entre em contato com o suporte."
        )
        lbl_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_footer.setStyleSheet("color: #45475A; font-size: 11px;")
        root.addWidget(lbl_footer)

    def _status_message(self) -> str:
        s = self._status
        if s == LicenseStatus.NOT_FOUND:
            return "⚠️  Nenhuma licença encontrada.\nInsira sua chave de ativação para continuar."
        if s == LicenseStatus.EXPIRED:
            exp = self._info.get("expiry", "")
            try:
                from datetime import date as _d
                d = _d.fromisoformat(exp)
                exp = d.strftime("%d/%m/%Y")
            except Exception:
                pass
            return f"🔴  Licença expirada em {exp}.\nRenove sua licença para continuar."
        if s == LicenseStatus.WRONG_MAC:
            return "🔴  Esta licença pertence a outro computador.\nAdquira uma nova licença."
        if s == LicenseStatus.INVALID:
            return "🔴  Licença corrompida ou inválida.\nInsira uma nova chave."
        return "⚠️  Ativação necessária."

    def _status_color(self) -> str:
        if self._status == LicenseStatus.NOT_FOUND:
            return "#FAB387"
        return "#F38BA8"

    def _on_key_changed(self, text: str):
        # Auto-formata enquanto digita: KIRO-XXXX-XXXX-XXXX-XXXX
        clean = text.upper().replace("-", "").replace(" ", "")
        formatted = ""
        if clean.startswith("KIRO"):
            clean = clean[4:]
            parts = [clean[i:i+4] for i in range(0, min(len(clean), 16), 4)]
            formatted = "KIRO-" + "-".join(parts)
        else:
            formatted = text.upper()

        # Atualiza sem loop
        self._txt_key.blockSignals(True)
        self._txt_key.setText(formatted)
        self._txt_key.blockSignals(False)

        # Habilita botão quando tiver 24 chars (KIRO-XXXX-XXXX-XXXX-XXXX)
        self._btn_activate.setEnabled(len(formatted) == 24)

    def _do_activate(self):
        key = self._txt_key.text().strip()
        self._btn_activate.setEnabled(False)
        self._btn_activate.setText("Verificando...")

        success, msg = activate_license(key)

        self._btn_activate.setEnabled(True)
        self._btn_activate.setText("🔑  Ativar Licença")

        if success:
            QMessageBox.information(self, "Licença Ativada", msg)
            self.activated.emit()
        else:
            QMessageBox.critical(self, "Falha na Ativação", msg)
            self._lbl_status.setText(f"🔴  {msg.split(chr(10))[0]}")
