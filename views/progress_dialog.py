import c4d

from core.constants import UIConstants
from core.logger import Logger

logger = Logger()


class ProgressDialog(c4d.gui.GeDialog):
    """Dialog postępu operacji z paskiem postępu i przyciskami akcji."""

    # Stałe ID dla kontrolek
    ID_TEXT_MESSAGE = 1000
    ID_PROGRESSBAR_GROUP = 1001
    ID_PROGRESSBAR = 1002
    ID_PROGRESS_TEXT = 1003
    ID_BTN_ACTION = 1004
    ID_BTN_CANCEL = 1005

    def __init__(
        self,
        title="Postęp operacji",
        message="Trwa przetwarzanie...",
        action_button_text="Kontynuuj",
        is_action_enabled=True,
    ):
        """
        Inicjalizuje dialog postępu.

        Args:
            title (str): Tytuł okna dialogu
            message (str): Początkowy komunikat
            action_button_text (str): Tekst na przycisku akcji
            is_action_enabled (bool): Czy przycisk akcji jest aktywny
        """
        super(ProgressDialog, self).__init__()
        self.title = title
        self.message = message
        self.action_button_text = action_button_text
        self.is_action_enabled = is_action_enabled
        self.progress = 0.0  # Wartość postępu 0.0-1.0
        self.canceled = False
        logger.debug(f"Inicjalizuję dialog postępu: {title}")

    def CreateLayout(self):
        """Tworzy układ dialogu postępu."""
        try:
            self.SetTitle(self.title)

            # Główny layout z wycentrowaniem
            if not self.GroupBegin(
                0,
                c4d.BFH_SCALEFIT | c4d.BFH_CENTER | c4d.BFV_CENTER,
                cols=1,
                rows=3,
                title="",
            ):
                return False

            # Ustawienie marginesów
            self.GroupBorderSpace(10, 10, 10, 10)

            # Komunikat
            self.AddStaticText(
                self.ID_TEXT_MESSAGE,
                c4d.BFH_SCALEFIT,
                initw=400,
                inith=40,
                name=self.message,
            )

            # Grupa paska postępu
            if self.GroupBegin(
                id=self.ID_PROGRESSBAR_GROUP, flags=c4d.BFH_SCALEFIT, cols=1, rows=2
            ):
                # Pasek postępu
                self.GroupBegin(id=0, flags=c4d.BFH_SCALEFIT, cols=1, rows=0)
                self.GroupBorderNoTitle(c4d.BORDER_THIN_IN)
                self.AddCustomGui(
                    self.ID_PROGRESSBAR,
                    c4d.CUSTOMGUI_PROGRESSBAR,
                    "",
                    c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT,
                    UIConstants.PROGRESS_BAR_WIDTH,  # szerokość z stałej
                    UIConstants.PROGRESS_BAR_HEIGHT,  # wysokość z stałej
                )
                self.GroupEnd()

                # Tekst postępu
                self.AddStaticText(
                    self.ID_PROGRESS_TEXT,
                    flags=c4d.BFH_CENTER,
                    initw=50,
                    inith=16,
                    name="0%",
                    borderstyle=0,
                )

                self.GroupEnd()  # Koniec grupy paska postępu

            # Grupa przycisków
            if not self.GroupBegin(0, c4d.BFH_RIGHT, cols=2, rows=1):
                return False

            # Przycisk akcji (np. Konwertuj, Usuń)
            self.AddButton(
                self.ID_BTN_ACTION, c4d.BFH_SCALE, name=self.action_button_text
            )
            self.Enable(self.ID_BTN_ACTION, self.is_action_enabled)

            # Przycisk Anuluj
            self.AddButton(self.ID_BTN_CANCEL, c4d.BFH_SCALE, name="Anuluj")

            # Zamykamy grupę przycisków
            self.GroupEnd()

            # Zamykamy główny layout
            self.GroupEnd()

            return True
        except Exception as e:
            logger.error(f"Błąd podczas tworzenia layoutu dialogu postępu: {str(e)}")
            return False

    def Command(self, id, msg):
        """Obsługuje zdarzenia w dialogu."""
        try:
            if id == self.ID_BTN_CANCEL:
                logger.debug(f"Kliknięto przycisk Anuluj w dialogu '{self.title}'")
                self.canceled = True
                self.Close()
                return True

            elif id == self.ID_BTN_ACTION:
                logger.debug(
                    f"Kliknięto przycisk akcji '{self.action_button_text}' w dialogu '{self.title}'"
                )
                self.Close()
                return True

            return super(ProgressDialog, self).Command(id, msg)
        except Exception as e:
            logger.error(f"Błąd podczas obsługi zdarzenia w dialogu postępu: {str(e)}")
            return False

    def ProcessEvents(self):
        """
        Przetwarza zdarzenia w kolejce C4D, aby odświeżyć interfejs.
        """
        try:
            # Odświeżenie interfejsu i przetworzenie zdarzeń
            c4d.DrawViews(c4d.DRAWFLAGS_FORCEFULLREDRAW)
            c4d.EventAdd()
            return True
        except Exception as e:
            logger.error(f"Błąd podczas przetwarzania zdarzeń: {str(e)}")
            return False

    def SetProgress(self, progress):
        """
        Ustawia wartość paska postępu.

        Args:
            progress (float): Wartość od 0.0 do 1.0 (0-100%)
        """
        try:
            self.progress = min(max(progress, 0.0), 1.0)  # Ograniczenie do 0.0-1.0

            # Aktualizacja paska postępu
            progressMsg = c4d.BaseContainer(c4d.BFM_SETSTATUSBAR)
            progressMsg[c4d.BFM_STATUSBAR_PROGRESSON] = True
            progressMsg[c4d.BFM_STATUSBAR_PROGRESS] = self.progress
            self.SendMessage(self.ID_PROGRESSBAR, progressMsg)

            # Aktualizacja tekstu postępu
            percent = int(self.progress * 100)
            self.SetString(self.ID_PROGRESS_TEXT, f"{percent}%")

            # Przetwarzanie zdarzeń
            self.ProcessEvents()

            return True
        except Exception as e:
            logger.error(f"Błąd podczas ustawiania postępu: {str(e)}")
            return False

    def SetMessage(self, message):
        """
        Aktualizuje wyświetlany komunikat.

        Args:
            message (str): Nowy komunikat
        """
        try:
            self.message = message
            self.SetString(self.ID_TEXT_MESSAGE, message)

            # Przetwarzanie zdarzeń
            self.ProcessEvents()

            return True
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji komunikatu: {str(e)}")
            return False

    def IsCanceled(self):
        """
        Sprawdza, czy operacja została anulowana.

        Returns:
            bool: True jeśli operacja została anulowana, False w przeciwnym razie
        """
        return self.canceled

    def StopProgress(self):
        """Zatrzymuje animację paska postępu."""
        try:
            progressMsg = c4d.BaseContainer(c4d.BFM_SETSTATUSBAR)
            progressMsg.SetBool(c4d.BFM_STATUSBAR_PROGRESSON, False)
            self.SendMessage(self.ID_PROGRESSBAR, progressMsg)
        except Exception as e:
            logger.error(f"Błąd podczas zatrzymywania paska postępu: {str(e)}")

    def IsOpen(self):
        """
        Sprawdza, czy dialog jest nadal otwarty.

        Returns:
            bool: True jeśli dialog jest otwarty, False w przeciwnym razie
        """
        try:
            # W Cinema 4D dialog jest otwarty, jeśli jego współrzędne są różne od (0,0)
            # lub jeśli ma aktywny wskaźnik okna
            if hasattr(self, "IsOpened") and self.IsOpened:
                return True
            return False
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania, czy dialog jest otwarty: {str(e)}")
            return False
