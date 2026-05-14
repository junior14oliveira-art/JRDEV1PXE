"""Aba 'Sobre' — JRDEV1 PXE."""
import sys
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QLinearGradient
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea,
)


def _get_resources_path() -> Path:
    """Retorna o caminho da pasta resources — funciona como script e como .exe."""
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent.parent.parent  # app/
    return base / "resources"


def _load_pixmap(filename: str, fallback_size: tuple = (200, 200)) -> QPixmap:
    """Carrega um pixmap da pasta resources. Retorna pixmap vazio se não encontrar."""
    path = _get_resources_path() / filename
    if path.exists():
        px = QPixmap(str(path))
        if not px.isNull():
            return px
    # Fallback: pixmap vazio
    px = QPixmap(*fallback_size)
    px.fill(QColor("#1A3A6B"))
    return px


class _BannerWidget(QWidget):
    """Widget que exibe a imagem JRDEV1_Wallpaper_WinPE.jpg como fundo com overlay escuro."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(220)
        self._bg = _load_pixmap("JRDEV1_Wallpaper_WinPE.jpg", (1920, 1080))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Imagem de fundo centralizada e cortada para preencher o widget
        w, h = self.width(), self.height()
        img_w, img_h = self._bg.width(), self._bg.height()

        # Escala mantendo proporção para cobrir o widget
        scale = max(w / img_w, h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        x = (w - new_w) // 2
        y = (h - new_h) // 2

        p.drawPixmap(x, y, new_w, new_h, self._bg)

        # Overlay gradiente escuro para legibilidade do texto
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(9, 20, 40, 180))   # #091428 com alpha
        grad.setColorAt(0.5, QColor(9, 20, 40, 120))
        grad.setColorAt(1.0, QColor(9, 20, 40, 220))
        p.fillRect(0, 0, w, h, QBrush(grad))

        p.end()


class AboutView(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Banner com wallpaper JRDEV1 ───────────────────────────── #
        banner = _BannerWidget()
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(0, 0, 0, 0)
        banner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo sobre o banner — usa JRDEV1.jpg (1024x1024, alta resolução)
        lbl_logo_img = QLabel()
        lbl_logo_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_px = _load_pixmap("JRDEV1.jpg", (140, 140))
        # Recorta em círculo
        logo_size = 110
        logo_px_scaled = logo_px.scaled(
            logo_size, logo_size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        # Cria pixmap circular
        circular = QPixmap(logo_size, logo_size)
        circular.fill(Qt.GlobalColor.transparent)
        cp = QPainter(circular)
        cp.setRenderHint(QPainter.RenderHint.Antialiasing)
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.addEllipse(0, 0, logo_size, logo_size)
        cp.setClipPath(path)
        ox = (logo_px_scaled.width() - logo_size) // 2
        oy = (logo_px_scaled.height() - logo_size) // 2
        cp.drawPixmap(-ox, -oy, logo_px_scaled)
        # Borda azul
        from PySide6.QtGui import QPen
        cp.setClipping(False)
        cp.setPen(QPen(QColor("#2E6BE6"), 3))
        cp.drawEllipse(2, 2, logo_size - 4, logo_size - 4)
        cp.end()

        lbl_logo_img.setPixmap(circular)
        banner_layout.addWidget(lbl_logo_img)

        # Nome sobre o banner
        lbl_name_banner = QLabel("JRDEV1 PXE")
        lbl_name_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_name_banner.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #FFFFFF; "
            "letter-spacing: 4px; background: transparent;"
        )
        banner_layout.addWidget(lbl_name_banner)

        lbl_sub_banner = QLabel("WinPE Studio Pro  •  v2.1.0")
        lbl_sub_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub_banner.setStyleSheet(
            "font-size: 13px; color: #7AB4FF; background: transparent; letter-spacing: 1px;"
        )
        banner_layout.addWidget(lbl_sub_banner)

        root.addWidget(banner)

        # ── Área de conteúdo com scroll ───────────────────────────── #
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #0D1B3E; border: none; }")

        content = QWidget()
        content.setStyleSheet("background-color: #0D1B3E;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(60, 32, 60, 40)
        content_layout.setSpacing(20)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Descrição ─────────────────────────────────────────────── #
        lbl_desc = QLabel(
            "Solução profissional para boot PXE, clonagem e customização\n"
            "de imagens WinPE em redes corporativas.\n\n"
            "Compatível com Dell Latitude, HP EliteBook e Lenovo ThinkPad\n"
            "a partir da 8ª geração Intel."
        )
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setStyleSheet("font-size: 14px; color: #7A9CC8; line-height: 1.8;")
        content_layout.addWidget(lbl_desc)

        # ── Separador ─────────────────────────────────────────────── #
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #1A3A6B; max-height: 1px; border: none;")
        content_layout.addWidget(sep)

        # ── Card do desenvolvedor ─────────────────────────────────── #
        dev_frame = QFrame()
        dev_frame.setStyleSheet("""
            QFrame {
                background-color: #1A3A6B;
                border: 1px solid #2A4A7B;
                border-radius: 14px;
            }
        """)
        dev_layout = QVBoxLayout(dev_frame)
        dev_layout.setContentsMargins(32, 24, 32, 24)
        dev_layout.setSpacing(10)

        lbl_dev_title = QLabel("DESENVOLVIDO POR")
        lbl_dev_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_dev_title.setStyleSheet(
            "font-size: 10px; color: #4A6FA5; letter-spacing: 3px; "
            "background: transparent; border: none;"
        )
        dev_layout.addWidget(lbl_dev_title)

        lbl_dev_name = QLabel("JRDEV1")
        lbl_dev_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_dev_name.setStyleSheet(
            "font-size: 30px; font-weight: bold; color: #FFFFFF; "
            "letter-spacing: 4px; background: transparent; border: none;"
        )
        dev_layout.addWidget(lbl_dev_name)

        lbl_dev_role = QLabel("Software Developer  •  </> Código  💡 Inovação")
        lbl_dev_role.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_dev_role.setStyleSheet(
            "font-size: 13px; color: #4A6FA5; background: transparent; border: none;"
        )
        dev_layout.addWidget(lbl_dev_role)

        dev_layout.addSpacing(16)

        # Linha Instagram
        lbl_ig_label = QLabel("INSTAGRAM")
        lbl_ig_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ig_label.setStyleSheet(
            "font-size: 10px; color: #4A6FA5; letter-spacing: 3px; "
            "background: transparent; border: none;"
        )
        dev_layout.addWidget(lbl_ig_label)

        btn_ig = QPushButton("  📸  @jrdev1")
        btn_ig.setFixedHeight(44)
        btn_ig.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #833AB4,
                    stop:0.5 #E1306C,
                    stop:1 #F77737
                );
                color: white;
                border: none;
                border-radius: 22px;
                padding: 0 40px;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9B4FCC,
                    stop:0.5 #F04080,
                    stop:1 #FF8C4A
                );
            }
        """)
        btn_ig.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ig.clicked.connect(self._open_instagram)
        dev_layout.addWidget(btn_ig, alignment=Qt.AlignmentFlag.AlignCenter)

        content_layout.addWidget(dev_frame)

        # ── Recursos do sistema ───────────────────────────────────── #
        feat_frame = QFrame()
        feat_frame.setStyleSheet("""
            QFrame {
                background-color: #091428;
                border: 1px solid #1A3A6B;
                border-radius: 14px;
            }
        """)
        feat_layout = QVBoxLayout(feat_frame)
        feat_layout.setContentsMargins(28, 20, 28, 20)
        feat_layout.setSpacing(8)

        lbl_feat_title = QLabel("RECURSOS")
        lbl_feat_title.setStyleSheet(
            "font-size: 10px; color: #4A6FA5; letter-spacing: 3px; "
            "background: transparent; border: none;"
        )
        feat_layout.addWidget(lbl_feat_title)

        features = [
            ("📡", "Servidor PXE/TFTP/DHCP integrado"),
            ("💾", "Injeção de drivers corporativos (Dell/HP/Lenovo)"),
            ("🌐", "Boot via rede com wimboot + HTTPDisk"),
            ("🎨", "Customização completa do WinPE (wallpaper, desktop, autostart)"),
            ("⚙️",  "Geração de ISO bootável UEFI + BIOS"),
            ("🔑", "Sistema de licenciamento por hardware"),
        ]
        for icon, text in features:
            row = QHBoxLayout()
            row.setSpacing(10)
            lbl_i = QLabel(icon)
            lbl_i.setFixedWidth(24)
            lbl_i.setStyleSheet("background: transparent; border: none; font-size: 15px;")
            lbl_t = QLabel(text)
            lbl_t.setStyleSheet("color: #7A9CC8; font-size: 13px; background: transparent; border: none;")
            row.addWidget(lbl_i)
            row.addWidget(lbl_t)
            row.addStretch()
            feat_layout.addLayout(row)

        content_layout.addWidget(feat_frame)

        # ── Rodapé ────────────────────────────────────────────────── #
        lbl_footer = QLabel("© 2024–2026 JRDEV1  •  Todos os direitos reservados")
        lbl_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_footer.setStyleSheet(
            "font-size: 11px; color: #2A4A7B; background: transparent;"
        )
        content_layout.addWidget(lbl_footer)

        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

    def _open_instagram(self):
        import subprocess
        subprocess.Popen(
            ["cmd", "/c", "start", "https://www.instagram.com/jrdev1"],
            shell=False
        )
