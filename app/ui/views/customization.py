"""View de Customização — Montar WIM, Trocar Wallpaper, Adicionar Arquivos ao Desktop."""
import os
from pathlib import Path
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFileDialog, QMessageBox, QProgressBar, QGroupBox, QFormLayout, QLineEdit, QFrame
)
from app.workers.dism_worker import (
    DismMountWorker, DismUnmountWorker, DismPatchWorker
)
from app.core.dism_service import DismService
from app.core.iso_service import IsoService
from app.workers.iso_worker import CorporateDriverWorker, CORPORATE_PACKS


def _get_resources_drivers():
    """Retorna o caminho da pasta de drivers — funciona como script e como .exe."""
    import sys as _sys
    from pathlib import Path as _Path
    if getattr(_sys, 'frozen', False):
        # Empacotado: recursos ficam em sys._MEIPASS/app/resources/drivers
        base = _Path(_sys._MEIPASS)
        return base / "app" / "resources" / "drivers"
    else:
        # Script: customization.py está em app/ui/views/
        # .parent = views, .parent = ui, .parent = app, .parent = raiz
        return _Path(__file__).parent.parent.parent / "resources" / "drivers"

class CustomizationView(QWidget):
    log_message = Signal(str)
    commit_finished = Signal()   # Novo sinal para automação
    wim_mounted = Signal(bool)   # True = montado, False = desmontado

    def __init__(self):
        super().__init__()
        self._work_dir = ""
        self._mount_dir = ""
        self._boot_wim = ""
        self._is_mounted = False
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(20)

        title = QLabel("🎨  Customização do WinPE")
        title.setObjectName("PageTitle")
        root.addWidget(title)

        sub = QLabel("Edite o interior do Windows PE (Wallpaper, Desktop, Drivers).")
        sub.setObjectName("PageSubtitle")
        root.addWidget(sub)

        # ── Status da Montagem ────────────────────────────────────────── #
        self._grp_mount = QGroupBox("Status do WIM (boot.wim)")
        layout_mount = QVBoxLayout(self._grp_mount)
        
        self._lbl_mount_status = QLabel("WIM não montado. Monte para editar arquivos internos.")
        self._lbl_mount_status.setStyleSheet("color: #f38ba8;") # Reddish
        layout_mount.addWidget(self._lbl_mount_status)

        self._btn_mount = QPushButton("🚀  Montar Imagem (Editar)")
        self._btn_mount.setObjectName("BtnPrimary")
        self._btn_mount.clicked.connect(self._toggle_mount)
        layout_mount.addWidget(self._btn_mount)

        root.addWidget(self._grp_mount)

        # ── Customizações (Desabilitadas se não montado) ──────────────── #
        self._grp_tools = QGroupBox("Ferramentas de Customização")
        form = QFormLayout(self._grp_tools)
        
        # Wallpaper
        self._btn_wallpaper = QPushButton("🖼️  Trocar Plano de Fundo (Wallpaper)")
        self._btn_wallpaper.clicked.connect(self._change_wallpaper)
        form.addRow("Visual:", self._btn_wallpaper)

        # Desktop
        self._btn_desktop = QPushButton("💻  Abrir Pasta do Desktop do WinPE")
        self._btn_desktop.clicked.connect(self._open_desktop_folder)
        form.addRow("Área de Trabalho:", self._btn_desktop)

        # Injetar Programa Auto-Start
        self._btn_autostart = QPushButton("⚡  Injetar Programa (Início Automático)")
        self._btn_autostart.clicked.connect(self._inject_autostart)
        form.addRow("Programas:", self._btn_autostart)

        # Injetar Drivers
        self._btn_drivers = QPushButton("🏎️  Injetar Drivers (.inf)")
        self._btn_drivers.clicked.connect(self._inject_drivers)
        form.addRow("Drivers:", self._btn_drivers)

        # Injetar Pacotes
        self._btn_packages = QPushButton("📦  Injetar Pacotes (.cab)")
        self._btn_packages.clicked.connect(self._inject_package)
        form.addRow("Pacotes:", self._btn_packages)

        # Separador Visual
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        form.addRow(line)

        # ── Pacote Corporativo ────────────────────────────────────── #
        self._btn_corp_drivers = QPushButton("🏢  Injetar Pacote Corporativo (Dell/HP/Lenovo 8ª gen+)")
        self._btn_corp_drivers.setObjectName("BtnPrimary")
        self._btn_corp_drivers.clicked.connect(self._inject_corporate_pack)
        form.addRow("Corporativo:", self._btn_corp_drivers)

        # Separador Visual 2
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        form.addRow(line2)

        # ISO via Rede (HTTPDisk)
        self._txt_http_url = QLineEdit("http://192.168.0.21:8080/strelec.iso")
        self._txt_http_url.setPlaceholderText("URL da ISO (ex: http://192.168.0.21:8080/strelec.iso)")
        self._btn_httpdisk = QPushButton("🌐  Injetar Suporte a ISO via Rede")
        self._btn_httpdisk.clicked.connect(self._inject_httpdisk)
        form.addRow("URL da ISO:", self._txt_http_url)
        form.addRow("Rede Avançada:", self._btn_httpdisk)

        root.addWidget(self._grp_tools)
        self._grp_tools.setEnabled(False)

        # ── Progresso ─────────────────────────────────────────────────── #
        self._progress = QProgressBar()
        self._progress.hide()
        root.addWidget(self._progress)

        root.addStretch()

    def set_project(self, work_dir: str):
        self._work_dir = work_dir
        # Gera uma pasta de montagem única baseada no nome do projeto (ex: Mount_TESTE2_114500)
        # Isso evita o erro 0xc1420113 do DISM
        proj_name = os.path.basename(work_dir)
        self._mount_dir = os.path.join(os.path.dirname(work_dir), f"Mount_{proj_name}")
        os.makedirs(self._mount_dir, exist_ok=True)
        
        # Detectar boot.wim
        svc = IsoService()
        info = svc.detect_winpe_structure(work_dir)
        self._boot_wim = info.get("boot_wim", "")
        
        if not self._boot_wim:
            self._lbl_mount_status.setText("Erro: boot.wim não encontrado na pasta de trabalho.")
            self._btn_mount.setEnabled(False)
        else:
            self._btn_mount.setEnabled(True)

    def _toggle_mount(self):
        if not self._is_mounted:
            self._start_mount()
        else:
            self._start_unmount()

    def _start_mount(self):
        self._btn_mount.setEnabled(False)
        self._progress.show()
        self._progress.setValue(10)
        
        self._worker = DismMountWorker(self._boot_wim, self._mount_dir)
        self._worker.log_message.connect(self.log_message)
        self._worker.progress.connect(self._progress.setValue)
        self._worker.finished.connect(self._on_mount_finished)
        self._worker.start()

    def _on_mount_finished(self, success: bool, msg: str):
        self._progress.hide()
        self._btn_mount.setEnabled(True)
        if success:
            self._is_mounted = True
            import os
            if os.path.isdir(msg):
                if self._mount_dir != msg:
                    self.log_message.emit(f"⚠️ Usando pasta alternativa: {msg}")
                self._mount_dir = msg
            self._btn_mount.setText("💾  Salvar e Desmontar")
            self._lbl_mount_status.setText(f"IMAGEM MONTADA E PRONTA PARA EDIÇÃO.\n{self._mount_dir}")
            self._lbl_mount_status.setStyleSheet("color: #a6e3a1;")
            self._grp_tools.setEnabled(True)
            self.wim_mounted.emit(True)   # ← avisa MainWindow
        else:
            QMessageBox.critical(self, "Erro na Montagem", msg)

    def _start_unmount(self):
        reply = QMessageBox.question(
            self, "Desmontar", "Deseja salvar as alterações feitas na imagem?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Cancel:
            return
            
        commit = (reply == QMessageBox.StandardButton.Yes)
        self._last_unmount_commit = commit # Guardar para automação
        self._btn_mount.setEnabled(False)
        self._progress.show()
        
        self._worker = DismUnmountWorker(self._mount_dir, commit=commit)
        self._worker.log_message.connect(self.log_message)
        self._worker.progress.connect(self._progress.setValue)
        self._worker.finished.connect(self._on_unmount_finished)
        self._worker.start()

    def _on_unmount_finished(self, success: bool, msg: str):
        self._progress.hide()
        self._btn_mount.setEnabled(True)
        if success:
            was_commit = getattr(self, '_last_unmount_commit', False)

            self._is_mounted = False
            self._btn_mount.setText("🚀  Montar Imagem (Editar)")
            self._lbl_mount_status.setText("WIM não montado. Monte para editar arquivos internos.")
            self._lbl_mount_status.setStyleSheet("color: #f38ba8;")
            self._grp_tools.setEnabled(False)
            self.wim_mounted.emit(False)  # ← avisa MainWindow

            if was_commit:
                self.commit_finished.emit()
        else:
            QMessageBox.critical(
                self, "Erro ao Desmontar",
                f"{msg}\n\n"
                "⚠️ CAUSA MAIS COMUM: Uma janela do Windows Explorer está aberta "
                "dentro da pasta de montagem.\n\n"
                "Feche TODAS as janelas do Explorer que mostrem arquivos do WinPE "
                "e tente desmontar novamente."
            )

    def _change_wallpaper(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Novo Wallpaper", "", "Imagens (*.jpg *.jpeg)"
        )
        if file_path:
            svc = DismService()
            if svc.set_wallpaper(self._mount_dir, file_path):
                QMessageBox.information(self, "Sucesso", "Papel de parede alterado com sucesso!")
                self.log_message.emit(f"Wallpaper alterado para: {file_path}")
            else:
                QMessageBox.warning(self, "Erro", "Falha ao trocar wallpaper. Verifique os logs.")

    def _open_desktop_folder(self):
        """Abre a pasta Desktop do WinPE no Explorer.

        O Desktop real do WinPE (com explorer.exe) é SEMPRE:
          X:\\windows\\system32\\config\\systemprofile\\Desktop
        Que equivale a:
          Mount\\Windows\\System32\\config\\systemprofile\\Desktop

        ⚠️ IMPORTANTE: Feche o Explorer ANTES de clicar em Salvar e Desmontar!
        """
        # Avisa o usuário sobre o risco de travamento
        QMessageBox.information(
            self, "⚠️ Atenção",
            "O Windows Explorer será aberto dentro da pasta do WinPE.\n\n"
            "IMPORTANTE: Antes de clicar em 'Salvar e Desmontar',\n"
            "FECHE COMPLETAMENTE esta janela do Explorer.\n\n"
            "Deixar o Explorer aberto causa o erro de desmontagem (0xc1420117)."
        )

        # Caminho correto do Desktop no WinPE (equivalente a X:\windows\system32\config\systemprofile\Desktop)
        desktop_path = os.path.join(
            self._mount_dir,
            "Windows", "System32", "config", "systemprofile", "Desktop"
        )

        try:
            import subprocess
            # Caminho da pasta que o Windows protege
            profile_path = os.path.join(self._mount_dir, "Windows", "System32", "config", "systemprofile")
            
            # 1. Toma posse da pasta e subpastas
            subprocess.run(f'takeown /f "{profile_path}" /r /d y', shell=True, capture_output=True, timeout=20)
            
            # 2. Concede controle total a "Todos" (S-1-1-0) de forma recursiva
            # Usar o SID S-1-1-0 (Everyone) é mais garantido que usar nomes que mudam com o idioma
            subprocess.run(f'icacls "{profile_path}" /grant *S-1-1-0:(OI)(CI)F /t /q /c', shell=True, capture_output=True, timeout=20)

            os.makedirs(desktop_path, exist_ok=True)
            os.startfile(desktop_path)
            self.log_message.emit(f"✅ Desktop aberto (Permissões resetadas): {desktop_path}")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Não foi possível abrir o Desktop do WinPE:\n{e}")


    def _inject_autostart(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Programa (EXE)", "", "Executáveis (*.exe);;Todos os Arquivos (*.*)"
        )
        if file_path:
            svc = DismService()
            if svc.inject_autostart_program(self._mount_dir, file_path):
                QMessageBox.information(self, "Sucesso", "Programa injetado! Ele iniciará automaticamente com o WinPE.")
                self.log_message.emit(f"Programa de auto-start injetado: {os.path.basename(file_path)}")
            else:
                QMessageBox.warning(self, "Erro", "Falha ao injetar o programa. Verifique os logs.")

    def _inject_drivers(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Selecionar Pasta de Drivers (contendo .inf)"
        )
        if dir_path:
            self.log_message.emit(f"Iniciando injeção de drivers de: {dir_path}")
            svc = DismService()
            # Como drivers podem demorar, o ideal seria um worker, 
            # mas vamos rodar direto por enquanto para seguir o padrão atual das ferramentas
            success = svc.add_drivers(self._mount_dir, dir_path, recurse=True, log_cb=self.log_message.emit)
            if success:
                QMessageBox.information(self, "Sucesso", "Drivers injetados com sucesso!")
                self.log_message.emit("Injeção de drivers concluída.")
            else:
                QMessageBox.warning(self, "Erro", "Falha ao injetar drivers. Verifique os logs.")

    def _inject_package(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Pacote (.cab)", "", "Pacotes (*.cab *.msu)"
        )
        if file_path:
            self.log_message.emit(f"Iniciando injeção de pacote: {file_path}")
            svc = DismService()
            success = svc.add_package(self._mount_dir, file_path, log_cb=self.log_message.emit)
            if success:
                QMessageBox.information(self, "Sucesso", "Pacote injetado com sucesso!")
                self.log_message.emit(f"Pacote {os.path.basename(file_path)} injetado.")
            else:
                QMessageBox.warning(self, "Erro", "Falha ao injetar pacote. Verifique os logs.")

    def _inject_corporate_pack(self):
        """Diálogo para injetar pacote corporativo Dell/HP/Lenovo 8ª gen+."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox, QLabel

        # Resolve caminho dos drivers em tempo de execução
        resources_drivers = _get_resources_drivers()

        # ── Diálogo de seleção ────────────────────────────────────────
        dlg = QDialog(self)
        dlg.setWindowTitle("Pacote Corporativo — Dell/HP/Lenovo 8ª gen+")
        dlg.setMinimumWidth(480)
        layout = QVBoxLayout(dlg)

        layout.addWidget(QLabel(
            "<b>Selecione os pacotes a injetar no boot.wim:</b><br>"
            "<small>Notebooks: Dell Latitude, HP EliteBook, Lenovo ThinkPad — Intel 8ª geração+</small>"
        ))
        layout.addSpacing(8)

        CAT_INFO = {
            "lan":     ("🔌 LAN (Rede Cabeada)",        "Intel I219-LM, Realtek, Others — OBRIGATÓRIO para PXE",  True),
            "storage": ("💾 Mass Storage (NVMe/SATA)",   "Drivers de disco — necessário para ver o HD/SSD",        True),
            "chipset": ("⚙️  Chipset Intel",              "PCH, USB, PCIe — recomendado para 8ª gen+",              False),
            "wlan":    ("📶 Wi-Fi",                       "Intel AX201/9560/8265 — opcional para clonagem via PXE", False),
        }

        checkboxes: dict[str, QCheckBox] = {}
        for cat, (title, desc, default) in CAT_INFO.items():
            packs = CORPORATE_PACKS.get(cat, [])
            has_any = any((resources_drivers / fn).exists() for fn, _ in packs)
            cb = QCheckBox(f"{title}\n  {desc}")
            cb.setChecked(default and has_any)
            cb.setEnabled(has_any)
            if not has_any:
                cb.setText(cb.text() + f"\n  ⚠️ Pacote não encontrado em:\n  {resources_drivers}")
            checkboxes[cat] = cb
            layout.addWidget(cb)

        layout.addSpacing(8)
        layout.addWidget(QLabel(
            "<small>⚠️ O WIM <b>não</b> pode estar montado durante a injeção.<br>"
            "Desmonte antes de continuar.</small>"
        ))

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        selected = [cat for cat, cb in checkboxes.items() if cb.isChecked()]
        if not selected:
            return

        # ── Verificar boot.wim ────────────────────────────────────────
        if not self._boot_wim:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erro", "Nenhum projeto carregado. Abra uma ISO primeiro.")
            return

        if self._is_mounted:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "WIM Montado",
                "Desmonte o WIM antes de injetar drivers.\n"
                "Clique em 'Salvar e Desmontar' primeiro.")
            return

        # ── Iniciar worker ────────────────────────────────────────────
        self.log_message.emit(f"🏢 Iniciando pacote corporativo: {', '.join(selected)}")
        self._btn_corp_drivers.setEnabled(False)
        self._progress.show()
        self._progress.setValue(0)

        self._corp_worker = CorporateDriverWorker(self._boot_wim, selected)
        self._corp_worker.log_message.connect(self.log_message)
        self._corp_worker.progress.connect(self._progress.setValue)
        self._corp_worker.finished.connect(self._on_corp_done)
        self._corp_worker.start()

    def _on_corp_done(self, success: bool, msg: str):
        self._progress.hide()
        self._btn_corp_drivers.setEnabled(True)
        self.log_message.emit(f"{'✅' if success else '❌'} {msg}")
        from PySide6.QtWidgets import QMessageBox
        if success:
            QMessageBox.information(self, "Pacote Corporativo", msg)
        else:
            QMessageBox.critical(self, "Erro", msg)

    def _inject_httpdisk(self):
        url = self._txt_http_url.text().strip()
        if not url:
            QMessageBox.warning(self, "Erro", "Por favor, informe a URL da ISO.")
            return

        self.log_message.emit(f"Iniciando injeção de HTTPDisk para: {url}")
        svc = DismService()
        success = svc.inject_httpdisk(self._mount_dir, url, log_cb=self.log_message.emit)
        if success:
            QMessageBox.information(
                self, "Sucesso", 
                "Suporte a HTTPDisk injetado!\n\n"
                "Ao dar o boot, o WinPE tentará montar a ISO automaticamente no Disco Y:."
            )
        else:
            QMessageBox.warning(self, "Erro", "Falha ao injetar HTTPDisk. Verifique os logs.")
