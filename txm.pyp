"""TXM - Texture Manager plugin dla Cinema 4D."""

import os
import sys

# Dodanie katalogu głównego do PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Importy po dodaniu ścieżki do PYTHONPATH
import c4d
from c4d import plugins

# from __init__ import current_dir
from core.constants import UIConstants
from core.logger import Logger
from core.utils import reload_modules, setup_python_path
from views.dialogs import Dlg

# Inicjalizacja loggera
logger = Logger()
logger.set_logging_mode(
    Logger.LOG_MODE_DEBUG
)  # ten fragment kodu przyszłości do usunięc

# Unikalny ID dla pluginu
PLUGIN_ID = 9234567  # Należy zamienić na własny unikalny ID


class TextureManagerPlugin(plugins.CommandData):
    """Główna klasa pluginu TXM."""

    def __init__(self):
        self.dialog = None

    def Execute(self, doc):
        """Metoda wywoływana przy uruchomieniu pluginu z menu."""
        try:
            logger.info("=" * 50)
            logger.info(
                f"Starting {UIConstants.APP_NAME} Version: {UIConstants.APP_VERSION}"
            )
            logger.info("=" * 50)

            # Konfiguracja środowiska
            setup_python_path()
            logger.debug(f"Katalog roboczy: {current_dir}")

            # Przeładowanie modułów
            reload_modules()

            # Tworzenie i otwieranie głównego dialogu
            if self.dialog is None or not self.dialog.IsOpen():
                logger.debug("Tworzenie głównego okna dialogowego...")
                self.dialog = Dlg()

                logger.debug("Otwieranie okna dialogowego...")
                if self.dialog.Open(c4d.DLG_TYPE_ASYNC, defaultw=1200, defaulth=500):
                    logger.debug("Dialog otwarty pomyślnie")
                else:
                    logger.error("Nie udało się otworzyć dialogu")
            else:
                # Dialog już istnieje, wyciągnij go na wierzch
                self.dialog.Show()

            logger.debug("=" * 50)
            return True

        except (ImportError, RuntimeError) as e:
            logger.error("=" * 50)
            logger.error("Krytyczny błąd podczas inicjalizacji aplikacji:")
            logger.error(f"Error in Execute: {str(e)}")
            logger.error("Szczegóły błędu:", exc_info=True)
            logger.error("=" * 50)
            return False

    def RestoreLayout(self, sec_ref):
        """Przywraca układ okna dialogowego."""
        if self.dialog is None:
            self.dialog = Dlg()
        return self.dialog.Restore(pluginid=PLUGIN_ID, secret=sec_ref)


def PluginMessage(id, data):
    """
    Obsługuje komunikaty pluginu od Cinema 4D.

    Ta funkcja jest wymagana przez API pluginów C4D.
    """
    # Obsługa komunikatów pluginu, np. zamykanie przy wyjściu z C4D
    if id == c4d.C4DPL_ENDACTIVITY:
        # Sprzątanie przy zamknięciu pluginu
        if logger:
            logger.debug("Zamykanie pluginu TXM")
            logger.close()
        # Zamykanie dialogu jeśli jest otwarty
        global_plugin_instance = plugins.FindPlugin(PLUGIN_ID)
        if global_plugin_instance and hasattr(global_plugin_instance, "dialog"):
            if global_plugin_instance.dialog and global_plugin_instance.dialog.IsOpen():
                global_plugin_instance.dialog.Close()

    # Obsługa komunikatu resetowania aplikacji
    elif id == c4d.C4DPL_PROGRAM_STARTED:
        logger.debug("Cinema 4D zostało uruchomione")

    return True


def RegisterTextureManagerPlugin():
    """Rejestruje plugin w systemie Cinema 4D."""
    # Ładowanie ikony z pliku
    icon_path = os.path.join(current_dir, "res", "txm.tif")
    icon = c4d.bitmaps.BaseBitmap()
    if icon.InitWith(icon_path)[0] == c4d.IMAGERESULT_OK:
        logger.debug("Ikona załadowana pomyślnie")
    else:
        logger.warning("Nie udało się załadować ikony")
        icon = None

    return plugins.RegisterCommandPlugin(
        id=PLUGIN_ID,
        str="TXM - Texture Manager",
        help="Zarządzanie teksturami w projekcie",
        info=0,
        icon=icon,
        dat=TextureManagerPlugin(),
    )


# Ta funkcja jest wywoływana przez Cinema 4D przy ładowaniu pluginu
if __name__ == "__main__":
    RegisterTextureManagerPlugin()
