"""Aba 'Sobre' — JRDEV1 PXE."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame,
)


def _make_logo_pixmap(size: int = 120) -> QPixmap:
    """
    Desenha a logo JRDEV1 programaticamente:
    círculo azul marinho + </> + lâmpada estilizada + faixa JRDEV1.
    """
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    cx, cy, r = size // 2, size // 2, size // 2 - 2

    # Círculo externo
    p.setPen(QPen(QColor("#1A3A6B"), 4))
    p.setBrush(QBrush(QColor("#0D1B3E")))
    p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

    # Texto </> no centro-esquerda
    font = QFont("Consolas", size // 8, QFont.Weight.Bold)
    p.setFont(font)
    p.setPen(QColor("#2E6BE6"))
    p.drawText(int(cx - r * 0.75), int(cy - r * 0.05),
               int(r * 0.9), int(r * 0.6),
               Qt.AlignmentFlag.AlignCenter, "</>")

    # Faixa inferior
    import math
    faixa_y = int(cy + r * 0.45)
    faixa_h = int(r * 0.55)
    p.setBrush(QBrush(QColor("#1A3A6B")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawChord(cx - r + 2, cy - r + 2, (r - 2) * 2, (r - 2) * 2,
                0 * 16, -180 * 16)

    # Texto JRDEV1 na faixa
    font2 = QFont("Segoe UI", size // 9, QFont.Weight.Bold)
    p.setFont(font2)
    p.setPen(QColor("#FFFFFF"))
    p.drawText(cx - r, faixa_y - 4, r * 2, faixa_h,
               Qt.AlignmentFlag.AlignCenter, "JRDEV1")

    p.end()
    return px


class AboutView(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Fundo com gradiente via widget filho
        bg = QFrame()
        bg.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #091428,
                    stop:1 #0D1B3E
                );
            }
        """)
        bg_layout = QVBoxLayout(bg)
        bg_layout.setContentsMargins(60, 50, 60, 50)
        bg_layout.setSpacing(0)
        bg_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ── Logo ──────────────────────────────────────────────────── #
        lbl_logo = QLabel()
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        px = _make_logo_pixmap(140)
        lbl_logo.setPixmap(px)
        bg_layout.addWidget(lbl_logo)

        bg_layout.addSpacing(20)

        # ── Nome do programa ──────────────────────────────────────── #
        lbl_name = QLabel("JRDEV1 PXE")
        lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_name.setStyleSheet(
            "font-size: 36px; font-weight: bold; color: #FFFFFF; letter-spacing: 3px;"
        )
        bg_layout.addWidget(lbl_name)

        lbl_sub = QLabel("WinPE Studio Pro")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet("font-size: 15px; color: #4A6FA5; letter-spacing: 2px;")
        bg_layout.addWidget(lbl_sub)

        bg_layout.addSpacing(8)

        # Versão
        lbl_ver = QLabel("Versão 2.1.0")
        lbl_ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ver.setStyleSheet("font-size: 12px; color: #2E6BE6;")
        bg_layout.addWidget(lbl_ver)

        bg_layout.addSpacing(32)

        # ── Separador ─────────────────────────────────────────────── #
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #1A3A6B; background: #1A3A6B; max-height: 1px;")
        bg_layout.addWidget(sep)

        bg_layout.addSpacing(28)

        # ── Descrição ─────────────────────────────────────────────── #
        lbl_desc = QLabel(
            "Solução profissional para boot PXE, clonagem e\n"
            "customização de imagens WinPE em redes corporativas."
        )
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setStyleSheet("font-size: 14px; color: #7A9CC8; line-height: 1.6;")
        bg_layout.addWidget(lbl_desc)

        bg_layout.addSpacing(32)

        # ── Desenvolvedor ─────────────────────────────────────────── #
        dev_frame = QFrame()
        dev_frame.setStyleSheet("""
            QFrame {
                background-color: #1A3A6B;
                border: 1px solid #2A4A7B;
                border-radius: 12px;
            }
        """)
        dev_layout = QVBoxLayout(dev_frame)
        dev_layout.setContentsMargins(28, 20, 28, 20)
        dev_layout.setSpacing(8)

        lbl_dev_title = QLabel("Desenvolvido por")
        lbl_dev_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_dev_title.setStyleSheet("font-size: 11px; color: #4A6FA5; text-transform: uppercase; letter-spacing: 2px;")
        dev_layout.addWidget(lbl_dev_title)

        lbl_dev_name = QLabel("JRDEV1")
        lbl_dev_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_dev_name.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #FFFFFF; letter-spacing: 2px;"
        )
        dev_layout.addWidget(lbl_dev_name)

        lbl_dev_role = QLabel("Software Developer  •  </> Código  💡 Inovação")
        lbl_dev_role.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_dev_role.setStyleSheet("font-size: 12px; color: #4A6FA5;")
        dev_layout.addWidget(lbl_dev_role)

        dev_layout.addSpacing(12)

        # Instagram
        lbl_ig_title = QLabel("Instagram")
        lbl_ig_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ig_title.setStyleSheet("font-size: 11px; color: #4A6FA5; text-transform: uppercase; letter-spacing: 1px;")
        dev_layout.addWidget(lbl_ig_title)

        btn_ig = QPushButton("📸  @jrdev1")
        btn_ig.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #833AB4, stop:0.5 #E1306C, stop:1 #F77737
                );
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 32px;
                font-size: 15px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9B4FCC, stop:0.5 #F04080, stop:1 #FF8C4A
                );
            }
        """)
        btn_ig.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ig.clicked.connect(self._open_instagram)
        dev_layout.addWidget(btn_ig, alignment=Qt.AlignmentFlag.AlignCenter)

        bg_layout.addWidget(dev_frame)

        bg_layout.addSpacing(28)

        # ── Rodapé ────────────────────────────────────────────────── #
        lbl_footer = QLabel("© 2024-2026 JRDEV1 — Todos os direitos reservados")
        lbl_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_footer.setStyleSheet("font-size: 11px; color: #2A4A7B;")
        bg_layout.addWidget(lbl_footer)

        root.addWidget(bg)

    def _open_instagram(self):
        import subprocess
        subprocess.Popen(
            ["cmd", "/c", "start", "https://www.instagram.com/jrdev1"],
            shell=False
        )
