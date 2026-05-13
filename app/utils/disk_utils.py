"""Utilitários de disco: espaço livre, validações de caminho."""
import shutil
from pathlib import Path
from loguru import logger


def get_free_space_gb(path: str | Path = "C:\\") -> float:
    """Retorna o espaço livre em GB para o disco que contém o caminho dado."""
    try:
        total, used, free = shutil.disk_usage(str(path))
        return round(free / (1024 ** 3), 2)
    except Exception as e:
        logger.warning(f"Não foi possível verificar espaço em disco: {e}")
        return 0.0


def get_file_size_mb(path: str | Path) -> float:
    """Retorna o tamanho de um arquivo em MB."""
    try:
        return round(Path(path).stat().st_size / (1024 ** 2), 2)
    except Exception:
        return 0.0


def ensure_dir(path: str | Path) -> Path:
    """Garante que um diretório existe, criando-o se necessário."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_remove(path: str | Path) -> bool:
    """Remove um arquivo ou diretório de forma segura, sem lançar exceção."""
    import shutil as _shutil
    p = Path(path)
    try:
        if p.is_dir():
            _shutil.rmtree(p)
        elif p.is_file():
            p.unlink()
        return True
    except Exception as e:
        logger.error(f"Erro ao remover '{p}': {e}")
        return False
