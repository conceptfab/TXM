from typing import List, Tuple

import c4d
import c4d.gui

from core.constants import UIConstants
from core.logger import Logger

logger = Logger()


class MenuBuilder:
    """Buduje menu aplikacji."""

    def __init__(self, dialog):
        self.dialog = dialog

    def build(self):
        """Tworzy strukturę menu."""
        try:
            self.dialog.MenuFlushAll()
            if self.dialog.MenuSubBegin("View"):
                self.dialog.MenuAddString(self.dialog.MENU_VIEW_OPTION1, "Option 1")
                self.dialog.MenuAddString(self.dialog.MENU_VIEW_OPTION2, "Option 2")
                self.dialog.MenuSubEnd()
            if self.dialog.MenuSubBegin("About"):
                self.dialog.MenuAddString(self.dialog.MENU_ABOUT_INFO, "Info")
                self.dialog.MenuSubEnd()
            return True
        except Exception as e:
            logger.error(f"Błąd podczas tworzenia menu: {str(e)}")
            return False


class TreeViewBuilder:
    """Buduje widok drzewa tekstur."""

    def __init__(self, dialog, texture_manager):
        self.dialog = dialog
        self.texture_manager = texture_manager

    def build(self):
        """Tworzy kontrolkę TreeView dla danych z analizy tekstur."""
        try:
            bc = c4d.BaseContainer()
            for flag_name, flag_value in UIConstants.TREEVIEW_FLAGS.items():
                bc.SetBool(flag_value, True)

            treeview = self.dialog.AddCustomGui(
                UIConstants.TEXTURE_LIST_VIEW,
                c4d.CUSTOMGUI_TREEVIEW,
                "",
                c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT,
                minw=300,
                minh=120,
                customdata=bc,
            )

            if treeview is None:
                return None

            # Konfiguracja kolumn do wyświetlania danych z wyniki_tekstur*.json
            layout = c4d.BaseContainer()
            layout.SetLong(UIConstants.ID_SELECTION, c4d.LV_CHECKBOX)
            layout.SetLong(UIConstants.ID_TEXTURE_NAME, c4d.LV_TREE)
            layout.SetLong(UIConstants.ID_SZEROKOSC, c4d.LV_USER)
            layout.SetLong(UIConstants.ID_WYSOKOSC, c4d.LV_USER)
            layout.SetLong(UIConstants.ID_GLEBIA_BITOWA, c4d.LV_USER)
            layout.SetLong(UIConstants.ID_PROFIL_KOLORU, c4d.LV_USER)
            layout.SetLong(UIConstants.ID_ROZMIAR_MB, c4d.LV_USER)
            layout.SetLong(UIConstants.ID_KANAL_ALPHA, c4d.LV_USER)
            layout.SetLong(UIConstants.ID_FLAGA, c4d.LV_USER)
            layout.SetLong(UIConstants.ID_DATA_UTWORZENIA, c4d.LV_USER)
            layout.SetLong(UIConstants.ID_DATA_MODYFIKACJI, c4d.LV_USER)
            layout.SetLong(UIConstants.ID_HASH, c4d.LV_USER)
            layout.SetLong(UIConstants.ID_FULL_PATH, c4d.LV_USER)

            # Ustawienie szerokości kolumn
            layout.SetLong(
                UIConstants.ID_SELECTION + 1000, UIConstants.COLUMN_SELECTION_WIDTH
            )
            layout.SetLong(
                UIConstants.ID_TEXTURE_NAME + 1000,
                UIConstants.COLUMN_TEXTURE_NAME_WIDTH,
            )
            layout.SetLong(
                UIConstants.ID_SZEROKOSC + 1000, UIConstants.COLUMN_WIDTH_WIDTH
            )
            layout.SetLong(
                UIConstants.ID_WYSOKOSC + 1000, UIConstants.COLUMN_HEIGHT_WIDTH
            )
            layout.SetLong(
                UIConstants.ID_GLEBIA_BITOWA + 1000, UIConstants.COLUMN_BIT_DEPTH_WIDTH
            )
            layout.SetLong(
                UIConstants.ID_PROFIL_KOLORU + 1000,
                UIConstants.COLUMN_COLOR_PROFILE_WIDTH,
            )
            layout.SetLong(
                UIConstants.ID_ROZMIAR_MB + 1000, UIConstants.COLUMN_SIZE_MB_WIDTH
            )
            layout.SetLong(
                UIConstants.ID_KANAL_ALPHA + 1000,
                UIConstants.COLUMN_ALPHA_CHANNEL_WIDTH,
            )
            layout.SetLong(UIConstants.ID_FLAGA + 1000, UIConstants.COLUMN_FLAG_WIDTH)
            layout.SetLong(
                UIConstants.ID_DATA_UTWORZENIA + 1000,
                UIConstants.COLUMN_CREATION_DATE_WIDTH,
            )
            layout.SetLong(
                UIConstants.ID_DATA_MODYFIKACJI + 1000,
                UIConstants.COLUMN_MODIFICATION_DATE_WIDTH,
            )
            layout.SetLong(UIConstants.ID_HASH + 1000, UIConstants.COLUMN_HASH_WIDTH)
            layout.SetLong(
                UIConstants.ID_FULL_PATH + 1000, UIConstants.COLUMN_FULL_PATH_WIDTH
            )

            # Liczba kolumn
            total_columns = 13

            treeview.SetLayout(total_columns, layout)

            # Ustawienie nagłówków kolumn
            treeview.SetHeaderText(UIConstants.ID_SELECTION, "Wybierz")
            treeview.SetHeaderText(UIConstants.ID_TEXTURE_NAME, "Nazwa")
            treeview.SetHeaderText(UIConstants.ID_SZEROKOSC, "Szerokość")
            treeview.SetHeaderText(UIConstants.ID_WYSOKOSC, "Wysokość")
            treeview.SetHeaderText(UIConstants.ID_GLEBIA_BITOWA, "Głębia bitowa")
            treeview.SetHeaderText(UIConstants.ID_PROFIL_KOLORU, "Profil koloru")
            treeview.SetHeaderText(UIConstants.ID_ROZMIAR_MB, "Rozmiar [MB]")
            treeview.SetHeaderText(UIConstants.ID_KANAL_ALPHA, "Kanał Alpha")
            treeview.SetHeaderText(UIConstants.ID_FLAGA, "Flaga")
            treeview.SetHeaderText(UIConstants.ID_DATA_UTWORZENIA, "Data utworzenia")
            treeview.SetHeaderText(UIConstants.ID_DATA_MODYFIKACJI, "Data modyfikacji")
            treeview.SetHeaderText(UIConstants.ID_HASH, "Hash SHA-256")
            treeview.SetHeaderText(UIConstants.ID_FULL_PATH, "Pełna ścieżka")

            return treeview
        except Exception as e:
            logger.error(f"Błąd podczas tworzenia TreeView: {str(e)}")
            return None


class ButtonRowBuilder:
    """Buduje rząd przycisków."""

    def __init__(self, dialog):
        self.dialog = dialog

    def build(self, group_id, buttons: List[Tuple[int, str]]):
        """Tworzy rząd przycisków w grupie."""
        try:
            if not self.dialog.GroupBegin(
                group_id,
                c4d.BFH_CENTER,
                rows=1,
                cols=len(buttons),
            ):
                return False

            self.dialog.GroupBorderSpace(4, 4, 4, 4)
            self.dialog.GroupSpace(4, 0)

            for button_id, button_name in buttons:
                self.dialog.AddButton(button_id, c4d.BFH_SCALEFIT, name=button_name)
                # Przyciski domyślnie nieaktywne
                self.dialog.Enable(button_id, False)
                self.dialog.GroupSpace(4, 0)

            self.dialog.GroupEnd()
            return True
        except Exception as e:
            logger.error(f"Błąd podczas tworzenia rzędu przycisków: {str(e)}")
            return False
