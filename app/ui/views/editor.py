from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTreeView, QFileSystemModel
from PySide6.QtCore import QDir

class EditorView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("WinPE Virtual File System")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        # File System Tree
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        # We will set root path later when a WIM is mounted
        
        layout.addWidget(self.tree)
