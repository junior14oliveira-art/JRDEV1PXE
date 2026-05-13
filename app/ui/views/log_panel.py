"""Painel de logs em tempo real."""
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QTextCursor, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QPlainTextEdit,
)


class LogPanelView(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("📋  Logs de Operação")
        title.setObjectName("PageTitle")
        header.addWidget(title)
        header.addStretch()

        btn_clear = QPushButton("Limpar")
        btn_clear.clicked.connect(self._clear)
        header.addWidget(btn_clear)
        root.addLayout(header)

        from PySide6.QtWidgets import QTextEdit
        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setObjectName("LogArea")
        self._text.setStyleSheet("""
            QTextEdit#LogArea {
                background-color: #11111b;
                color: #cdd6f4;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        root.addWidget(self._text, stretch=1)

    @Slot(str)
    def append(self, message: str):
        # Detecção automática de cores baseada em palavras-chave
        color = "#cdd6f4" # Cor padrão (Texto Catppuccin Mocha)
        
        msg_upper = message.upper()
        if any(k in msg_upper for k in ["ERRO", "ERROR", "FALHA", "FAILED", "CRITICAL"]):
            color = "#f38ba8" # Vermelho
        elif any(k in msg_upper for k in ["SUCESSO", "SUCCESS", "CONCLUÍDO", "DONE", "OK"]):
            color = "#a6e3a1" # Verde
        elif any(k in msg_upper for k in ["AVISO", "WARNING", "WARN"]):
            color = "#f9e2af" # Amarelo
        elif any(k in msg_upper for k in ["INFO", "DEBUG"]):
            color = "#89b4fa" # Azul
            
        # Escape de entidades HTML
        from xml.sax.saxutils import escape
        safe_msg = escape(message).replace("\n", "<br>")
        
        html = f'<span style="color: {color};">{safe_msg}</span>'
        self._text.append(html)
        
        # Auto-scroll
        self._text.moveCursor(QTextCursor.MoveOperation.End)

    def _clear(self):
        self._text.clear()
