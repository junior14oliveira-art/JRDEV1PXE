"""View de geração de ISO — reconstruir e salvar."""
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFileDialog,
    QGroupBox, QFormLayout, QProgressBar, QMessageBox,
)

from app.workers.build_worker import BuildIsoWorker


class BuildView(QWidget):
    log_message = Signal(str)

    def __init__(self):
        super().__init__()
        self._source_dir = ""
        self._oscdimg_path = "oscdimg"
        self._worker: BuildIsoWorker | None = None
        self._setup_ui()

    # ──────────────────────────────────────────────────────────────────── #
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(20)

        title = QLabel("⚙️  Gerar Nova ISO")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        sub = QLabel("Reembala a pasta de trabalho em uma ISO bootável.")
        sub.setObjectName("PageSubtitle")
        root.addWidget(sub)

        # ── Grupo de configurações ────────────────────────────────────── #
        grp = QGroupBox("Configurações")
        form = QFormLayout(grp)
        form.setSpacing(12)

        # Pasta fonte (preenchida automaticamente)
        self._txt_source = QLineEdit()
        self._txt_source.setPlaceholderText("Preenchido automaticamente ao abrir ISO…")
        self._txt_source.setReadOnly(True)
        form.addRow("Pasta do WinPE:", self._txt_source)

        # Destino da ISO
        dest_row = QHBoxLayout()
        self._txt_dest = QLineEdit()
        self._txt_dest.setPlaceholderText("E:\\WinPE_Custom.iso")
        btn_browse = QPushButton("…")
        btn_browse.setFixedWidth(36)
        btn_browse.clicked.connect(self._browse_dest)
        dest_row.addWidget(self._txt_dest)
        dest_row.addWidget(btn_browse)
        form.addRow("Salvar ISO em:", dest_row)

        # Versão
        self._txt_version = QLineEdit("1.0")
        self._txt_version.setFixedWidth(60)
        self._txt_version.textChanged.connect(self._update_suggested_name)
        form.addRow("Versão do Projeto:", self._txt_version)
        
        # Label do volume
        self._txt_label = QLineEdit("WINPE_CUSTOM")
        self._txt_label.setMaxLength(32)
        form.addRow("Label do volume:", self._txt_label)

        root.addWidget(grp)

        # ── Progresso ─────────────────────────────────────────────────── #
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(True)
        root.addWidget(self._progress)

        self._lbl_status = QLabel("")
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._lbl_status)

        # ── Botão ─────────────────────────────────────────────────────── #
        self._btn_build = QPushButton("🔨  Gerar ISO Agora")
        self._btn_build.setObjectName("BtnPrimary")
        self._btn_build.setFixedHeight(48)
        self._btn_build.clicked.connect(self._start_build)
        root.addWidget(self._btn_build)

        root.addStretch()

    # ──────────────────────────────────────────────────────────────────── #
    def set_source(self, path: str):
        self._source_dir = path
        self._txt_source.setText(path)
        self._update_suggested_name()

    def _update_suggested_name(self):
        if not self._source_dir:
            return
        base = Path(self._source_dir)
        ver = self._txt_version.text().strip().replace(".", "_")
        # Sufixo _NET indica que tem drivers de rede injetados
        default_out = str(base.parent / f"{base.name}_NET_v{ver}.iso")
        self._txt_dest.setText(default_out)

    def set_oscdimg_path(self, path: str):
        if path:
            self._oscdimg_path = path

    def _browse_dest(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar ISO como", self._txt_dest.text(),
            "Imagem ISO (*.iso)"
        )
        if path:
            self._txt_dest.setText(path)

    # ──────────────────────────────────────────────────────────────────── #
    def _start_build(self):
        source = self._txt_source.text().strip()
        dest = self._txt_dest.text().strip()

        if not source:
            QMessageBox.warning(self, "Atenção", "Abra uma ISO primeiro na tela de Início.")
            return
        if not dest:
            QMessageBox.warning(self, "Atenção", "Informe o caminho de saída da ISO.")
            return

        self._btn_build.setEnabled(False)
        self._progress.setValue(0)
        self._lbl_status.setText("Construindo ISO…")

        self._worker = BuildIsoWorker(
            source_dir=source,
            output_iso=dest,
            oscdimg_path=self._oscdimg_path,
            volume_label=self._txt_label.text().strip() or "WINPE_CUSTOM",
        )
        self._worker.log_message.connect(self.log_message)
        self._worker.progress.connect(self._progress.setValue)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_finished(self, success: bool, msg: str):
        self._btn_build.setEnabled(True)
        self._lbl_status.setText(msg)
        if success:
            self._progress.setValue(100)
            QMessageBox.information(self, "Concluído", msg)
        else:
            QMessageBox.critical(self, "Erro", msg)
