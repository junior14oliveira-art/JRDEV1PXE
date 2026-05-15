"""
WinPE Studio — Painel Admin de Licenças
Uso exclusivo do desenvolvedor para gerar e gerenciar licenças.

Execute: python license_manager.py
"""
import hashlib
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QTableView,
    QGroupBox, QFormLayout, QMessageBox, QHeaderView,
    QFrame, QStatusBar, QDialog, QDialogButtonBox,
)
from app.core.license_service import generate_license_key

_DB_FILE = Path(__file__).parent / "licenses.json"

# ── Credenciais do admin (hash SHA-256 da senha) ─────────────────────────── #
_ADMIN_EMAIL    = "junior.14.oliveira@gmail.com"
_ADMIN_PASS_SHA = hashlib.sha256("Jesus23@".encode()).hexdigest()


# ══════════════════════════════════════════════════════════════════════════ #
#  Banco de licenças                                                         #
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
#  Estilo                                                                    #
# ══════════════════════════════════════════════════════════════════════════ #

STYLE = """
QMainWindow, QWidget, QDialog {
    background-color: #0D1B3E;
    color: #E8EDF5;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #2A4A7B;
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px;
    font-weight: bold;
    color: #2E6BE6;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
    background-color: #0D1B3E;
}
QLineEdit, QComboBox {
    background-color: #1A3A6B;
    border: 1px solid #2A4A7B;
    border-radius: 6px;
    padding: 8px 12px;
    color: #E8EDF5;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #2E6BE6; }
QPushButton {
    background-color: #1A3A6B;
    color: #E8EDF5;
    border: 1px solid #2A4A7B;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
}
QPushButton:hover { background-color: #2A4A8B; border-color: #2E6BE6; }
QPushButton#BtnGenerate {
    background-color: #2E6BE6;
    color: #FFFFFF;
    border: none;
    font-size: 14px;
    padding: 10px 24px;
}
QPushButton#BtnGenerate:hover { background-color: #4A85F5; }
QPushButton#BtnRevoke {
    background-color: #F38BA8;
    color: #11111B;
    border: none;
}
QPushButton#BtnRevoke:hover { background-color: #EBA0AC; }
QTableView {
    background-color: #091428;
    border: 1px solid #1A3A6B;
    border-radius: 8px;
    gridline-color: #1A3A6B;
    selection-background-color: #2E6BE6;
    selection-color: #FFFFFF;
}
QHeaderView::section {
    background-color: #1A3A6B;
    color: #7A9CC8;
    padding: 8px;
    border: none;
    font-weight: bold;
}
QStatusBar { color: #4A6FA5; }
"""


# ══════════════════════════════════════════════════════════════════════════ #
#  Tela de Login                                                             #
# ══════════════════════════════════════════════════════════════════════════ #

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JRDEV1 — Acesso Restrito")
        self.setFixedSize(420, 340)
        self.setStyleSheet(STYLE)
        self._ok = False
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 36, 40, 36)
        root.setSpacing(0)

        # Logo / título
        lbl_logo = QLabel("</> 💡")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_logo.setStyleSheet("font-size: 28px; background: transparent;")
        root.addWidget(lbl_logo)

        lbl_title = QLabel("JRDEV1 PXE")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #FFFFFF; letter-spacing: 2px;")
        root.addWidget(lbl_title)

        lbl_sub = QLabel("Gerenciador de Licenças")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet("font-size: 12px; color: #4A6FA5; margin-bottom: 20px;")
        root.addWidget(lbl_sub)

        root.addSpacing(20)

        # Email
        lbl_email = QLabel("E-mail:")
        lbl_email.setStyleSheet("color: #7A9CC8; font-size: 12px;")
        root.addWidget(lbl_email)
        root.addSpacing(4)
        self._txt_email = QLineEdit()
        self._txt_email.setPlaceholderText("seu@email.com")
        self._txt_email.setText(_ADMIN_EMAIL)
        root.addWidget(self._txt_email)

        root.addSpacing(12)

        # Senha
        lbl_pass = QLabel("Senha:")
        lbl_pass.setStyleSheet("color: #7A9CC8; font-size: 12px;")
        root.addWidget(lbl_pass)
        root.addSpacing(4)
        self._txt_pass = QLineEdit()
        self._txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self._txt_pass.setPlaceholderText("••••••••")
        self._txt_pass.returnPressed.connect(self._do_login)
        root.addWidget(self._txt_pass)

        root.addSpacing(4)

        # Erro
        self._lbl_err = QLabel("")
        self._lbl_err.setStyleSheet("color: #F38BA8; font-size: 11px;")
        self._lbl_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._lbl_err)

        root.addSpacing(16)

        # Botão
        btn = QPushButton("🔐  Entrar")
        btn.setObjectName("BtnGenerate")
        btn.setFixedHeight(42)
        btn.clicked.connect(self._do_login)
        root.addWidget(btn)

    def _do_login(self):
        email = self._txt_email.text().strip().lower()
        senha = self._txt_pass.text()
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()

        if email == _ADMIN_EMAIL.lower() and senha_hash == _ADMIN_PASS_SHA:
            self._ok = True
            self.accept()
        else:
            self._lbl_err.setText("❌ E-mail ou senha incorretos.")
            self._txt_pass.clear()
            self._txt_pass.setFocus()

    def accepted_login(self) -> bool:
        return self._ok


# ══════════════════════════════════════════════════════════════════════════ #
#  Janela principal                                                          #
# ══════════════════════════════════════════════════════════════════════════ #

class LicenseManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JRDEV1 PXE — Gerenciador de Licenças")
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

        lbl = QLabel("🔑  Gerenciador de Licenças — JRDEV1 PXE")
        lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #2E6BE6;")
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

        btn_row = QHBoxLayout()
        self._btn_gen = QPushButton("⚡  Gerar Licença")
        self._btn_gen.setObjectName("BtnGenerate")
        self._btn_gen.clicked.connect(self._generate)
        btn_row.addWidget(self._btn_gen)
        btn_row.addStretch()
        form.addRow("", btn_row)
        root.addWidget(grp)

        # ── Tabela ────────────────────────────────────────────────────── #
        grp2 = QGroupBox("Licenças Emitidas")
        v2 = QVBoxLayout(grp2)

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

        self._model = QStandardItemModel()
        self._model.setHorizontalHeaderLabels([
            "Cliente", "Chave", "Plano", "Emitida em", "Expira em", "Status", "Notas"
        ])

        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(-1)

        self._table = QTableView()
        self._table.setModel(self._proxy)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet("alternate-background-color: #0D2040;")
        self._table.doubleClicked.connect(self._show_key_dialog)
        v2.addWidget(self._table)
        root.addWidget(grp2, stretch=1)

        self._sb = QStatusBar()
        self.setStatusBar(self._sb)
        self._sb.showMessage("Pronto.")

    def _generate(self):
        client = self._txt_client.text().strip()
        if not client:
            QMessageBox.warning(self, "Atenção", "Informe o nome do cliente.")
            return

        plan_idx = self._cmb_plan.currentIndex()
        days_map = [90, 180, 365, 730]
        days     = days_map[plan_idx]
        plan_lbl = self._cmb_plan.currentText().strip()
        expiry   = date.today() + timedelta(days=days)
        key      = generate_license_key(expiry)

        _add_record({
            "client":  client,
            "key":     key,
            "plan":    plan_lbl,
            "issued":  date.today().isoformat(),
            "expiry":  expiry.isoformat(),
            "notes":   self._txt_notes.text().strip(),
            "revoked": False,
        })
        self._refresh_table()
        self._show_generated_key(client, key, expiry, plan_lbl)
        self._txt_client.clear()
        self._txt_notes.clear()

    def _show_generated_key(self, client, key, expiry, plan):
        dlg = QDialog(self)
        dlg.setWindowTitle("Licença Gerada")
        dlg.setMinimumWidth(480)
        dlg.setStyleSheet(STYLE)
        v = QVBoxLayout(dlg)
        v.setSpacing(16)
        v.setContentsMargins(24, 24, 24, 24)
        v.addWidget(QLabel(f"<b>✅ Licença gerada para: {client}</b>"))
        v.addWidget(QLabel(f"Plano: {plan}  |  Expira em: {expiry.strftime('%d/%m/%Y')}"))

        lbl_key = QLabel(key)
        lbl_key.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_key.setStyleSheet(
            "font-size: 22px; font-weight: bold; letter-spacing: 4px; "
            "color: #A6E3A1; background: #1A3A6B; border-radius: 8px; padding: 16px;"
        )
        lbl_key.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v.addWidget(lbl_key)
        v.addWidget(QLabel("<small>📋 Copie e envie ao cliente. A chave só funciona em 1 PC.</small>"))

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
                status = "🚫 Revogada";  color = QColor("#F38BA8")
            elif days_left < 0:
                status = "🔴 Expirada";  color = QColor("#F38BA8")
            elif days_left <= 15:
                status = f"⚠️ {days_left}d";  color = QColor("#FAB387")
            else:
                status = f"✅ {days_left}d";   color = QColor("#A6E3A1")

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

        total   = len(records)
        active  = sum(1 for r in records if not r.get("revoked") and (date.fromisoformat(r["expiry"]) >= today if r.get("expiry") else False))
        expired = sum(1 for r in records if not r.get("revoked") and (date.fromisoformat(r["expiry"]) < today if r.get("expiry") else False))
        revoked = sum(1 for r in records if r.get("revoked"))
        self._sb.showMessage(f"Total: {total}  |  Ativas: {active}  |  Expiradas: {expired}  |  Revogadas: {revoked}")

    def _on_search(self, text):
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
            f"Revogar a licença de:\n\n{client}\n{key}\n\nO cliente não poderá mais usar o programa.",
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
            "color: #A6E3A1; background: #1A3A6B; border-radius: 8px; padding: 14px;"
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
    app.setApplicationName("JRDEV1 License Manager")

    # Tela de login obrigatória
    login = LoginDialog()
    login.exec()
    if not login.accepted_login():
        sys.exit(0)

    win = LicenseManagerWindow()
    win.show()
    sys.exit(app.exec())
