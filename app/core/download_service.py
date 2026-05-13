"""Serviço para baixar imagens base de WinPE."""
import os
import requests
from pathlib import Path
from typing import Callable
from loguru import logger

class DownloadService:
    """Lida com downloads de arquivos grandes com feedback de progresso."""

    def download_file(
        self, 
        url: str, 
        dest_path: str | Path, 
        progress_cb: Callable[[int], None] | None = None,
        log_cb: Callable[[str], None] | None = None
    ) -> bool:
        """Faz download de uma URL para dest_path."""
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if log_cb: log_cb(f"Iniciando download de: {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_cb and total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            progress_cb(percent)

            if log_cb: log_cb(f"Download concluído: {dest_path.name}")
            return True
        except Exception as e:
            logger.error(f"Erro no download: {e}")
            if log_cb: log_cb(f"ERRO: {e}")
            return False
