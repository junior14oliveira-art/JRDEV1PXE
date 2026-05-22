"""
Aba 'Instalação PXE' — Instala Windows automaticamente via rede.

Fluxo:
1. Usuário seleciona a ISO do Windows
2. Configura usuário/senha/disco
3. Clica "Preparar ISO"
4. O programa extrai a ISO, injeta autounattend.xml e script de autostart
5. Clica "Iniciar PXE" — notebooks instalam Windows automaticamente
"""
import os
import time
from pathlib import Path
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QGroupBox, QFormLayout,
    QMessageBox, QFileDialog, QProgressBar, QFrame, QPlainTextEdit,
)
from app.core.unattend_service import UnattendConfig, inject_autounattend
from app.workers.base_worker import BaseWorker
from app.core.iso_service import IsoService


class PrepareInstallWorker(BaseWorker):
    """Prepara ISO do Windows para instalação automática via PXE."""

    def __init__(self, iso_path: str, work_dir: str, config: UnattendConfig,
                 server_ip: str, parent=None):
        super().__init__(parent)
        self.iso_path = iso_path
        self.work_dir = work_dir
        self.config = config
        self.server_ip = server_ip

    def run(self):
        try:
            work = Path(self.work_dir)

            self._log("📦 Extraindo ISO do Windows...")
            self.progress.emit(5)
            svc = IsoService()
            svc.extract_iso(self.iso_path, self.work_dir, log_cb=self._log)
            self.progress.emit(50)

            self._log("📝 Injetando autounattend.xml...")
            ok, result = inject_autounattend(self.work_dir, self.config)
            if not ok:
                self.finished.emit(False, f"Falha ao gerar XML: {result}")
                return
            self._log(f"✅ autounattend.xml: {result}")
            self.progress.emit(70)

            self._log("⚡ Injetando script de autostart no WinPE...")
            self._inject_autostart(work)
            self.progress.emit(100)

            self._log("✅ Preparação concluída! Inicie o servidor PXE.")
            self.finished.emit(True, str(self.work_dir))

        except Exception as e:
            self.finished.emit(False, f"Erro: {e}")

    def _inject_autostart(self, work_dir: Path):
        """Injeta startnet.cmd no WinPE para iniciar o setup automaticamente."""
        script = (
            "@echo off\n"
            "echo JRDEV1 PXE - Instalacao Automatica\n"
            "wpeinit\n"
            "set /a T=0\n"
            ":WAIT\n"
            "ipconfig | find \"192.168\" >nul 2>&1\n"
            "if %errorlevel%==0 goto OK\n"
            "set /a T=%T%+1\n"
            "if %T% GEQ 15 goto OK\n"
            "timeout /t 2 /nobreak >nul\n"
            "goto WAIT\n"
            ":OK\n"
            f"net use Z: \\\\{self.server_ip}\\IMG /user:ACESSO REDE >nul 2>&1\n"
            "if exist Z:\\setup.exe ( Z:\\setup.exe /auto upgrade /quiet & goto END )\n"
            "if exist X:\\setup.exe ( X:\\setup.exe /auto upgrade /quiet & goto END )\n"
            "echo [ERRO] setup.exe nao encontrado\n"
            "pause\n"
            ":END\n"
        )
        sources = work_dir / "sources"
        if sources.exists():
            (sources / "startnet.cmd").write_text(script, encoding="ascii", errors="replace")
            self._log(f"✅ startnet.cmd injetado")
        else:
            self._log("⚠️ Pasta sources nao encontrada")


class PxeInstallView(QWidget):
    log_message = Signal(str)
    request_start_pxe = Signal(str)  # emite work_dir para o main_window iniciar PXE

    def __init__(self):
        super().__init__()
        self._worker = None
        self._prepared_dir = ""
        self._server_ip = "192.168.0.21"
        self._setup_ui()

    def set_server_ip(self, ip: str):
        if ip:
            self._server_ip = ip

    def _append_log(self, msg: str):
        """Adiciona mensagem ao painel de log local."""
        if hasattr(self, '_log_panel'):
            self._log_panel.appendPlainText(msg)
            sb = self._log_panel.verticalScrollBar()
            sb.setValue(sb.maximum())

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(20)

        title = QLabel("🚀  Instalação PXE")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        sub = QLabel(
            "Instala o Windows automaticamente via rede.\n"
            "Notebook dá boot via PXE → Windows instala sozinho → reinicia pronto."
        )
        sub.setObjectName("PageSubtitle")
        root.addWidget(sub)

        # ── ISO ───────────────────────────────────────────────────────── #
        grp_iso = QGroupBox("💿 ISO do Windows")
        form_iso = QFormLayout(grp_iso)
        form_iso.setSpacing(12)

        iso_row = QHBoxLayout()
        self._txt_iso = QLineEdit()
        self._txt_iso.setPlaceholderText("Selecione a ISO do Windows 10/11...")
        iso_row.addWidget(self._txt_iso)
        btn_iso = QPushButton("📂")
        btn_iso.setFixedWidth(36)
        btn_iso.clicked.connect(self._browse_iso)
        iso_row.addWidget(btn_iso)
        form_iso.addRow("ISO do Windows:", iso_row)

        self._txt_version = QLineEdit()
        self._txt_version.setPlaceholderText("Ex: Win11_Pro_v1 (controle de versão)")
        form_iso.addRow("Nome/Versão:", self._txt_version)
        root.addWidget(grp_iso)

        # ── Usuário ───────────────────────────────────────────────────── #
        grp_user = QGroupBox("👤 Conta de Usuário")
        form_user = QFormLayout(grp_user)
        form_user.setSpacing(12)

        self._txt_username = QLineEdit("usuario")
        form_user.addRow("Usuário:", self._txt_username)

        self._txt_password = QLineEdit()
        self._txt_password.setPlaceholderText("Deixe em branco para sem senha")
        self._txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        form_user.addRow("Senha:", self._txt_password)
        root.addWidget(grp_user)

        # ── Disco ─────────────────────────────────────────────────────── #
        grp_disk = QGroupBox("💾 Disco e Partição")
        form_disk = QFormLayout(grp_disk)
        form_disk.setSpacing(12)

        self._cmb_disk = QComboBox()
        self._cmb_disk.addItems(["Disco 0 (primeiro disco)", "Disco 1", "Disco 2"])
        form_disk.addRow("Disco alvo:", self._cmb_disk)

        self._cmb_partition = QComboBox()
        self._cmb_partition.addItems([
            "GPT — UEFI (notebooks modernos)",
            "MBR — BIOS Legacy (notebooks antigos)",
        ])
        form_disk.addRow("Tipo de partição:", self._cmb_partition)

        self._cmb_edition = QComboBox()
        self._cmb_edition.addItems(["Professional", "Home", "Enterprise"])
        form_disk.addRow("Edição:", self._cmb_edition)

        lbl_warn = QLabel("⚠️  O disco será FORMATADO completamente sem confirmação!")
        lbl_warn.setStyleSheet(
            "color: #FAB387; background: #1A2A1A; border: 1px solid #FAB387; "
            "border-radius: 6px; padding: 8px;"
        )
        form_disk.addRow(lbl_warn)
        root.addWidget(grp_disk)

        # ── Status ────────────────────────────────────────────────────── #
        self._lbl_status = QLabel("Selecione uma ISO e configure as opções acima.")
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_status.setWordWrap(True)
        self._lbl_status.setStyleSheet(
            "background: #091428; border: 1px solid #2A4A7B; "
            "border-radius: 8px; padding: 12px; color: #7A9CC8; font-size: 12px;"
        )
        root.addWidget(self._lbl_status)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.hide()
        root.addWidget(self._progress)

        # ── Log ───────────────────────────────────────────────────────── #
        grp_log = QGroupBox("📋 Log")
        log_layout = QVBoxLayout(grp_log)
        self._log_panel = QPlainTextEdit()
        self._log_panel.setReadOnly(True)
        self._log_panel.setMaximumBlockCount(300)
        self._log_panel.setFixedHeight(160)
        self._log_panel.setStyleSheet(
            "QPlainTextEdit {"
            "  background-color: #060E1F;"
            "  color: #5DADE2;"
            "  font-family: 'Consolas', monospace;"
            "  font-size: 11px;"
            "  border: 1px solid #1A3A6B;"
            "  border-radius: 4px;"
            "  padding: 6px;"
            "}"
        )
        log_layout.addWidget(self._log_panel)
        root.addWidget(grp_log)

        # Conecta log_message ao painel local também
        self.log_message.connect(self._append_log)

        # ── Botões ────────────────────────────────────────────────────── #
        btn_row = QHBoxLayout()

        self._btn_prepare = QPushButton("⚙️  Preparar ISO para PXE")
        self._btn_prepare.setFixedHeight(44)
        self._btn_prepare.clicked.connect(self._prepare)
        btn_row.addWidget(self._btn_prepare)

        self._btn_start_pxe = QPushButton("📡  Iniciar PXE Agora")
        self._btn_start_pxe.setObjectName("BtnPrimary")
        self._btn_start_pxe.setFixedHeight(44)
        self._btn_start_pxe.setEnabled(False)
        self._btn_start_pxe.clicked.connect(self._start_pxe)
        btn_row.addWidget(self._btn_start_pxe)

        btn_container = QWidget()
        btn_container.setLayout(btn_row)
        root.addWidget(btn_container)
        root.addStretch()

    def _browse_iso(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar ISO do Windows", "", "Imagens ISO (*.iso)"
        )
        if path:
            self._txt_iso.setText(path)
            self._txt_version.setText(Path(path).stem[:40])

    def _build_config(self) -> UnattendConfig:
        cfg = UnattendConfig()
        cfg.username = self._txt_username.text().strip() or "usuario"
        cfg.password = self._txt_password.text()
        cfg.computer_name = "*"
        cfg.disk_index = self._cmb_disk.currentIndex()
        cfg.partition_style = "GPT" if self._cmb_partition.currentIndex() == 0 else "MBR"
        cfg.windows_edition = self._cmb_edition.currentText()
        return cfg

    def _prepare(self):
        iso = self._txt_iso.text().strip()
        if not iso or not Path(iso).exists():
            QMessageBox.warning(self, "Atenção", "Selecione uma ISO válida do Windows.")
            return

        version = self._txt_version.text().strip() or "WIN_AUTO"
        stamp = time.strftime("%H%M%S")
        work_dir = str(Path("E:/WinPE_Studio_Workspace") / f"{version}_{stamp}")
        cfg = self._build_config()

        resp = QMessageBox.question(
            self, "Confirmar",
            f"Preparar instalação automática:\n\n"
            f"ISO: {Path(iso).name}\n"
            f"Usuário: {cfg.username}  |  Disco: {cfg.disk_index} ({cfg.partition_style})\n\n"
            f"⚠️ O disco {cfg.disk_index} será FORMATADO ao instalar!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        self._btn_prepare.setEnabled(False)
        self._btn_start_pxe.setEnabled(False)
        self._progress.show()
        self._progress.setValue(0)
        self._lbl_status.setText("⏳ Preparando ISO... aguarde (pode demorar alguns minutos)")

        self._worker = PrepareInstallWorker(
            iso_path=iso, work_dir=work_dir,
            config=cfg, server_ip=self._server_ip,
        )
        self._worker.log_message.connect(self.log_message)
        self._worker.progress.connect(self._progress.setValue)
        self._worker.finished.connect(self._on_prepared)
        self._worker.start()

    @Slot(bool, str)
    def _on_prepared(self, success: bool, result: str):
        self._btn_prepare.setEnabled(True)
        self._progress.hide()

        if success:
            self._prepared_dir = result
            self._btn_start_pxe.setEnabled(True)
            self._lbl_status.setText(
                f"✅ ISO preparada!\n{result}\n\nClique em 'Iniciar PXE Agora'."
            )
            self._lbl_status.setStyleSheet(
                "background: #0D2A1A; border: 1px solid #A6E3A1; "
                "border-radius: 8px; padding: 12px; color: #A6E3A1; font-size: 12px;"
            )
            self.log_message.emit(f"✅ ISO preparada: {result}")
        else:
            self._lbl_status.setText(f"❌ Erro: {result}")
            self._lbl_status.setStyleSheet(
                "background: #2A0D0D; border: 1px solid #F38BA8; "
                "border-radius: 8px; padding: 12px; color: #F38BA8; font-size: 12px;"
            )
            QMessageBox.critical(self, "Erro", result)

    def _start_pxe(self):
        if not self._prepared_dir:
            QMessageBox.warning(
                self, "Atenção",
                "Prepare a ISO primeiro!\n\n"
                "Clique em '⚙️ Preparar ISO para PXE' antes de iniciar o servidor."
            )
            return
        self.request_start_pxe.emit(self._prepared_dir)
        self._lbl_status.setText(
            "📡 Servidor PXE iniciado!\n"
            "Ligue os notebooks — eles instalarão o Windows automaticamente."
        )
        self._lbl_status.setStyleSheet(
            "background: #0D1A2A; border: 1px solid #2E6BE6; "
            "border-radius: 8px; padding: 12px; color: #2E6BE6; font-size: 12px;"
        )
