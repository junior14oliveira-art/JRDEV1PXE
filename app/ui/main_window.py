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
from app.ui.views.about_view import AboutView
from app.ui.views.unattend_view import UnattendView
from app.workers.iso_worker import ExtractIsoWorker


# ── Constantes ──────────────────────────────────────────────────────────── #
NAV_ITEMS = [
    ("🏠", "Início",       "dashboard"),
    ("📥", "Baixar",       "download"),
    ("📁", "Arquivos",     "files"),
    ("🎨", "Customizar",   "custom"),
    ("📡", "Rede PXE",     "pxe"),
    ("⚙️", "Gerar ISO",    "build"),
    ("⚡", "Instalação Auto", "unattend"),
    ("📋", "Logs",         "logs"),
    ("ℹ️",  "Sobre",        "about"),
]
WORK_DIR = Path("E:/WinPE_Studio_Workspace")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JRDEV1 PXE — WinPE Studio Pro v2.1")
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
        self._v_unattend = UnattendView()
        self._v_logs = LogPanelView()
        self._v_about = AboutView()

        self._stack.addWidget(self._v_dashboard)  # 0
        self._stack.addWidget(self._v_download)   # 1
        self._stack.addWidget(self._v_files)       # 2
        self._stack.addWidget(self._v_custom)      # 3
        self._stack.addWidget(self._v_pxe)         # 4
        self._stack.addWidget(self._v_build)       # 5
        self._stack.addWidget(self._v_unattend)    # 6
        self._stack.addWidget(self._v_logs)        # 7
        self._stack.addWidget(self._v_about)       # 8

        # Conectar sinais
        self._v_dashboard.iso_selected.connect(self._on_iso_selected)
        self._v_download.log_message.connect(self._v_logs.append)
        self._v_download.iso_downloaded.connect(self._on_iso_selected)
        self._v_files.status_message.connect(self.statusBar().showMessage)
        self._v_custom.log_message.connect(self._v_logs.append)
        self._v_custom.commit_finished.connect(self._on_custom_commit_done)
        self._v_custom.wim_mounted.connect(self._on_wim_mounted)
        self._v_pxe.log_message.connect(self._v_logs.append)
        self._v_build.log_message.connect(self._v_logs.append)
        self._v_unattend.log_message.connect(self._v_logs.append)

    def _detect_env(self):
        """Detecta o ambiente e passa para as views."""
        status = detect_system()
        if status.oscdimg_found:
            self._v_build.set_oscdimg_path(status.oscdimg_path)
            # Proteção: só chama se o método existir (compatibilidade)
            if hasattr(self._v_unattend, 'set_oscdimg_path'):
                self._v_unattend.set_oscdimg_path(status.oscdimg_path)
        
        # Atualiza o dashboard com o status real (opcional, dashboard já chama internamente, 
        # mas centralizar aqui é melhor)
        # self._v_dashboard.update_status(status)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(200)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(4)

        # ── Logo JRDEV1 ───────────────────────────────────────────── #
        logo_frame = QFrame()
        logo_frame.setStyleSheet("""
            QFrame {
                background-color: #091428;
                border-bottom: 1px solid #1A3A6B;
                padding: 8px 0;
            }
        """)
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(12, 8, 12, 12)
        logo_layout.setSpacing(2)

        # Ícone </> em destaque
        lbl_icon = QLabel("</> 💡")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 22px; color: #2E6BE6; background: transparent; border: none;")
        logo_layout.addWidget(lbl_icon)

        lbl_brand = QLabel("JRDEV1 PXE")
        lbl_brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_brand.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #FFFFFF; "
            "letter-spacing: 2px; background: transparent; border: none;"
        )
        logo_layout.addWidget(lbl_brand)

        lbl_tagline = QLabel("WinPE Studio Pro")
        lbl_tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_tagline.setStyleSheet("font-size: 10px; color: #4A6FA5; background: transparent; border: none;")
        logo_layout.addWidget(lbl_tagline)

        layout.addWidget(logo_frame)
        layout.addSpacing(8)

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

        # Status da licença
        self._lbl_license = QLabel("🔑 ...")
        self._lbl_license.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_license.setWordWrap(True)
        self._lbl_license.setStyleSheet("color: #6C7086; font-size: 11px; padding: 0 8px;")
        layout.addWidget(self._lbl_license)

        layout.addSpacing(4)

        # Status ISO carregada
        self._lbl_iso_name = QLabel("Nenhuma ISO")
        self._lbl_iso_name.setObjectName("SidebarInfo")
        self._lbl_iso_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_iso_name.setWordWrap(True)
        layout.addWidget(self._lbl_iso_name)

        layout.addSpacing(8)

        # Botão fechar / encerrar tudo
        btn_exit = QPushButton(" ⏻  Fechar Programa")
        btn_exit.setObjectName("BtnExit")
        btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exit.setFixedHeight(36)
        btn_exit.setStyleSheet(
            "QPushButton#BtnExit {"
            "  background-color: #313244;"
            "  color: #f38ba8;"
            "  border: 1px solid #f38ba8;"
            "  border-radius: 6px;"
            "  font-weight: bold;"
            "  margin: 0 12px;"
            "}"
            "QPushButton#BtnExit:hover {"
            "  background-color: #f38ba8;"
            "  color: #1e1e2e;"
            "}"
        )
        btn_exit.clicked.connect(self._confirm_exit)
        layout.addWidget(btn_exit)

        layout.addSpacing(8)

        # Selecionar Dashboard por padrão
        self._nav_buttons["dashboard"].setChecked(True)
        return sidebar

    def _setup_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.showMessage("Pronto.")

    def set_license_info(self, info: dict):
        """Atualiza o label de licença na sidebar."""
        days_left = info.get("days_left", 0)
        expiry    = info.get("expiry", "")
        try:
            from datetime import date
            exp_fmt = date.fromisoformat(expiry).strftime("%d/%m/%Y")
        except Exception:
            exp_fmt = expiry

        if days_left <= 7:
            color = "#F38BA8"   # vermelho
            icon  = "🔴"
        elif days_left <= 30:
            color = "#FAB387"   # laranja
            icon  = "⚠️"
        else:
            color = "#A6E3A1"   # verde
            icon  = "✅"

        self._lbl_license.setText(f"{icon} Licença: {days_left}d\nExpira {exp_fmt}")
        self._lbl_license.setStyleSheet(
            f"color: {color}; font-size: 11px; padding: 0 8px;"
        )

    # ─────────────────────────────────────────────────────────────────── #
    #  Navegação                                                           #
    # ─────────────────────────────────────────────────────────────────── #
    _PAGE_INDEX = {
        "dashboard": 0, "download": 1, "files": 2, "custom": 3,
        "pxe": 4, "build": 5, "unattend": 6, "logs": 7, "about": 8
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
        self._v_pxe.setEnabled(False)  # PXE bloqueado até extração + injeção terminar

        self._v_logs.append(f"ISO selecionada: {iso_path}")
        self._v_logs.append(f"Pasta de trabalho: {work}")
        
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
        self._v_pxe.setEnabled(True)

        if success:
            # Atualiza TODAS as views com o projeto correto APÓS extração completa
            self._v_files.set_root(self._work_dir)
            self._v_custom.set_project(self._work_dir)
            self._v_build.set_source(self._work_dir)
            self._v_pxe.set_project(self._work_dir)
            self._v_unattend.set_project(self._work_dir)
            self._v_logs.append(f"✅ Projeto carregado: {self._work_dir}")

            # Pergunta se quer injetar drivers de rede
            resp = QMessageBox.question(
                self,
                "Injetar Drivers de Rede?",
                "Deseja injetar drivers de rede no boot.wim agora?\n\n"
                "✅ Sim — necessário para ISOs sem drivers (WinPE limpo, ADK)\n"
                "❌ Não — ISOs que já têm drivers (Strelec, Hiren's)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if resp == QMessageBox.StandardButton.Yes:
                self._v_logs.append("🔌 Injeção de drivers solicitada — iniciando...")
                self._inject_drivers_async()
            else:
                self._v_logs.append("⏭️  Injeção de drivers ignorada.")
                self._v_logs.append("🚀 Pode iniciar o servidor PXE agora.")
                self._navigate("files")
        else:
            QMessageBox.critical(self, "Erro na Extração", msg)

    def _inject_drivers_async(self):
        """Inicia a injeção de drivers em background (reutiliza o worker)."""
        from app.workers.iso_worker import ExtractIsoWorker
        # Cria um worker só para injeção (iso_path vazio, work_dir já extraído)
        self._inject_worker = _DriverInjectWorker(self._work_dir)
        self._inject_worker.log_message.connect(self._v_logs.append)
        self._inject_worker.finished.connect(self._on_inject_done)
        self._global_progress.show()
        self._global_progress.setValue(0)
        self._v_pxe.setEnabled(False)
        self._inject_worker.start()

    @Slot(bool, str)
    def _on_inject_done(self, success: bool, msg: str):
        self._global_progress.hide()
        self._v_pxe.setEnabled(True)
        self._v_logs.append(f"{'✅' if success else '⚠️'} {msg}")
        self._v_logs.append("🚀 Pode iniciar o servidor PXE agora.")
        self._navigate("files")
    @Slot(bool)
    def _on_wim_mounted(self, mounted: bool):
        """Bloqueia 'Gerar ISO' enquanto o WIM estiver montado."""
        self._v_build.setEnabled(not mounted)
        if mounted:
            self.statusBar().showMessage(
                "⚠️ WIM montado — finalize a edição e clique 'Salvar e Desmontar' antes de gerar a ISO."
            )
        else:
            self.statusBar().showMessage("WIM desmontado. Pode gerar a ISO.")

    # ─────────────────────────────────────────────────────────────────── #
    #  Fechar / Encerrar tudo                                              #
    # ─────────────────────────────────────────────────────────────────── #
    def _confirm_exit(self):
        """Botão 'Fechar Programa' — pede confirmação e encerra tudo."""
        # Avisa se o servidor PXE estiver rodando
        pxe_running = getattr(self._v_pxe, '_is_running', False)
        wim_mounted = getattr(self._v_custom, '_is_mounted', False)

        warnings = []
        if pxe_running:
            warnings.append("• Servidor PXE está ativo — será encerrado")
        if wim_mounted:
            warnings.append("• WIM está montado — será desmontado SEM salvar")

        msg = "Deseja fechar o WinPE Studio e encerrar todos os processos?"
        if warnings:
            msg += "\n\n⚠️ Atenção:\n" + "\n".join(warnings)

        resp = QMessageBox.question(
            self, "Fechar Programa", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if resp == QMessageBox.StandardButton.Yes:
            self._shutdown_all()
            self.close()

    def _shutdown_all(self):
        """Para todos os serviços e workers antes de fechar."""
        import sys

        self._v_logs.append("🔴 Encerrando todos os processos...")

        # 1. Parar servidor PXE
        try:
            if getattr(self._v_pxe, '_is_running', False):
                self._v_logs.append("  → Parando servidor PXE...")
                self._v_pxe._stop_server()
        except Exception as e:
            self._v_logs.append(f"  ⚠️ PXE: {e}")

        # 2. Desmontar WIM se estiver montado (sem salvar)
        try:
            if getattr(self._v_custom, '_is_mounted', False):
                self._v_logs.append("  → Desmontando WIM (descartando)...")
                from app.core.dism_service import DismService
                DismService().unmount_wim(
                    self._v_custom._mount_dir,
                    commit=False,
                    log_cb=self._v_logs.append,
                )
        except Exception as e:
            self._v_logs.append(f"  ⚠️ WIM: {e}")

        # 3. Parar workers em background
        for attr in ('_worker', '_inject_worker'):
            try:
                w = getattr(self, attr, None)
                if w and w.isRunning():
                    self._v_logs.append(f"  → Aguardando worker {attr}...")
                    w.quit()
                    w.wait(2000)
            except Exception:
                pass

        # 4. Parar download worker se existir
        try:
            dw = getattr(self._v_download, '_worker', None)
            if dw and dw.isRunning():
                self._v_logs.append("  → Parando download...")
                dw.quit()
                dw.wait(2000)
        except Exception:
            pass

        self._v_logs.append("✅ Tudo encerrado.")

    def closeEvent(self, event):
        """Intercepta o X da janela — mesma lógica do botão Fechar."""
        pxe_running = getattr(self._v_pxe, '_is_running', False)
        wim_mounted = getattr(self._v_custom, '_is_mounted', False)

        if pxe_running or wim_mounted:
            warnings = []
            if pxe_running:
                warnings.append("• Servidor PXE está ativo — será encerrado")
            if wim_mounted:
                warnings.append("• WIM está montado — será desmontado SEM salvar")

            msg = "Deseja fechar o WinPE Studio?\n\n⚠️ Atenção:\n" + "\n".join(warnings)
            resp = QMessageBox.question(
                self, "Fechar", msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

        self._shutdown_all()
        event.accept()

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


# ── Worker dedicado apenas para injeção de drivers ───────────────────────── #
from app.workers.base_worker import BaseWorker
from app.core.iso_service import IsoService

class _DriverInjectWorker(BaseWorker):
    """Injeta drivers de rede num projeto já extraído, sem re-extrair a ISO."""

    def __init__(self, work_dir: str, parent=None):
        super().__init__(parent)
        self.work_dir = work_dir

    def run(self):
        try:
            svc = IsoService()
            info = svc.detect_winpe_structure(self.work_dir)
            if not info.get("boot_wim"):
                self.finished.emit(False, "boot.wim não encontrado no projeto.")
                return

            # Importa e reutiliza a lógica de injeção do ExtractIsoWorker
            from app.workers.iso_worker import ExtractIsoWorker
            # Cria instância temporária só para usar o método de injeção
            injector = ExtractIsoWorker.__new__(ExtractIsoWorker)
            injector.log_message = self.log_message  # compartilha o signal de log
            injector._log = self._log
            injector._inject_network_drivers(info["boot_wim"])
            self.finished.emit(True, "Injeção de drivers concluída.")
        except Exception as e:
            self.finished.emit(False, f"Erro na injeção: {e}")
