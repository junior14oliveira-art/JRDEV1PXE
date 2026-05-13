"""View para obter uma imagem base do Windows PE (Download ou Geração Local)."""
import os
from pathlib import Path
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QMessageBox, QGroupBox, QListWidget, QListWidgetItem,
    QRadioButton, QButtonGroup
)
from app.workers.download_worker import DownloadWorker
from app.workers.generator_worker import GeneratorWorker

# Links de fallback (Se o usuário preferir baixar)
FALLBACK_LINKS = [
    {
        "name": "Hiren's BootCD PE (x64) - Estável",
        "url": "https://www.hirensbootcd.org/files/HBCD_PE_x64.iso",
        "desc": "Base ultra estável e compatível. Ótima para começar."
    },
    {
        "name": "Win10XPE Base (x64) - Limpa",
        "url": "https://github.com/ChrisRfr/Win10XPE/releases/download/v2023-01-20/Win10XPE_x64.iso",
        "desc": "Imagem baseada no projeto Win10XPE. Muito rápida."
    }
]

class DownloadView(QWidget):
    log_message = Signal(str)
    iso_downloaded = Signal(str) # Avisa o dashboard que a ISO está pronta

    def __init__(self):
        super().__init__()
        self._worker = None
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(24)

        title = QLabel("📦  Obter WinPE Base Original")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        sub = QLabel("Escolha como obter um Windows PE limpo para seu projeto.")
        sub.setObjectName("PageSubtitle")
        root.addWidget(sub)

        # ── Opção 1: Geração via ADK (Recomendado) ────────────────────── #
        grp_gen = QGroupBox("🚀  Opção 1: Gerar Localmente (Recomendado)")
        layout_gen = QVBoxLayout(grp_gen)
        
        lbl_gen = QLabel("Usa o Windows ADK instalado no seu PC para criar uma ISO 100% original.\n"
                         "⚠️ REQUER o 'Windows PE Add-on' instalado separadamente no ADK.")
        lbl_gen.setWordWrap(True)
        lbl_gen.setStyleSheet("color: #fab387;") # Yellowish
        layout_gen.addWidget(lbl_gen)

        row_adk = QHBoxLayout()
        self._btn_generate = QPushButton("🔨  Gerar WinPE Original Agora")
        self._btn_generate.setObjectName("BtnPrimary")
        self._btn_generate.setFixedHeight(50)
        self._btn_generate.clicked.connect(self._start_generation)
        row_adk.addWidget(self._btn_generate, stretch=2)

        self._btn_adk_link = QPushButton("🌐  Baixar PE Add-on (Microsoft)")
        self._btn_adk_link.clicked.connect(self._open_adk_link)
        row_adk.addWidget(self._btn_adk_link, stretch=1)
        layout_gen.addLayout(row_adk)
        
        root.addWidget(grp_gen)

        # ── Opção 2: Download ────────────────────────────────────────── #
        grp_dl = QGroupBox("📥  Opção 2: Baixar da Internet")
        layout_dl = QVBoxLayout(grp_dl)
        
        self._list_dl = QListWidget()
        for img in FALLBACK_LINKS:
            item = QListWidgetItem(f"{img['name']}\n{img['desc']}")
            item.setData(Qt.ItemDataRole.UserRole, img['url'])
            self._list_dl.addItem(item)
        
        layout_dl.addWidget(self._list_dl)

        self._btn_download = QPushButton("⬇️  Baixar Imagem Selecionada")
        self._btn_download.clicked.connect(self._start_download)
        layout_dl.addWidget(self._btn_download)
        
        root.addWidget(grp_dl)

        # ── Progresso ─────────────────────────────────────────────────── #
        self._progress = QProgressBar()
        self._progress.hide()
        root.addWidget(self._progress)

        self._lbl_status = QLabel("")
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._lbl_status)

        root.addStretch()

    def _start_generation(self):
        dest_iso = "E:/WinPE_Original_Gerado.iso"
        
        self._set_ui_busy(True)
        self._lbl_status.setText("Gerando WinPE via ADK... Isso pode levar 2-3 minutos.")

        self._worker = GeneratorWorker(dest_iso)
        self._worker.log_message.connect(self.log_message)
        self._worker.progress.connect(self._progress.setValue)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _start_download(self):
        item = self._list_dl.currentItem()
        if not item:
            QMessageBox.warning(self, "Atenção", "Selecione uma imagem para baixar.")
            return

        url = item.data(Qt.ItemDataRole.UserRole)
        name = item.text().split("\n")[0].replace(" ", "_")
        dest_path = f"E:/{name}.iso"

        self._set_ui_busy(True)
        self._lbl_status.setText(f"Baixando {name}...")

        from app.workers.download_worker import DownloadWorker
        self._worker = DownloadWorker(url, dest_path)
        self._worker.log_message.connect(self.log_message)
        self._worker.progress.connect(self._progress.setValue)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _set_ui_busy(self, busy: bool):
        self._btn_generate.setEnabled(not busy)
        self._btn_download.setEnabled(not busy)
        if busy:
            self._progress.show()
            self._progress.setValue(0)
        else:
            self._progress.hide()
            self._lbl_status.setText("")

    def _on_finished(self, success: bool, msg: str):
        self._set_ui_busy(False)
        if success:
            dest = msg.split(": ")[-1].strip()
            QMessageBox.information(self, "Sucesso", f"Operação concluída!\n\nArquivo salvo em: {dest}")
            self.iso_downloaded.emit(dest)
        else:
            QMessageBox.critical(self, "Erro", msg)

    def _open_adk_link(self):
        import webbrowser
        webbrowser.open("https://learn.microsoft.com/en-us/windows-hardware/get-started/adk-install#download-the-winpe-add-on-for-the-windows-adk")
