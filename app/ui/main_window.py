"""Janela principal do WinPE Studio — layout simples com sidebar + stack de views."""
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QLabel, QPushButton, QSpacerItem,
    QSizePolicy, QProgressBar, QStatusBar, QMessageBox,
    QFrame,
)

from app.core.system_checker import detect_system
from app.ui.styles import DARK_THEME_QSS
from app.ui.views.dashboard import DashboardView
from app.ui.views.file_explorer import FileExplorerView
from app.ui.views.customization import CustomizationView
from app.ui.views.pxe_view import PxeView
from app.ui.views.download_view import DownloadView
from app.ui.views.build_view import BuildView
from app.ui.views.log_panel import LogPanelView
from app.workers.iso_worker import ExtractIsoWorker


# ── Constantes ──────────────────────────────────────────────────────────── #
NAV_ITEMS = [
    ("🏠", "Início",    "dashboard"),
    ("📥", "Baixar",    "download"),
    ("📁", "Arquivos",  "files"),
    ("🎨", "Customizar", "custom"),
    ("📡", "Rede PXE",   "pxe"),
    ("⚙️", "Gerar ISO",  "build"),
    ("📋", "Logs",       "logs"),
]
WORK_DIR = Path("E:/WinPE_Studio_Workspace")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WinPE Studio Pro v2.1")
        self.resize(1100, 720)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(DARK_THEME_QSS)

        self._worker: ExtractIsoWorker | None = None
        self._work_dir: str = ""

        self._setup_statusbar()  # deve vir antes de _setup_ui
        self._setup_ui()
        self._detect_env()

    # ─────────────────────────────────────────────────────────────────── #
    #  Layout principal                                                     #
    # ─────────────────────────────────────────────────────────────────── #
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main = QHBoxLayout(central)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # Sidebar
        self._sidebar = self._build_sidebar()
        main.addWidget(self._sidebar)

        # Área de conteúdo
        content_wrap = QVBoxLayout()
        content_wrap.setContentsMargins(0, 0, 0, 0)
        content_wrap.setSpacing(0)

        # Barra de progresso global (oculta por padrão)
        self._global_progress = QProgressBar()
        self._global_progress.setRange(0, 100)
        self._global_progress.setFixedHeight(4)
        self._global_progress.setTextVisible(False)
        self._global_progress.setObjectName("GlobalProgress")
        self._global_progress.hide()
        content_wrap.addWidget(self._global_progress)

        # Stack de views
        self._stack = QStackedWidget()
        content_wrap.addWidget(self._stack, stretch=1)
        main.addLayout(content_wrap, stretch=1)

        # Instanciar views
        self._v_dashboard = DashboardView()
        self._v_download = DownloadView()
        self._v_files = FileExplorerView()
        self._v_custom = CustomizationView()
        self._v_pxe = PxeView()
        self._v_build = BuildView()
        self._v_logs = LogPanelView()

        self._stack.addWidget(self._v_dashboard)  # 0
        self._stack.addWidget(self._v_download)   # 1
        self._stack.addWidget(self._v_files)       # 2
        self._stack.addWidget(self._v_custom)      # 3
        self._stack.addWidget(self._v_pxe)         # 4
        self._stack.addWidget(self._v_build)       # 5
        self._stack.addWidget(self._v_logs)        # 6

        # Conectar sinais
        self._v_dashboard.iso_selected.connect(self._on_iso_selected)
        self._v_download.log_message.connect(self._v_logs.append)
        self._v_download.iso_downloaded.connect(self._on_iso_selected)
        self._v_files.status_message.connect(self.statusBar().showMessage)
        self._v_custom.log_message.connect(self._v_logs.append)
        self._v_custom.commit_finished.connect(self._on_custom_commit_done)
        self._v_pxe.log_message.connect(self._v_logs.append)
        self._v_build.log_message.connect(self._v_logs.append)

    def _detect_env(self):
        """Detecta o ambiente e passa para as views."""
        status = detect_system()
        # Passa o caminho do oscdimg para a view de build
        if status.oscdimg_found:
            self._v_build.set_oscdimg_path(status.oscdimg_path)
        
        # Atualiza o dashboard com o status real (opcional, dashboard já chama internamente, 
        # mas centralizar aqui é melhor)
        # self._v_dashboard.update_status(status)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(200)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(4)

        # Logo
        logo = QLabel("WinPE\nStudio")
        logo.setObjectName("SidebarLogo")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)
        layout.addSpacing(16)

        # Botões de navegação
        self._nav_buttons: dict[str, QPushButton] = {}
        for icon, label, page_id in NAV_ITEMS:
            btn = QPushButton(f" {icon}  {label}")
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, pid=page_id: self._navigate(pid))
            layout.addWidget(btn)
            self._nav_buttons[page_id] = btn

        layout.addStretch()

        # Status ISO carregada
        self._lbl_iso_name = QLabel("Nenhuma ISO")
        self._lbl_iso_name.setObjectName("SidebarInfo")
        self._lbl_iso_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_iso_name.setWordWrap(True)
        layout.addWidget(self._lbl_iso_name)

        # Selecionar Dashboard por padrão
        self._nav_buttons["dashboard"].setChecked(True)
        return sidebar

    def _setup_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.showMessage("Pronto.")

    # ─────────────────────────────────────────────────────────────────── #
    #  Navegação                                                           #
    # ─────────────────────────────────────────────────────────────────── #
    _PAGE_INDEX = {
        "dashboard": 0, "download": 1, "files": 2, "custom": 3, 
        "pxe": 4, "build": 5, "logs": 6
    }

    def _navigate(self, page_id: str):
        for pid, btn in self._nav_buttons.items():
            btn.setChecked(pid == page_id)
        self._stack.setCurrentIndex(self._PAGE_INDEX.get(page_id, 0))

    # ─────────────────────────────────────────────────────────────────── #
    #  Fluxo: abrir ISO → extrair → liberar navegação                     #
    # ─────────────────────────────────────────────────────────────────── #
    @Slot(str)
    def _on_iso_selected(self, iso_path: str):
        import time
        iso = Path(iso_path)
        # Adiciona o horário (HHMMSS) ao nome para garantir que a pasta seja sempre nova e única
        stamp = time.strftime("%H%M%S")
        work = WORK_DIR / f"{iso.stem}_{stamp}"
        self._work_dir = str(work)

        self._lbl_iso_name.setText(iso.name)
        self.statusBar().showMessage(f"Extraindo em nova pasta: {work.name}…")
        self._global_progress.show()
        self._global_progress.setValue(0)
        
        # Bloquear ações durante a extração
        self._v_files.setEnabled(False)
        self._v_build.setEnabled(False)

        # Log
        self._v_logs.append(f"ISO selecionada: {iso_path}")
        self._v_logs.append(f"Pasta de trabalho: {work}")
        
        # Preencher views imediatamente para dar feedback
        self._v_files.set_root(self._work_dir)
        self._v_custom.set_project(self._work_dir)
        self._v_pxe.set_project(self._work_dir)
        self._v_build.set_source(self._work_dir)
        
        self._navigate("logs")

        # Worker de extração
        self._worker = ExtractIsoWorker(iso_path=iso_path, work_dir=str(work))
        self._worker.log_message.connect(self._v_logs.append)
        self._worker.progress.connect(self._global_progress.setValue)
        self._worker.finished.connect(self._on_extract_done)
        self._worker.start()

    @Slot(bool, str)
    def _on_extract_done(self, success: bool, msg: str):
        self._global_progress.hide()
        self.statusBar().showMessage(msg)
        self._v_logs.append(f"{'✅' if success else '❌'} {msg}")
        
        self._v_files.setEnabled(True)
        self._v_custom.setEnabled(True)
        self._v_build.setEnabled(True)

        if success:
            self._v_files.set_root(self._work_dir)
            self._v_custom.set_project(self._work_dir)
            self._v_pxe.set_project(self._work_dir)
            self._v_build.set_source(self._work_dir)
            self._navigate("files")
        else:
            QMessageBox.critical(self, "Erro na Extração", msg)
    @Slot()
    def _on_custom_commit_done(self):
        """Chamado quando o usuário termina de editar e salva o WIM."""
        resp = QMessageBox.question(
            self, "Alterações Salvas",
            "As edições foram gravadas no WinPE com sucesso.\n\n"
            "Deseja gerar a ISO final agora?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            self._navigate("build")
            # Iniciar o build automaticamente com as configurações padrão
            self._v_build._start_build()
