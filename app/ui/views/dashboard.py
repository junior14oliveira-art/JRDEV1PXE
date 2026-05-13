"""Dashboard — tela inicial: abrir ISO e ver status do projeto."""
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QFileDialog, QSizePolicy, QMessageBox,
)

from app.core.system_checker import detect_system
from app.utils.disk_utils import get_free_space_gb


class DashboardView(QWidget):
    iso_selected = Signal(str)   # caminho da ISO escolhida

    def __init__(self):
        super().__init__()
        self._status = None
        self._setup_ui()
        self._load_status()

    # ──────────────────────────────────────────────────────────────────── #
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(24)

        # ── Cabeçalho ────────────────────────────────────────────────── #
        title = QLabel("WinPE Studio")
        title.setObjectName("PageTitle")
        sub = QLabel("Editor de imagens Windows PE — simples e direto.")
        sub.setObjectName("PageSubtitle")
        root.addWidget(title)
        root.addWidget(sub)

        # ── Botão principal ───────────────────────────────────────────── #
        row_actions = QHBoxLayout()
        row_actions.setSpacing(12)
        
        btn_open = QPushButton("📂  Abrir ISO do WinPE")
        btn_open.setObjectName("BtnPrimary")
        btn_open.setFixedHeight(52)
        btn_open.setMinimumWidth(260)
        btn_open.clicked.connect(self._browse_iso)
        row_actions.addWidget(btn_open)

        btn_cleanup = QPushButton("🧹  Limpar Workspace")
        btn_cleanup.setFixedHeight(52)
        btn_cleanup.setMinimumWidth(200)
        btn_cleanup.clicked.connect(self._on_cleanup_workspace)
        row_actions.addWidget(btn_cleanup)
        row_actions.addStretch()
        
        root.addLayout(row_actions)

        # ── Cards de status ───────────────────────────────────────────── #
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        self._card_dism = self._make_card("DISM", "Verificando…")
        self._card_adk  = self._make_card("ADK / oscdimg", "Verificando…")
        self._card_disk = self._make_card("Disco Livre (E:)", "Verificando…")
        self._card_admin = self._make_card("Permissões", "Verificando…")

        for card in (self._card_dism, self._card_adk, self._card_disk, self._card_admin):
            cards_row.addWidget(card["frame"])

        cards_row.addStretch()
        root.addLayout(cards_row)
        root.addStretch()

    # ──────────────────────────────────────────────────────────────────── #
    def _make_card(self, label: str, value: str) -> dict:
        frame = QFrame()
        frame.setObjectName("StatusCard")
        frame.setFixedSize(180, 90)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        lbl = QLabel(label)
        lbl.setObjectName("CardLabel")
        val = QLabel(value)
        val.setObjectName("CardValue")
        layout.addWidget(lbl)
        layout.addWidget(val)
        return {"frame": frame, "value_lbl": val}

    def _set_card(self, card: dict, text: str, ok: bool):
        card["value_lbl"].setText(text)
        color = "#A6E3A1" if ok else "#F38BA8"
        card["value_lbl"].setStyleSheet(f"color: {color}; font-weight: bold;")

    # ──────────────────────────────────────────────────────────────────── #
    def _load_status(self):
        try:
            s = detect_system()
            self._set_card(self._card_dism,  "✔ Disponível" if s.dism_found else "✘ Não encontrado", s.dism_found)
            self._set_card(self._card_adk,   "✔ Disponível" if s.oscdimg_found else "⚠ Ausente", s.oscdimg_found)
            self._set_card(self._card_disk,  f"{get_free_space_gb('E:\\')} GB livres", True)
            self._set_card(self._card_admin, "✔ Admin" if s.is_admin else "⚠ Sem admin", s.is_admin)
        except Exception:
            pass  # offline / sem WMI — não bloqueia

    # ──────────────────────────────────────────────────────────────────── #
    def _browse_iso(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar ISO do WinPE", "E:\\",
            "Imagens ISO (*.iso);;Todos (*.*)"
        )
        if path:
            self.iso_selected.emit(path)

    def _on_cleanup_workspace(self):
        import shutil
        work_dir = Path("E:/WinPE_Studio_Workspace")
        if not work_dir.exists():
            QMessageBox.information(self, "Limpar", "Pasta de trabalho já está vazia.")
            return
            
        resp = QMessageBox.question(
            self, "Confirmar Limpeza",
            f"Isso removerá TODOS os arquivos temporários em:\n{work_dir}\n\nDeseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            try:
                shutil.rmtree(work_dir)
                QMessageBox.information(self, "Sucesso", "Pasta de trabalho limpa.")
            except Exception as e:
                QMessageBox.warning(self, "Erro", f"Não foi possível limpar tudo. Arquivos podem estar em uso.\n\nErro: {e}")
