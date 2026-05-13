"""Operações de arquivo seguras: cópia, movimentação e verificação de integridade."""
import hashlib
import shutil
from pathlib import Path
from typing import Callable
from loguru import logger


def copy_file(src: str | Path, dst: str | Path,
              progress_cb: Callable[[int, int], None] | None = None) -> bool:
    """
    Copia um arquivo de src para dst, com callback opcional de progresso.
    progress_cb(bytes_copied, total_bytes)
    """
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    total = src.stat().st_size
    copied = 0
    chunk = 1024 * 1024  # 1 MB
    try:
        with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
            while chunk_data := fsrc.read(chunk):
                fdst.write(chunk_data)
                copied += len(chunk_data)
                if progress_cb:
                    progress_cb(copied, total)
        logger.debug(f"Arquivo copiado: {src} → {dst}")
        return True
    except Exception as e:
        logger.error(f"Erro ao copiar '{src}' para '{dst}': {e}")
        return False


def move_file(src: str | Path, dst: str | Path) -> bool:
    """Move um arquivo ou diretório."""
    try:
        shutil.move(str(src), str(dst))
        logger.debug(f"Movido: {src} → {dst}")
        return True
    except Exception as e:
        logger.error(f"Erro ao mover '{src}': {e}")
        return False


def calculate_sha256(path: str | Path) -> str:
    """Calcula o hash SHA-256 de um arquivo."""
    sha256 = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        logger.error(f"Erro ao calcular hash de '{path}': {e}")
        return ""


def list_executables(directory: str | Path) -> list[Path]:
    """Lista todos os executáveis (.exe, .bat, .cmd) em um diretório (recursivo)."""
    p = Path(directory)
    exts = {".exe", ".bat", ".cmd", ".ps1"}
    return [f for f in p.rglob("*") if f.suffix.lower() in exts]
