import importlib
import os
import sys

# Globalny logger
from core.logger import Logger

logger = Logger()


# Dodanie katalogu głównego do PYTHONPATH
def setup_python_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)
    return current_dir


# Globalna zmienna statusu
_global_status = "Ready"


def get_global_status() -> str:
    """Pobiera aktualny globalny status aplikacji."""
    try:
        import core.controller

        status_text = core.controller.status()
        logger.debug(f"Pobrany status z kontrolera: {status_text}")
        return status_text
    except Exception as e:
        logger.error(f"Błąd podczas pobierania statusu: {str(e)}")
        return "Error"


def set_global_status(status: str) -> None:
    """Ustawia globalny status aplikacji."""
    global _global_status
    _global_status = status
    logger.debug(f"Status zmieniony na: {status}")


def format_file_size(size_in_bytes: int) -> str:
    """Formatuje rozmiar pliku do czytelnej postaci."""
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes/1024:.1f} KB"
    else:
        return f"{size_in_bytes/(1024*1024):.1f} MB"


def reload_modules():
    """Przeładowanie modułów, aby zapewnić aktualność kodu."""
    try:
        import core.controller

        importlib.reload(core.controller)
        logger.debug("Pomyślnie przeładowano moduły core")
        return True
    except Exception as e:
        logger.error(f"Błąd podczas przeładowania modułów: {str(e)}")
        return False
