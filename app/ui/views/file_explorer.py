"""Explorador de arquivos do WinPE extraído — add, remove, copiar arquivos."""
import shutil
from pathlib import Path

from PySide6.QtCore import Qt, QDir, QModelIndex, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTreeView, QFileSystemModel,
    QFileDialog, QMessageBox, QMenu, QSplitter,
    QFrame, QToolBar,
)


class FileExplorerView(QWidget):
    status_message = Signal(str)

    def __init__(self):
        super().__init__()
        self._root_path: str = ""
        self._setup_ui()

    # ──────────────────────────────────────────────────────────────────── #
    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)

        # Cabeçalho
        title = QLabel("📁  Arquivos do WinPE")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        # Info do projeto
        self._lbl_path = QLabel("Nenhuma ISO aberta.")
        self._lbl_path.setObjectName("PageSubtitle")
        root.addWidget(self._lbl_path)

        # Toolbar de ações
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self._btn_add = self._make_btn("➕ Adicionar Arquivo", self._add_file)
        self._btn_add_folder = self._make_btn("📂 Adicionar Pasta", self._add_folder)
        self._btn_delete = self._make_btn("🗑 Remover", self._delete_selected)
        self._btn_snapshot = self._make_btn("📸 Criar Backup (Versão)", self._create_snapshot)
        self._btn_snapshot.setObjectName("BtnSecondary")

        toolbar.addWidget(self._btn_add)
        toolbar.addWidget(self._btn_add_folder)
        toolbar.addWidget(self._btn_delete)
        toolbar.addWidget(self._btn_snapshot)
        toolbar.addStretch()
        root.addLayout(toolbar)

        # Tree view
        self._model = QFileSystemModel()
        self._model.setRootPath("")

        self._tree = QTreeView()
        self._tree.setModel(self._model)
        self._tree.setColumnWidth(0, 380)
        self._tree.setAlternatingRowColors(True)
        self._tree.setSortingEnabled(True)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_context_menu)
        root.addWidget(self._tree, stretch=1)

        self._set_controls_enabled(False)

    def _make_btn(self, text: str, slot) -> QPushButton:
        btn = QPushButton(text)
        btn.clicked.connect(slot)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _set_controls_enabled(self, enabled: bool):
        for btn in (self._btn_add, self._btn_add_folder, self._btn_delete, self._btn_snapshot):
            btn.setEnabled(enabled)

    # ──────────────────────────────────────────────────────────────────── #
    def set_root(self, path: str):
        """Define o diretório raiz a exibir (pasta extraída da ISO)."""
        self._root_path = path
        idx = self._model.setRootPath(path)
        self._tree.setRootIndex(idx)
        self._lbl_path.setText(f"Raiz: {path}")
        self._set_controls_enabled(True)
        self.status_message.emit(f"Explorador apontado para: {path}")

    # ──────────────────────────────────────────────────────────────────── #
    def _current_dir(self) -> Path:
        idx = self._tree.currentIndex()
        if idx.isValid():
            p = Path(self._model.filePath(idx))
            return p if p.is_dir() else p.parent
        return Path(self._root_path)

    def _add_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Selecionar arquivo(s) para adicionar", "E:\\"
        )
        dest_dir = self._current_dir()
        for f in files:
            try:
                shutil.copy2(f, dest_dir / Path(f).name)
                self.status_message.emit(f"Adicionado: {Path(f).name}")
            except Exception as e:
                QMessageBox.warning(self, "Erro", str(e))

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Selecionar pasta para adicionar", "E:\\"
        )
        if not folder:
            return
        dest = self._current_dir() / Path(folder).name
        try:
            shutil.copytree(folder, dest, dirs_exist_ok=True)
            self.status_message.emit(f"Pasta adicionada: {Path(folder).name}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", str(e))

    def _delete_selected(self):
        idx = self._tree.currentIndex()
        if not idx.isValid():
            return
        path = Path(self._model.filePath(idx))
        resp = QMessageBox.question(
            self, "Confirmar remoção",
            f"Remover permanentemente:\n{path.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resp == QMessageBox.StandardButton.Yes:
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                self.status_message.emit(f"Removido: {path.name}")
            except Exception as e:
                QMessageBox.warning(self, "Erro", str(e))

    def _create_snapshot(self):
        """Copia o diretório atual para uma pasta de backup (Controle de Versões)."""
        if not self._root_path:
            return

        base = Path(self._root_path)
        backup_root = base.parent / "Backups" / base.name
        backup_root.mkdir(parents=True, exist_ok=True)

        # Contar backups existentes para sugerir versão
        existing = list(backup_root.glob("v*"))
        v_num = len(existing) + 1
        
        name, ok = QFileDialog.getSaveFileName(
            self, "Criar Snapshot de Versão",
            str(backup_root / f"v{v_num}"),
            "Pasta de Backup (*)"
        )
        
        if ok and name:
            dest = Path(name)
            try:
                self.status_message.emit(f"Criando snapshot em: {dest.name}...")
                shutil.copytree(base, dest, dirs_exist_ok=True)
                QMessageBox.information(self, "Sucesso", f"Snapshot criado:\n{dest}")
                self.status_message.emit(f"Snapshot concluído: {dest.name}")
            except Exception as e:
                QMessageBox.critical(self, "Erro no Backup", f"Falha ao criar snapshot: {e}")

    def _show_context_menu(self, pos):
        idx = self._tree.indexAt(pos)
        menu = QMenu(self)
        menu.addAction("➕ Adicionar arquivo aqui", self._add_file)
        menu.addAction("📂 Adicionar pasta aqui", self._add_folder)
        if idx.isValid():
            menu.addSeparator()
            menu.addAction("🗑 Remover", self._delete_selected)
        menu.exec(self._tree.viewport().mapToGlobal(pos))
