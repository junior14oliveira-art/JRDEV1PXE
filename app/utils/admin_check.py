"""Utilitários para verificação e elevação de privilégios administrativos."""
import ctypes
import sys
from loguru import logger


def is_admin() -> bool:
    """Retorna True se o processo atual tem privilégios de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def require_admin() -> None:
    """
    Verifica se o processo é administrador.
    Se não for, relança o processo com UAC (elevação).
    """
    if not is_admin():
        cmd = " ".join(sys.argv)
        logger.warning(f"Sem privilégios de administrador. Tentando elevar: {sys.executable} {cmd}")
        try:
            # ShellExecuteW com 'runas' abre o prompt do UAC
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, cmd, None, 1
            )
            if ret > 32:
                logger.info("Solicitação de elevação enviada com sucesso. Saindo do processo atual.")
                sys.exit(0)
            else:
                logger.error(f"Erro ShellExecuteW: {ret}")
        except Exception as e:
            logger.error(f"Falha ao elevar privilégios: {e}")
            # Se falhar a elevação, continua como usuário comum (o dashboard vai avisar)
    else:
        logger.info("Privilégios de administrador confirmados.")
