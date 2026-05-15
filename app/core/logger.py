import sys
from loguru import logger
from pathlib import Path

def setup_logger():
    """
    Configura o sistema de logs usando loguru.
    Logs são exibidos no console e salvos em arquivo.
    """
    # Remove o logger padrão
    logger.remove()
    
    # Formato moderno e amigável
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # Adiciona console apenas se stdout existir (não existe em .exe sem console)
    import io
    if sys.stdout is not None and hasattr(sys.stdout, 'buffer'):
        try:
            utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            logger.add(utf8_stdout, format=log_format, level="DEBUG")
        except Exception:
            pass
    elif sys.stdout is not None:
        try:
            logger.add(sys.stdout, format=log_format, level="DEBUG")
        except Exception:
            pass
    
    # Adiciona arquivo de log (rotativo)
    log_file = Path("logs/winpe_studio.log")
    log_file.parent.mkdir(exist_ok=True)
    logger.add(
        log_file,
        format=log_format,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )
    
    logger.info("Logger inicializado com sucesso.")
