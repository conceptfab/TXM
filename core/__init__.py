"""Moduł core zawierający podstawowe komponenty aplikacji TXM.

Zawiera:
- Logger - system logowania
- Controller - główny kontroler aplikacji
- files_worker - narzędzia do pracy z plikami
- files_analyzer - analizator plików
- models - modele danych
"""

from .logger import Logger

# Inicjalizacja loggera
logger = Logger()

try:
    logger.debug("Próba importu files_worker")
    from . import files_worker, models

    logger.debug("Import files_worker i models udany")
except ImportError as e:
    logger.error(f"Błąd importu: {e}")

try:
    logger.debug("Próba importu files_analyzer")
    from . import files_analyzer

    logger.debug("Import files_analyzer udany")
except ImportError as e:
    logger.error(f"Import files_analyzer nieudany: {str(e)}")
    raise

try:
    logger.debug("Próba importu Controller z controller")
    from .controller import Controller

    logger.debug("Import Controller udany")
except ImportError as e:
    logger.error(f"Błąd podczas importu Controller: {str(e)}")
    raise

__all__ = [
    "Controller",
    "files_worker",
    "files_analyzer",
    "analyze_c4d_textures",
    "models",
]
