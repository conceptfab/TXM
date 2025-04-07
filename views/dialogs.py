import c4d

from core.constants import (
    GROUP_H_CENTER,
    GROUP_V_CENTER,
    SPACER_BOTTOM,
    SPACER_LEFT,
    SPACER_RIGHT,
    SPACER_TOP,
    UIConstants,
)
from core.controllers import StatusManager, TextureController
from core.logger import Logger
from core.models import TextureManager
from core.utils import format_file_size, get_global_status
from views.builders import MenuBuilder
from views.tabs import SettingsTab, TexturesTab

logger = Logger()


class AboutDialog(c4d.gui.GeDialog):
    """Dialog z informacjami o aplikacji."""

    def CreateLayout(self):
        """Tworzy układ dialogu "O programie"."""
        self.SetTitle("About TXM")

        self.GroupBegin(
            GROUP_V_CENTER, c4d.BFV_SCALEFIT | c4d.BFH_SCALEFIT, cols=1, rows=5
        )
        self.GroupSpace(0, 0)

        self.AddStaticText(SPACER_TOP, c4d.BFV_SCALEFIT, name="")
        self.AddStaticText(
            0, c4d.BFH_CENTER, name=f"{UIConstants.APP_NAME} v{UIConstants.APP_VERSION}"
        )
        self.AddStaticText(SPACER_TOP, c4d.BFV_SCALEFIT, name="")

        self.GroupBegin(GROUP_H_CENTER, c4d.BFH_SCALEFIT, cols=3, rows=1)
        self.GroupSpace(0, 0)

        self.AddStaticText(SPACER_LEFT, c4d.BFH_SCALEFIT, name="")
        self.AddStaticText(0, c4d.BFH_CENTER, name="Zbudowane przez CURSORA")
        self.AddStaticText(SPACER_RIGHT, c4d.BFH_SCALEFIT, name="")

        self.GroupEnd()

        self.AddStaticText(SPACER_BOTTOM, c4d.BFV_SCALEFIT, name="")
        self.GroupEnd()

        return True


class Dlg(c4d.gui.GeDialog):
    """Główny dialog aplikacji TXM."""

    # Stałe dla głównego okna
    WINDOW_WIDTH = UIConstants.WINDOW_WIDTH
    WINDOW_HEIGHT = UIConstants.WINDOW_HEIGHT
    WINDOW_MARGIN = UIConstants.MARGIN_GROUP
    BUTTON_WIDTH = 100
    BUTTON_HEIGHT = 20
    BUTTON_SPACING = 5

    # Stałe dla menu
    MENU_VIEW = 20000
    MENU_VIEW_OPTION1 = 20001
    MENU_VIEW_OPTION2 = 20002
    MENU_ABOUT = 20010
    MENU_ABOUT_INFO = 20011

    # Stałe dla zakładek
    TAB_GROUP = 10001
    FIRST_TAB = 10010
    SECOND_TAB = 10020

    def __init__(self):
        """Inicjalizuje główny dialog aplikacji."""
        try:
            logger.debug("=" * 30)
            logger.debug("Inicjalizacja głównego okna dialogowego")
            super(Dlg, self).__init__()

            # Konfiguracja podstawowych parametrów
            self._first_tab_visible = True
            self.treeview = None

            # Inicjalizacja menedżera tekstur i załadowanie przykładowych danych
            self._texture_manager = TextureManager()
            self._texture_manager.load_sample_textures()  # Użyj naszych przykładowych tekstur zamiast losowych
            self.list_view = None

            # Inicjalizacja komponentów UI
            self.menu_builder = MenuBuilder(self)
            self.textures_tab = TexturesTab(self, self._texture_manager)
            self.settings_tab = SettingsTab(self)

            # Inicjalizacja kontrolera tekstur
            self.texture_controller = TextureController(self._texture_manager, self)

            # Pobranie początkowego statusu
            self._current_status = get_global_status()

            # Inicjalizacja managera statusu
            self.status_manager = StatusManager(self, self._current_status)

            logger.debug("Dialog zainicjalizowany pomyślnie")
            logger.debug("=" * 30)
        except Exception as e:
            logger.error("Błąd podczas inicjalizacji dialogu:")
            logger.error(f"Error in Dialog initialization: {str(e)}")
            logger.error("Szczegóły błędu:", exc_info=True)
            raise

    def CreateLayout(self):
        """Tworzy układ głównego dialogu."""
        try:
            self.SetTitle(UIConstants.WINDOW_TITLE)

            # Menu górne
            self.menu_builder.build()

            # Używamy stałych wartości dla wymiarów okna
            window_w = self.WINDOW_WIDTH
            window_h = self.WINDOW_HEIGHT

            # Główna grupa określająca wymiary okna
            if not self.GroupBegin(
                1000,
                c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT,
                1,
                1,
                title="",
                initw=window_w,
                inith=window_h,
            ):
                return False

            # Główny layout - grupa zakładek
            tab_flags = c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT
            if self.TabGroupBegin(self.TAB_GROUP, tab_flags, tabtype=c4d.TAB_TABS):
                # Tworzenie zakładek
                self.textures_tab.build(self.FIRST_TAB)
                self.settings_tab.build(self.SECOND_TAB)

                self.GroupEnd()  # Koniec TabGroup
            self.GroupEnd()  # Koniec głównej grupy

            # Inicjalizacja wartości i stanu UI
            self.calc_selected()

            return True
        except Exception as e:
            logger.error(f"Błąd podczas tworzenia layoutu: {str(e)}")
            return False

    def InitValues(self):
        """Inicjalizuje wartości w dialogu."""
        try:
            # Wyczyść tabelę na starcie
            self._texture_manager.clear()

            # Aktualizuj UI
            self.calc_selected()

            # Ustaw stan przycisków
            self.texture_controller.setup_initial_button_state(self._current_status)

            # Aktywuj przycisk Load Textures
            self.Enable(UIConstants.BTN_BROWSE, True)

            return True
        except Exception as e:
            logger.error(f"Błąd w InitValues: {str(e)}")
            return False

    def Command(self, id, msg):
        """Obsługuje zdarzenia w dialogu."""
        try:
            # Obsługa przełączania zakładek
            if id == self.TAB_GROUP:
                tab_value = msg.GetInt32(c4d.BFM_GETVALUE)
                return True

            # Obsługa menu
            elif id == self.MENU_VIEW_OPTION1 or id == self.MENU_VIEW_OPTION2:
                return True
            elif id == self.MENU_ABOUT_INFO:
                dialog = AboutDialog()
                return dialog.Open(c4d.DLG_TYPE_MODAL, defaultw=300, defaulth=200)

            # Aktualizacja statusu
            elif id == UIConstants.STATUS_BAR_TEXT:
                return True

            # Obsługa przycisków
            elif id == UIConstants.BTN_PROCESS_SELECTED:
                result = self.texture_controller.toggle_selection()
                self.calc_selected()
                return result
            elif id == UIConstants.BTN_BROWSE:
                # Automatycznie użyj folderu tekstur aktywnego dokumentu C4D
                return self.texture_controller.load_textures_from_directory()
            elif id == UIConstants.BTN_CLEAR:
                return self.texture_controller.clear_textures()
            elif id == UIConstants.BTN_REFRESH:
                self.treeview.Refresh()
                return self.texture_controller.update_ui_state()
            elif id == UIConstants.PROGRESS_BTN:
                logger.debug("Kliknięto przycisk z paskiem postępu")
                return self.texture_controller.process_with_progress()
            elif id in [UIConstants.BTN_IMPORT, UIConstants.BTN_EXPORT]:
                return self._handle_button_click(id)

            return True
        except Exception as e:
            logger.error(f"Błąd: {str(e)}")
            return False

    def _handle_button_click(self, button_id: int) -> bool:
        """Obsługuje kliknięcie przycisku."""
        try:
            button_names = {
                UIConstants.BTN_IMPORT: "Import",
                UIConstants.BTN_EXPORT: "Export",
                UIConstants.BTN_REFRESH: "Refresh",
                UIConstants.BTN_CLEAR: "Clear",
            }
            button_name = button_names.get(button_id, "Unknown")
            c4d.gui.MessageDialog(f"Kliknięto przycisk: {button_name}")
            return True
        except Exception as e:
            logger.error(f"Błąd podczas obsługi kliknięcia przycisku: {str(e)}")
            return False

    def calc_selected(self) -> bool:
        """Oblicza i aktualizuje informacje o zaznaczeniu."""
        try:
            if hasattr(self, "texture_controller"):
                self.texture_controller.update_selection_info()
                self.texture_controller.update_ui_state()  # Dodane - aktualizacja stanu przycisków

                # Aktualizacja głównego statusu
                selected_count = self._texture_manager.count_selected()
                total_count = self._texture_manager.get_texture_count()
                selected_size = self._texture_manager.calculate_selected_size()

                status_text = f"Zaznaczono {selected_count} z {total_count} plików ({format_file_size(selected_size)})"
                self.SetString(UIConstants.STATUS_TOTAL_SIZE, f"Status: {status_text}")

                return True
            return False
        except Exception as e:
            logger.error(f"Błąd w calc_selected: {str(e)}")
            return False
