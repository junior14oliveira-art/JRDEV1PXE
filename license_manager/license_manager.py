"""
WinPE Studio — Painel Admin de Licenças
Uso exclusivo do desenvolvedor para gerar e gerenciar licenças.

Execute: python license_manager.py
"""
import json
import sys
import os
from datetime import date, datetime, timedelta
from pathlib import Path

# Adiciona o diretório pai ao path para importar license_service
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem, QFont, QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QTableView,
    QGroupBox, QFormLayout, QMessageBox, QHeaderView,
    QFrame, QStatusBar, QDialog, QDialogButtonBox, QTextEdit,
)
from app.core.license_service import generate_license_key, _SECRET

# Arquivo local de registro de licenças emitidas
_DB_FILE = Path(__file__).parent / "licenses.json"


# ══════════════════════════════════════════════════════════════════════════ #
#  Banco de licenças (JSON local)                                            #
# ══════════════════════════════════════════════════════════════════════════ #

def _load_db() -> list[dict]:
    if _DB_FILE.exists():
        try:
            return json.loads(_DB_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_db(records: list[dict]):
    _DB_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


def _add_record(record: dict):
    records = _load_db()
    records.append(record)
    _save_db(records)


# ══════════════════════════════════════════════════════════════════════════ #
#  Janela principal                                                          #
# ══════════════════════════════════════════════════════════════════════════ #

STYLE = """
QMainWindow, QWidget, QDialog {
    background-color: #1E1E2E;
    color: #CDD6F4;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #313244;
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px;
    font-weight: bold;
    color: #89B4FA;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
}
QLineEdit, QComboBox, QTextEdit {
    background-color: #313244;
    border: 1px solid #45475A;
    border-radius: 6px;
    padding: 8px 12px;
    color: #CDD6F4;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #89B4FA;
}
QPushButton {
    background-color: #313244;
    color: #CDD6F4;
    border: 1px solid #45475A;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
}
QPushButton:hover { background-color: #45475A; }
QPushButton#BtnGenerate {
    background-color: #A6E3A1;
    color: #11111B;
    border: none;
    font-size: 14px;
    padding: 10px 24px;
}
QPushButton#BtnGenerate:hover { background-color: #94E2D5; }
QPushButton#BtnRevoke {
    background-color: #F38BA8;
    color: #11111B;
    border: none;
}
QPushButton#BtnRevoke:hover { background-color: #EBA0AC; }
QTableView {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 8px;
    gridline-color: #313244;
    selection-background-color: #89B4FA;
    selection-color: #11111B;
}
QHeaderView::section {
    background-color: #313244;
    color: #A6ADC8;
    padding: 8px;
    border: none;
    font-weight: bold;
}
QStatusBar { color: #6C7086; }
"""


class LicenseManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WinPE Studio — Gerenciador de Licenças")
        self.resize(1000, 680)
        self.setStyleSheet(STYLE)
        self._setup_ui()
        self._refresh_table()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 24, 24, 16)
        root.setSpacing(16)

        # Título
        lbl = QLabel("🔑  Gerenciador de Licenças — WinPE Studio Pro")
        lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #89B4FA;")
        root.addWidget(lbl)

        # ── Painel de geração ─────────────────────────────────────────── #
        grp = QGroupBox("Gerar Nova Licença")
        form = QFormLayout(grp)
        form.setSpacing(12)

        self._txt_client = QLineEdit()
        self._txt_client.setPlaceholderText("Ex: Empresa ABC / João Silva")
        form.addRow("Cliente:", self._txt_client)

        self._txt_notes = QLineEdit()
        self._txt_notes.setPlaceholderText("Observações opcionais")
        form.addRow("Notas:", self._txt_notes)

        self._cmb_plan = QComboBox()
        self._cmb_plan.addItems([
            "3 meses  (90 dias)",
            "6 meses  (180 dias)",
            "12 meses (365 dias)",
            "24 meses (730 dias)",
        ])
        self._cmb_plan.setCurrentIndex(1)
        form.addRow("Plano:", self._cmb_plan)

        # Linha de ação
        btn_row = QHBoxLayout()
        self._btn_gen = QPushButton("⚡  Gerar Licença")
        self._btn_gen.setObjectName("BtnGenerate")
        self._btn_gen.clicked.connect(self._generate)
        btn_row.addWidget(self._btn_gen)
        btn_row.addStretch()
        form.addRow("", btn_row)

        root.addWidget(grp)

        # ── Tabela de licenças ────────────────────────────────────────── #
        grp2 = QGroupBox("Licenças Emitidas")
        v2 = QVBoxLayout(grp2)

        # Barra de busca
        search_row = QHBoxLayout()
        self._txt_search = QLineEdit()
        self._txt_search.setPlaceholderText("🔍  Buscar por cliente, chave ou status...")
        self._txt_search.textChanged.connect(self._on_search)
        search_row.addWidget(self._txt_search)

        btn_refresh = QPushButton("↻  Atualizar")
        btn_refresh.clicked.connect(self._refresh_table)
        search_row.addWidget(btn_refresh)

        btn_revoke = QPushButton("🚫  Revogar Selecionada")
        btn_revoke.setObjectName("BtnRevoke")
        btn_revoke.clicked.connect(self._revoke_selected)
        search_row.addWidget(btn_revoke)

        v2.addLayout(search_row)

        # Modelo da tabela
        self._model = QStandardItemModel()
        self._model.setHorizontalHeaderLabels([
            "Cliente", "Chave", "Plano", "Emitida em", "Expira em", "Status", "Notas"
        ])

        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(-1)  # busca em todas as colunas

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("alternate-background-color: #252535;")
        self._table.doubleClicked.connect(self._show_key_dialog)
        v2.addWidget(self._table)

        root.addWidget(grp2, stretch=1)

        # Status bar
        self._sb = QStatusBar()
        self.setStatusBar(self._sb)
        self._sb.showMessage("Pronto.")

    # ── Geração ──────────────────────────────────────────────────────── #

    def _generate(self):
        client = self._txt_client.text().strip()
        if not client:
            QMessageBox.warning(self, "Atenção", "Informe o nome do cliente.")
            return

        plan_idx = self._cmb_plan.currentIndex()
        days_map = [90, 180, 365, 730]
        days     = days_map[plan_idx]
        plan_lbl = self._cmb_plan.currentText().strip()

        expiry = date.today() + timedelta(days=days)
        key    = generate_license_key(expiry)

        record = {
            "client":   client,
            "key":      key,
            "plan":     plan_lbl,
            "issued":   date.today().isoformat(),
            "expiry":   expiry.isoformat(),
            "notes":    self._txt_notes.text().strip(),
            "revoked":  False,
        }
        _add_record(record)
        self._refresh_table()

        # Mostra a chave gerada em destaque
        self._show_generated_key(client, key, expiry, plan_lbl)

        # Limpa campos
        self._txt_client.clear()
        self._txt_notes.clear()

    def _show_generated_key(self, client: str, key: str, expiry: date, plan: str):
        dlg = QDialog(self)
        dlg.setWindowTitle("Licença Gerada")
        dlg.setMinimumWidth(480)
        dlg.setStyleSheet(STYLE)
        v = QVBoxLayout(dlg)
        v.setSpacing(16)
        v.setContentsMargins(24, 24, 24, 24)

        v.addWidget(QLabel(f"<b>✅ Licença gerada para: {client}</b>"))
        v.addWidget(QLabel(f"Plano: {plan}  |  Expira em: {expiry.strftime('%d/%m/%Y')}"))

        # Chave em destaque
        lbl_key = QLabel(key)
        lbl_key.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_key.setStyleSheet(
            "font-size: 22px; font-weight: bold; letter-spacing: 4px; "
            "color: #A6E3A1; background: #313244; border-radius: 8px; padding: 16px;"
        )
        lbl_key.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v.addWidget(lbl_key)

        v.addWidget(QLabel(
            "<small>📋 Copie esta chave e envie ao cliente.<br>"
            "O cliente cola no programa e ativa na máquina dele.<br>"
            "<b>A chave só funciona em 1 PC.</b></small>"
        ))

        btn_copy = QPushButton("📋  Copiar Chave")
        btn_copy.setObjectName("BtnGenerate")
        btn_copy.clicked.connect(lambda: (
            QApplication.clipboard().setText(key),
            btn_copy.setText("✅  Copiado!")
        ))
        v.addWidget(btn_copy)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btns.accepted.connect(dlg.accept)
        v.addWidget(btns)

        dlg.exec()

    # ── Tabela ───────────────────────────────────────────────────────── #

    def _refresh_table(self):
        self._model.removeRows(0, self._model.rowCount())
        records = _load_db()
        today   = date.today()

        for r in records:
            expiry_str = r.get("expiry", "")
            revoked    = r.get("revoked", False)

            try:
                expiry    = date.fromisoformat(expiry_str)
                days_left = (expiry - today).days
                exp_fmt   = expiry.strftime("%d/%m/%Y")
            except Exception:
                days_left = -1
                exp_fmt   = expiry_str

            if revoked:
                status = "🚫 Revogada"
                color  = QColor("#F38BA8")
            elif days_left < 0:
                status = "🔴 Expirada"
                color  = QColor("#F38BA8")
            elif days_left <= 15:
                status = f"⚠️ {days_left}d restantes"
                color  = QColor("#FAB387")
            else:
                status = f"✅ {days_left}d restantes"
                color  = QColor("#A6E3A1")

            issued_fmt = ""
            try:
                issued_fmt = date.fromisoformat(r.get("issued", "")).strftime("%d/%m/%Y")
            except Exception:
                issued_fmt = r.get("issued", "")

            row = [
                QStandardItem(r.get("client", "")),
                QStandardItem(r.get("key", "")),
                QStandardItem(r.get("plan", "")),
                QStandardItem(issued_fmt),
                QStandardItem(exp_fmt),
                QStandardItem(status),
                QStandardItem(r.get("notes", "")),
            ]
            row[5].setForeground(color)
            for item in row:
                item.setData(r, Qt.ItemDataRole.UserRole)

            self._model.appendRow(row)

        total    = len(records)
        active   = sum(1 for r in records if not r.get("revoked") and (date.fromisoformat(r["expiry"]) >= today if r.get("expiry") else False))
        expired  = sum(1 for r in records if not r.get("revoked") and (date.fromisoformat(r["expiry"]) < today if r.get("expiry") else False))
        revoked  = sum(1 for r in records if r.get("revoked"))
        self._sb.showMessage(
            f"Total: {total}  |  Ativas: {active}  |  Expiradas: {expired}  |  Revogadas: {revoked}"
        )

    def _on_search(self, text: str):
        self._proxy.setFilterFixedString(text)

    def _revoke_selected(self):
        idx = self._table.currentIndex()
        if not idx.isValid():
            QMessageBox.information(self, "Atenção", "Selecione uma licença na tabela.")
            return

        src_idx = self._proxy.mapToSource(idx)
        item    = self._model.item(src_idx.row(), 0)
        record  = item.data(Qt.ItemDataRole.UserRole)
        client  = record.get("client", "")
        key     = record.get("key", "")

        resp = QMessageBox.question(
            self, "Revogar Licença",
            f"Revogar a licença de:\n\n{client}\n{key}\n\n"
            "O cliente não conseguirá mais usar o programa.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resp != QMessageBox.StandardButton.Yes:
            return

        records = _load_db()
        for r in records:
            if r.get("key") == key:
                r["revoked"] = True
                r["revoked_at"] = datetime.now().isoformat()
        _save_db(records)
        self._refresh_table()
        QMessageBox.information(self, "Revogada", f"Licença de {client} revogada.")

    def _show_key_dialog(self, idx):
        """Duplo clique na linha — mostra a chave em destaque para copiar."""
        src_idx = self._proxy.mapToSource(idx)
        item    = self._model.item(src_idx.row(), 0)
        record  = item.data(Qt.ItemDataRole.UserRole)
        key     = record.get("key", "")
        client  = record.get("client", "")
        expiry  = record.get("expiry", "")

        try:
            exp_fmt = date.fromisoformat(expiry).strftime("%d/%m/%Y")
        except Exception:
            exp_fmt = expiry

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Chave — {client}")
        dlg.setMinimumWidth(440)
        dlg.setStyleSheet(STYLE)
        v = QVBoxLayout(dlg)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(12)

        v.addWidget(QLabel(f"<b>{client}</b>  |  Expira: {exp_fmt}"))

        lbl_key = QLabel(key)
        lbl_key.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_key.setStyleSheet(
            "font-size: 20px; font-weight: bold; letter-spacing: 4px; "
            "color: #A6E3A1; background: #313244; border-radius: 8px; padding: 14px;"
        )
        lbl_key.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v.addWidget(lbl_key)

        btn_copy = QPushButton("📋  Copiar Chave")
        btn_copy.setObjectName("BtnGenerate")
        btn_copy.clicked.connect(lambda: (
            QApplication.clipboard().setText(key),
            btn_copy.setText("✅  Copiado!")
        ))
        v.addWidget(btn_copy)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.reject)
        v.addWidget(btns)
        dlg.exec()


# ══════════════════════════════════════════════════════════════════════════ #
#  Entry point                                                               #
# ══════════════════════════════════════════════════════════════════════════ #

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("WinPE License Manager")
    win = LicenseManagerWindow()
    win.show()
    sys.exit(app.exec())
