import c4d

from core.constants import UIConstants
from core.logger import Logger
from views.builders import ButtonRowBuilder, TreeViewBuilder
from views.list_view import ListView

logger = Logger()


class TexturesTab:
    """Implementuje zakładkę tekstur."""

    def __init__(self, dialog, texture_manager):
        self.dialog = dialog
        self.texture_manager = texture_manager
        self.tree_builder = TreeViewBuilder(dialog, texture_manager)
        self.button_builder = ButtonRowBuilder(dialog)

    def build(self, tab_id):
        """Buduje interfejs zakładki tekstur."""
        try:
            if not self.dialog.GroupBegin(
                tab_id,
                c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT,
                cols=1,
                rows=2,  # Zmieniono z 3 na 2 po usunięciu przycisku
                title="Textures",
            ):
                return False

            # Grupa dla TreeView
            if self.dialog.GroupBegin(
                1001,
                c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT,
                rows=2,
                cols=3,
                groupflags=c4d.BORDER_OUT,
            ):
                treeview = self.tree_builder.build()
                if treeview:
                    list_view = ListView(self.dialog, self.texture_manager)
                    treeview.SetRoot(None, list_view, None)
                    treeview.Refresh()
                    self.dialog.treeview = treeview
                    self.dialog.list_view = list_view
            self.dialog.GroupEnd()

            # Status bar
            if self.dialog.GroupBegin(
                1002,
                c4d.BFH_SCALEFIT,
                rows=1,
                cols=3,
                groupflags=c4d.BORDER_OUT,
            ):
                self.dialog.AddButton(
                    UIConstants.BTN_PROCESS_SELECTED,
                    c4d.BFH_LEFT,
                    name="Zaznacz wszystkie",
                )
                # Przycisk domyślnie nieaktywny
                self.dialog.Enable(UIConstants.BTN_PROCESS_SELECTED, False)

                self.dialog.AddStaticText(
                    UIConstants.STATUS_SELECTION_COUNT,
                    c4d.BFH_LEFT,
                    initw=200,
                    name="Selected: 0 / 0",
                )
                self.dialog.AddStaticText(
                    UIConstants.STATUS_TOTAL_SIZE,
                    c4d.BFH_LEFT,
                    initw=200,
                    name="Filesize Sum: 0 B",
                )
            self.dialog.GroupEnd()

            # Przyciski akcji w jednym rzędzie
            buttons = [
                (UIConstants.BTN_IMPORT, "Import"),
                (UIConstants.BTN_EXPORT, "Export"),
                (UIConstants.BTN_REFRESH, "Refresh"),
                (UIConstants.BTN_CLEAR, "Clear"),
            ]
            self.button_builder.build(UIConstants.ACTION_BUTTONS_GROUP, buttons)

            # Odstęp 16px
            self.dialog.GroupSpace(16, 0)

            # Przycisk Load Textures na dole
            if self.dialog.GroupBegin(
                UIConstants.TEXTURE_LOAD_GROUP,
                c4d.BFH_SCALEFIT,
                rows=3,
                cols=1,
            ):
                # Pusty rząd na górze
                self.dialog.AddStaticText(0, c4d.BFH_CENTER)

                # Przycisk w środkowym rzędzie
                self.dialog.AddButton(
                    UIConstants.BTN_BROWSE,
                    c4d.BFH_CENTER,
                    initw=120,
                    name="Load Textures",
                )
                # Wyraźnie oznaczamy przycisk jako nieaktywny
                self.dialog.Enable(UIConstants.BTN_BROWSE, False)

                # Status bar w trzecim rzędzie
                if self.dialog.GroupBegin(0, c4d.BFH_SCALEFIT, rows=1, cols=1):
                    self.dialog.AddStaticText(
                        UIConstants.STATUS_BAR_TEXT,
                        c4d.BFH_LEFT,
                        name=f"Status: {self.dialog._current_status}",
                        borderstyle=c4d.BORDER_NONE,
                    )
                self.dialog.GroupEnd()
            self.dialog.GroupEnd()

            # Odstęp 27px od dolnej krawędzi
            self.dialog.GroupSpace(27, 0)

            self.dialog.GroupEnd()
            return True
        except Exception as e:
            logger.error(f"Błąd podczas budowania zakładki tekstur: {str(e)}")
            return False


class SettingsTab:
    """Implementuje zakładkę ustawień."""

    def __init__(self, dialog):
        self.dialog = dialog

    def build(self, tab_id):
        """Buduje interfejs zakładki ustawień."""
        try:
            if self.dialog.GroupBegin(
                tab_id,
                c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT,
                cols=1,
                rows=1,
                title="Settings",
            ):
                # W przyszłości można dodać elementy dla drugiej zakładki
                self.dialog.GroupEnd()
                return True
            return False
        except Exception as e:
            logger.error(f"Błąd podczas budowania zakładki ustawień: {str(e)}")
            return False
