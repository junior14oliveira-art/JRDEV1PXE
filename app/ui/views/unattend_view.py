"""View de Instalação Automática — gera autounattend.xml e ISO completa."""
import os
from pathlib import Path
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QGroupBox, QFormLayout,
    QMessageBox, QFileDialog, QProgressBar, QTextEdit,
)
from app.core.unattend_service import UnattendConfig, generate_autounattend, inject_autounattend
from app.workers.build_worker import BuildIsoWorker


class UnattendView(QWidget):
    log_message = Signal(str)

    def __init__(self):
        super().__init__()
        self._work_dir = ""
        self._oscdimg_path = "oscdimg"
        self._worker = None
        self._setup_ui()

    def set_oscdimg_path(self, path: str):
        if path:
            self._oscdimg_path = path

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(20)

        title = QLabel("🖥️  Instalação Automática do Windows")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        sub = QLabel(
            "Gera um autounattend.xml e a ISO final completa — pronta para instalar\n"
            "o Windows sem nenhuma interação. Formata, instala, cria usuário e reinicia."
        )
        sub.setObjectName("PageSubtitle")
        root.addWidget(sub)

        # ── Configuração do Usuário ───────────────────────────────────── #
        grp_user = QGroupBox("👤 Conta de Usuário")
        form_user = QFormLayout(grp_user)
        form_user.setSpacing(12)

        self._txt_username = QLineEdit("usuario")
        self._txt_username.setPlaceholderText("Nome do usuário")
        form_user.addRow("Usuário:", self._txt_username)

        self._txt_password = QLineEdit()
        self._txt_password.setPlaceholderText("Deixe em branco para sem senha")
        self._txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        form_user.addRow("Senha:", self._txt_password)

        self._txt_computer = QLineEdit("*")
        self._txt_computer.setPlaceholderText("* = gerado automaticamente pelo Windows")
        form_user.addRow("Nome do PC:", self._txt_computer)

        root.addWidget(grp_user)

        # ── Configuração do Disco ─────────────────────────────────────── #
        grp_disk = QGroupBox("💾 Configuração do Disco")
        form_disk = QFormLayout(grp_disk)
        form_disk.setSpacing(12)

        self._cmb_disk = QComboBox()
        self._cmb_disk.addItems(["Disco 0 (primeiro disco)", "Disco 1", "Disco 2"])
        form_disk.addRow("Disco alvo:", self._cmb_disk)

        self._cmb_partition = QComboBox()
        self._cmb_partition.addItems([
            "GPT — UEFI (recomendado para notebooks modernos)",
            "MBR — BIOS Legacy (notebooks antigos)",
        ])
        form_disk.addRow("Tipo de partição:", self._cmb_partition)

        self._cmb_edition = QComboBox()
        self._cmb_edition.addItems(["Professional", "Home", "Enterprise", "Education"])
        form_disk.addRow("Edição do Windows:", self._cmb_edition)

        lbl_aviso = QLabel(
            "⚠️  <b>ATENÇÃO:</b> O disco selecionado será completamente formatado!\n"
            "Todos os dados serão apagados sem confirmação."
        )
        lbl_aviso.setStyleSheet(
            "color: #FAB387; background: #1A2A1A; border: 1px solid #FAB387; "
            "border-radius: 6px; padding: 8px;"
        )
        lbl_aviso.setWordWrap(True)
        form_disk.addRow(lbl_aviso)
        root.addWidget(grp_disk)

        # ── Destino ───────────────────────────────────────────────────── #
        grp_dest = QGroupBox("📁 Destino")
        form_dest = QFormLayout(grp_dest)
        form_dest.setSpacing(12)

        dest_row = QHBoxLayout()
        self._txt_dest = QLineEdit()
        self._txt_dest.setPlaceholderText("Pasta raiz da ISO extraída")
        dest_row.addWidget(self._txt_dest)
        btn_browse = QPushButton("📂")
        btn_browse.setFixedWidth(36)
        btn_browse.clicked.connect(self._browse_dest)
        dest_row.addWidget(btn_browse)
        form_dest.addRow("Pasta da ISO:", dest_row)

        # Saída da ISO final
        iso_row = QHBoxLayout()
        self._txt_iso_out = QLineEdit()
        self._txt_iso_out.setPlaceholderText("E:\\Windows_Auto.iso")
        iso_row.addWidget(self._txt_iso_out)
        btn_iso = QPushButton("📂")
        btn_iso.setFixedWidth(36)
        btn_iso.clicked.connect(self._browse_iso_out)
        iso_row.addWidget(btn_iso)
        form_dest.addRow("ISO de saída:", iso_row)

        root.addWidget(grp_dest)

        # ── Progresso ─────────────────────────────────────────────────── #
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.hide()
        root.addWidget(self._progress)

        self._lbl_status = QLabel("")
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_status.setStyleSheet("color: #7A9CC8; font-size: 12px;")
        root.addWidget(self._lbl_status)

        # ── Botões ────────────────────────────────────────────────────── #
        btn_row = QHBoxLayout()

        self._btn_preview = QPushButton("👁️  Visualizar XML")
        self._btn_preview.clicked.connect(self._preview_xml)
        btn_row.addWidget(self._btn_preview)

        self._btn_generate = QPushButton("⚡  Gerar XML + ISO Completa")
        self._btn_generate.setObjectName("BtnPrimary")
        self._btn_generate.setFixedHeight(44)
        self._btn_generate.clicked.connect(self._generate_all)
        btn_row.addWidget(self._btn_generate)

        btn_container = QWidget()
        btn_container.setLayout(btn_row)
        root.addWidget(btn_container)

        root.addStretch()

    def set_project(self, work_dir: str):
        self._work_dir = work_dir
        self._txt_dest.setText(work_dir)
        # Sugere nome da ISO de saída
        base = Path(work_dir)
        iso_out = str(base.parent / f"{base.name}_AUTO.iso")
        self._txt_iso_out.setText(iso_out)

    def _browse_dest(self):
        d = QFileDialog.getExistingDirectory(self, "Selecionar pasta raiz da ISO")
        if d:
            self._txt_dest.setText(d)
            base = Path(d)
            self._txt_iso_out.setText(str(base.parent / f"{base.name}_AUTO.iso"))

    def _browse_iso_out(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar ISO como", self._txt_iso_out.text(), "Imagem ISO (*.iso)"
        )
        if path:
            self._txt_iso_out.setText(path)

    def _build_config(self) -> UnattendConfig:
        cfg = UnattendConfig()
        cfg.username = self._txt_username.text().strip() or "usuario"
        cfg.password = self._txt_password.text()
        cfg.computer_name = self._txt_computer.text().strip() or "*"
        cfg.disk_index = self._cmb_disk.currentIndex()
        cfg.partition_style = "GPT" if self._cmb_partition.currentIndex() == 0 else "MBR"
        cfg.windows_edition = self._cmb_edition.currentText()
        return cfg

    def _preview_xml(self):
        import tempfile
        cfg = self._build_config()
        tmp = Path(tempfile.mktemp(suffix=".xml"))
        generate_autounattend(cfg, tmp)
        xml_content = tmp.read_text(encoding="utf-8")
        tmp.unlink(missing_ok=True)
        dlg = _XmlPreviewDialog(xml_content, self)
        dlg.exec()

    def _generate_all(self):
        """Gera o autounattend.xml E a ISO completa em sequência."""
        dest = self._txt_dest.text().strip()
        iso_out = self._txt_iso_out.text().strip()

        if not dest:
            QMessageBox.warning(self, "Atenção", "Selecione a pasta da ISO primeiro.")
            return
        if not iso_out:
            QMessageBox.warning(self, "Atenção", "Informe o caminho da ISO de saída.")
            return

        cfg = self._build_config()

        # Confirmação
        msg = (
            f"Isso vai:\n\n"
            f"1. Gerar autounattend.xml em:\n   {dest}\n\n"
            f"2. Gerar a ISO final em:\n   {iso_out}\n\n"
            f"Usuário: {cfg.username}  |  Senha: {'(sem senha)' if not cfg.password else '***'}\n"
            f"Disco: {cfg.disk_index} ({cfg.partition_style})  |  Edição: {cfg.windows_edition}\n\n"
            f"⚠️ O disco {cfg.disk_index} será FORMATADO ao instalar!"
        )
        resp = QMessageBox.question(
            self, "Confirmar", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        # ── Passo 1: Gera autounattend.xml ───────────────────────────── #
        self._btn_generate.setEnabled(False)
        self._progress.show()
        self._progress.setValue(5)
        self._lbl_status.setText("📝 Gerando autounattend.xml...")
        self.log_message.emit("📝 Gerando autounattend.xml...")

        ok, result = inject_autounattend(dest, cfg)
        if not ok:
            self._btn_generate.setEnabled(True)
            self._progress.hide()
            self._lbl_status.setText("")
            QMessageBox.critical(self, "Erro", f"Falha ao gerar XML:\n{result}")
            return

        self.log_message.emit(f"✅ autounattend.xml gerado: {result}")
        self._progress.setValue(15)
        self._lbl_status.setText("⚙️ Gerando ISO final... (pode demorar alguns minutos)")
        self.log_message.emit("⚙️ Iniciando geração da ISO...")

        # ── Passo 2: Gera a ISO ───────────────────────────────────────── #
        self._worker = BuildIsoWorker(
            source_dir=dest,
            output_iso=iso_out,
            oscdimg_path=self._oscdimg_path,
            volume_label="WIN_AUTO",
        )
        self._worker.log_message.connect(self.log_message)
        self._worker.progress.connect(self._on_build_progress)
        self._worker.finished.connect(self._on_build_done)
        self._worker.start()

    @Slot(int)
    def _on_build_progress(self, value: int):
        # Mapeia 0-100 do worker para 15-100 da barra (15% já usado pelo XML)
        mapped = 15 + int(value * 0.85)
        self._progress.setValue(mapped)

    @Slot(bool, str)
    def _on_build_done(self, success: bool, msg: str):
        self._btn_generate.setEnabled(True)
        self._progress.setValue(100 if success else 0)
        self._lbl_status.setText(msg)

        if success:
            iso_out = self._txt_iso_out.text()
            size_gb = 0
            try:
                size_gb = round(Path(iso_out).stat().st_size / (1024**3), 2)
            except Exception:
                pass

            self.log_message.emit(f"✅ ISO gerada: {iso_out} ({size_gb} GB)")
            QMessageBox.information(
                self, "✅ Concluído!",
                f"ISO gerada com sucesso!\n\n"
                f"Arquivo: {iso_out}\n"
                f"Tamanho: {size_gb} GB\n\n"
                f"Esta ISO instala o Windows automaticamente:\n"
                f"• Formata o disco {self._cmb_disk.currentIndex()}\n"
                f"• Cria usuário: {self._txt_username.text()}\n"
                f"• Sem nenhuma interação necessária"
            )
        else:
            self.log_message.emit(f"❌ Erro: {msg}")
            QMessageBox.critical(self, "Erro na geração da ISO", msg)


# ── Diálogo de preview do XML ─────────────────────────────────────────────── #
from PySide6.QtWidgets import QDialog, QDialogButtonBox

class _XmlPreviewDialog(QDialog):
    def __init__(self, xml: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preview — autounattend.xml")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setPlainText(xml)
        txt.setStyleSheet(
            "font-family: 'Cascadia Code', 'Consolas', monospace; "
            "font-size: 12px; background: #060E1F; color: #5DADE2; "
            "border: 1px solid #1A3A6B;"
        )
        layout.addWidget(txt)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)


class UnattendView(QWidget):
    log_message = Signal(str)

    def __init__(self):
        super().__init__()
        self._work_dir = ""
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(20)

        title = QLabel("🖥️  Instalação Automática do Windows")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        sub = QLabel(
            "Gera um autounattend.xml que instala o Windows sem nenhuma interação.\n"
            "Formata o disco, instala, cria usuário e reinicia automaticamente."
        )
        sub.setObjectName("PageSubtitle")
        root.addWidget(sub)

        # ── Configuração do Usuário ───────────────────────────────────── #
        grp_user = QGroupBox("👤 Conta de Usuário")
        form_user = QFormLayout(grp_user)
        form_user.setSpacing(12)

        self._txt_username = QLineEdit("usuario")
        self._txt_username.setPlaceholderText("Nome do usuário (ex: usuario, tecnico, admin)")
        form_user.addRow("Usuário:", self._txt_username)

        self._txt_password = QLineEdit()
        self._txt_password.setPlaceholderText("Deixe em branco para sem senha")
        self._txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        form_user.addRow("Senha:", self._txt_password)

        self._txt_computer = QLineEdit("*")
        self._txt_computer.setPlaceholderText("* = gerado automaticamente pelo Windows")
        form_user.addRow("Nome do PC:", self._txt_computer)

        root.addWidget(grp_user)

        # ── Configuração do Disco ─────────────────────────────────────── #
        grp_disk = QGroupBox("💾 Configuração do Disco")
        form_disk = QFormLayout(grp_disk)
        form_disk.setSpacing(12)

        self._cmb_disk = QComboBox()
        self._cmb_disk.addItems(["Disco 0 (primeiro disco)", "Disco 1", "Disco 2"])
        form_disk.addRow("Disco alvo:", self._cmb_disk)

        self._cmb_partition = QComboBox()
        self._cmb_partition.addItems([
            "GPT — UEFI (recomendado para notebooks modernos)",
            "MBR — BIOS Legacy (notebooks antigos)",
        ])
        form_disk.addRow("Tipo de partição:", self._cmb_partition)

        self._cmb_edition = QComboBox()
        self._cmb_edition.addItems([
            "Professional",
            "Home",
            "Enterprise",
            "Education",
        ])
        form_disk.addRow("Edição do Windows:", self._cmb_edition)

        lbl_aviso = QLabel(
            "⚠️  <b>ATENÇÃO:</b> O disco selecionado será completamente formatado!\n"
            "Todos os dados serão apagados sem confirmação."
        )
        lbl_aviso.setStyleSheet(
            "color: #FAB387; background: #1A2A1A; border: 1px solid #FAB387; "
            "border-radius: 6px; padding: 8px;"
        )
        lbl_aviso.setWordWrap(True)
        form_disk.addRow(lbl_aviso)

        root.addWidget(grp_disk)

        # ── Destino ───────────────────────────────────────────────────── #
        grp_dest = QGroupBox("📁 Destino")
        form_dest = QFormLayout(grp_dest)
        form_dest.setSpacing(12)

        dest_row = QHBoxLayout()
        self._txt_dest = QLineEdit()
        self._txt_dest.setPlaceholderText("Pasta raiz da ISO extraída (onde ficará o autounattend.xml)")
        dest_row.addWidget(self._txt_dest)
        btn_browse = QPushButton("📂")
        btn_browse.setFixedWidth(36)
        btn_browse.clicked.connect(self._browse_dest)
        dest_row.addWidget(btn_browse)
        form_dest.addRow("Pasta da ISO:", dest_row)

        root.addWidget(grp_dest)

        # ── Botões ────────────────────────────────────────────────────── #
        btn_row = QHBoxLayout()

        self._btn_preview = QPushButton("👁️  Visualizar XML")
        self._btn_preview.clicked.connect(self._preview_xml)
        btn_row.addWidget(self._btn_preview)

        self._btn_generate = QPushButton("⚡  Gerar e Injetar na ISO")
        self._btn_generate.setObjectName("BtnPrimary")
        self._btn_generate.setFixedHeight(44)
        self._btn_generate.clicked.connect(self._generate)
        btn_row.addWidget(self._btn_generate)

        root.addWidget(QWidget())  # spacer
        btn_container = QWidget()
        btn_container.setLayout(btn_row)
        root.addWidget(btn_container)

        root.addStretch()

    def set_project(self, work_dir: str):
        """Chamado quando uma ISO é carregada — preenche o destino automaticamente."""
        self._work_dir = work_dir
        self._txt_dest.setText(work_dir)

    def _browse_dest(self):
        d = QFileDialog.getExistingDirectory(self, "Selecionar pasta raiz da ISO")
        if d:
            self._txt_dest.setText(d)

    def _build_config(self) -> UnattendConfig:
        cfg = UnattendConfig()
        cfg.username = self._txt_username.text().strip() or "usuario"
        cfg.password = self._txt_password.text()
        cfg.computer_name = self._txt_computer.text().strip() or "*"
        cfg.disk_index = self._cmb_disk.currentIndex()
        cfg.partition_style = "GPT" if self._cmb_partition.currentIndex() == 0 else "MBR"
        cfg.windows_edition = self._cmb_edition.currentText()
        return cfg

    def _preview_xml(self):
        """Mostra o XML que será gerado sem salvar."""
        import tempfile
        cfg = self._build_config()
        tmp = Path(tempfile.mktemp(suffix=".xml"))
        generate_autounattend(cfg, tmp)
        xml_content = tmp.read_text(encoding="utf-8")
        tmp.unlink(missing_ok=True)

        dlg = _XmlPreviewDialog(xml_content, self)
        dlg.exec()

    def _generate(self):
        dest = self._txt_dest.text().strip()
        if not dest:
            QMessageBox.warning(self, "Atenção", "Selecione a pasta da ISO primeiro.")
            return

        cfg = self._build_config()

        # Confirmação
        msg = (
            f"Gerar autounattend.xml em:\n{dest}\n\n"
            f"Usuário: {cfg.username}\n"
            f"Senha: {'(sem senha)' if not cfg.password else '***'}\n"
            f"Disco: {cfg.disk_index} ({cfg.partition_style})\n"
            f"Edição: {cfg.windows_edition}\n\n"
            f"⚠️ O disco {cfg.disk_index} será FORMATADO ao instalar!"
        )
        resp = QMessageBox.question(
            self, "Confirmar Geração", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        ok, result = inject_autounattend(dest, cfg)
        if ok:
            self.log_message.emit(f"✅ autounattend.xml gerado: {result}")
            QMessageBox.information(
                self, "Sucesso",
                f"✅ autounattend.xml gerado com sucesso!\n\n"
                f"Arquivo: {result}\n\n"
                f"Agora gere a ISO normalmente — o Windows instalará\n"
                f"automaticamente ao dar boot nesta ISO."
            )
        else:
            self.log_message.emit(f"❌ Erro: {result}")
            QMessageBox.critical(self, "Erro", result)


# ── Diálogo de preview do XML ─────────────────────────────────────────────── #
from PySide6.QtWidgets import QDialog, QDialogButtonBox

class _XmlPreviewDialog(QDialog):
    def __init__(self, xml: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preview — autounattend.xml")
        self.resize(800, 600)
        layout = QVBoxLayout(self)

        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setPlainText(xml)
        txt.setStyleSheet(
            "font-family: 'Cascadia Code', 'Consolas', monospace; "
            "font-size: 12px; "
            "background: #060E1F; "
            "color: #5DADE2; "
            "border: 1px solid #1A3A6B;"
        )
        layout.addWidget(txt)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
