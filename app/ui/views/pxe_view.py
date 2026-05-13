"""
View para gerenciamento do Servidor PXE integrado — v3.0
Segue Heurísticas de Nielsen: Visibilidade do status e Controle do Usuário.

Changelog:
  v1.0 — Botao iniciar/parar, combo de interface
  v2.0 — Indicadores de status DHCP/TFTP/HTTP
  v3.0 — Painel de LOG embutido na tela, diagnostico de inicializacao
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QGroupBox, QFormLayout, QFrame, QMessageBox,
    QPlainTextEdit
)
from PySide6.QtCore import Qt, Signal, Slot
from app.core.network.pxe_server import get_network_interfaces, PxeServer, VERSION


class PxeView(QWidget):
    log_message = Signal(str)
    _internal_log = Signal(str)  # Signal thread-safe para logs internos

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_running = False
        self._server = None
        self._project_dir = ""
        self._setup_ui()
        self._load_interfaces()
        # Conectar signal interno ao slot (garante execucao na main thread)
        self._internal_log.connect(self._on_log_received)

    def set_project(self, project_dir: str):
        """Define o projeto atual para o servidor PXE."""
        self._project_dir = project_dir
        self._on_log_received(f"[INFO] Projeto vinculado: {project_dir}")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Cabeçalho com versao
        header = QLabel(f"🚀 Servidor PXE v{VERSION}")
        header.setObjectName("ViewHeader")
        layout.addWidget(header)

        # --- Group: Configurações de Rede ---
        grp_net = QGroupBox("Configurações de Rede")
        form_net = QFormLayout(grp_net)

        self._cb_interface = QComboBox()
        self._cb_interface.currentIndexChanged.connect(self._on_interface_changed)
        form_net.addRow("Placa de Rede:", self._cb_interface)

        self._lbl_ip = QLabel("IP: 0.0.0.0")
        form_net.addRow("Endereço Atual:", self._lbl_ip)

        layout.addWidget(grp_net)

        # --- Group: Status do Servidor ---
        grp_status = QGroupBox("Status dos Serviços")
        status_layout = QHBoxLayout(grp_status)

        self._status_dhcp = self._create_status_indicator("DHCP")
        self._status_tftp = self._create_status_indicator("TFTP")
        self._status_http = self._create_status_indicator("HTTP")

        status_layout.addWidget(self._status_dhcp)
        status_layout.addWidget(self._status_tftp)
        status_layout.addWidget(self._status_http)

        layout.addWidget(grp_status)

        # --- Painel de Controle ---
        ctrl_layout = QHBoxLayout()

        self._btn_start = QPushButton("▶️  INICIAR SERVIDOR")
        self._btn_start.setObjectName("BtnPrimary")
        self._btn_start.setFixedHeight(50)
        self._btn_start.clicked.connect(self._toggle_server)

        self._btn_clear = QPushButton("🗑️ Limpar Log")
        self._btn_clear.setFixedHeight(50)
        self._btn_clear.clicked.connect(lambda: self._log_panel.clear())

        ctrl_layout.addWidget(self._btn_start, stretch=3)
        ctrl_layout.addWidget(self._btn_clear, stretch=1)
        layout.addLayout(ctrl_layout)

        # --- PAINEL DE LOG EMBUTIDO ---
        grp_log = QGroupBox("📋 Log do Servidor PXE (Tempo Real)")
        log_layout = QVBoxLayout(grp_log)

        self._log_panel = QPlainTextEdit()
        self._log_panel.setReadOnly(True)
        self._log_panel.setMaximumBlockCount(500)
        self._log_panel.setStyleSheet(
            "QPlainTextEdit {"
            "  background-color: #1e1e2e;"
            "  color: #cdd6f4;"
            "  font-family: 'Consolas', 'Courier New', monospace;"
            "  font-size: 11px;"
            "  border: 1px solid #45475a;"
            "  border-radius: 4px;"
            "  padding: 8px;"
            "}"
        )
        log_layout.addWidget(self._log_panel)

        layout.addWidget(grp_log, stretch=1)

    def _create_status_indicator(self, name):
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        l = QVBoxLayout(frame)

        lbl_name = QLabel(name)
        lbl_name.setAlignment(Qt.AlignCenter)
        lbl_name.setStyleSheet("font-weight: bold;")

        indicator = QLabel("OFFLINE")
        indicator.setAlignment(Qt.AlignCenter)
        indicator.setStyleSheet("color: #f38ba8; font-weight: bold;")

        l.addWidget(lbl_name)
        l.addWidget(indicator)

        setattr(self, f"_ind_{name.lower()}", indicator)
        return frame

    def _toggle_server(self):
        if not self._is_running:
            self._start_server()
        else:
            self._stop_server()

    def _emit_log(self, msg: str):
        """Chamado pelas threads do servidor. Emite signal thread-safe."""
        self._internal_log.emit(msg)

    @Slot(str)
    def _on_log_received(self, msg: str):
        """Slot executado na main thread. Atualiza UI com seguranca."""
        self._log_panel.appendPlainText(msg)
        sb = self._log_panel.verticalScrollBar()
        sb.setValue(sb.maximum())
        self.log_message.emit(msg)

    def _start_server(self):
        ip = self._cb_interface.currentData()
        mask = self._cb_interface.itemData(
            self._cb_interface.currentIndex(), Qt.UserRole + 1
        )

        if not ip or ip == "0.0.0.0":
            QMessageBox.warning(self, "Erro", "Selecione uma placa de rede válida.")
            return

        if not self._project_dir:
            self._on_log_received("[AVISO] Nenhum projeto carregado. Boot pode falhar.")

        try:
            self._is_running = True
            self._btn_start.setText("⏹️  PARAR SERVIDOR")
            self._btn_start.setStyleSheet(
                "background-color: #f38ba8; color: white;"
            )

            self._server = PxeServer(
                ip, mask or "255.255.255.0", self._project_dir or ""
            )
            self._server.start(log_cb=self._emit_log)

            self._ind_dhcp.setText("ONLINE")
            self._ind_dhcp.setStyleSheet("color: #a6e3a1; font-weight: bold;")
            self._ind_tftp.setText("ONLINE")
            self._ind_tftp.setStyleSheet("color: #a6e3a1; font-weight: bold;")
            self._ind_http.setText("ONLINE")
            self._ind_http.setStyleSheet("color: #a6e3a1; font-weight: bold;")

        except Exception as e:
            self._on_log_received(f"[ERRO FATAL] {e}")
            self._stop_server()

    def _stop_server(self):
        self._is_running = False
        if self._server:
            self._server.stop(log_cb=self._emit_log)
            self._server = None

        self._btn_start.setText("▶️  INICIAR SERVIDOR")
        self._btn_start.setStyleSheet("")
        self._ind_dhcp.setText("OFFLINE")
        self._ind_dhcp.setStyleSheet("color: #f38ba8; font-weight: bold;")
        self._ind_tftp.setText("OFFLINE")
        self._ind_tftp.setStyleSheet("color: #f38ba8; font-weight: bold;")
        self._ind_http.setText("OFFLINE")
        self._ind_http.setStyleSheet("color: #f38ba8; font-weight: bold;")

    def _load_interfaces(self):
        """Carrega as interfaces de rede no combo box."""
        self._interfaces = get_network_interfaces()
        self._cb_interface.clear()
        for iface in self._interfaces:
            self._cb_interface.addItem(
                f"{iface['name']} ({iface['ip']})", iface['ip']
            )
            idx = self._cb_interface.count() - 1
            self._cb_interface.setItemData(idx, iface['mask'], Qt.UserRole + 1)

        if not self._interfaces:
            self._cb_interface.addItem("Nenhuma interface encontrada", "0.0.0.0")

    def _on_interface_changed(self):
        """Atualiza o label do IP quando o usuário troca a placa."""
        ip = self._cb_interface.currentData()
        self._lbl_ip.setText(f"IP: {ip}")
