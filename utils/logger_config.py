import logging
import sys
from pathlib import Path
from datetime import datetime

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    class Fore:
        CYAN = ''
    class Style:
        RESET_ALL = ''

def setup_logging() -> logging.Logger:
    """
    Configura el sistema de logging para la aplicación.

    Crea un directorio 'logs' si no existe y configura dos handlers:
    - Un StreamHandler para la consola con formato de color.
    - Un FileHandler para guardar logs en un archivo diario.

    Returns:
        logging.Logger: El objeto logger configurado.
    """
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"integrated_app_{datetime.now().strftime('%Y%m%d')}.log"
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Evitar añadir múltiples handlers si la función se llama varias veces
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # Formateador para la consola con colores
    console_formatter = logging.Formatter(f'{Fore.CYAN}%(asctime)s{Style.RESET_ALL} - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    
    # Formateador para el archivo
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()
