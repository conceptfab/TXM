import os
from typing import Any, Dict, List, Optional

import c4d

from core import files_worker
from core.constants import UIConstants
from core.logger import Logger
from core.models import TextureManager
from core.utils import format_file_size, get_global_status, set_global_status

# Stała identyfikująca kolejkę wiadomości
PLUGIN_ID_MESSAGE_QUEUE = 1000

logger = Logger()


class TextureController:
    """Kontroler zarządzający logiką przetwarzania tekstur."""

    def __init__(self, texture_manager, dialog):
        """Inicjalizacja kontrolera tekstur."""
        logger.debug("Inicjalizacja TextureController")
        self.texture_manager = texture_manager
        self.dialog = dialog
        logger.debug(
            "TextureController zainicjalizowany z menedżerem tekstur i dialogiem"
        )

    def setup_initial_button_state(self, status: str) -> bool:
        """Ustawia początkowy stan przycisków."""
        try:
            logger.debug("Konfiguracja początkowego stanu przycisków")
            # Wszystkie przyciski domyślnie nieaktywne
            self.dialog.Enable(UIConstants.BTN_BROWSE, False)
            self.dialog.Enable(UIConstants.BTN_PROCESS_SELECTED, False)
            self.dialog.Enable(
                UIConstants.PROGRESS_BTN, False
            )  # Upewniamy się, że przycisk postępu jest wyłączony
            self.set_action_buttons_state(False)

            # Używamy przekazanego statusu
            if status == "Znaleziono folder tekstur":
                self.dialog.Enable(UIConstants.BTN_BROWSE, True)
                logger.debug("Aktywowano przycisk Load Textures")
                logger.debug("Sprawdzanie statusu przed aktywacją przycisku")
                logger.debug(f"Status: {status}")

            logger.debug("Przyciski zostały ustawione w stan początkowy")
            return True
        except Exception as e:
            logger.error(
                f"Błąd podczas ustawiania początkowego stanu przycisków: {str(e)}"
            )
            return False

    def update_ui_state(self) -> bool:
        """Aktualizuje stan przycisków w oparciu o bieżący stan aplikacji."""
        try:
            has_textures = self.texture_manager.get_texture_count() > 0
            has_selected = self.texture_manager.count_selected() > 0

            logger.debug(
                f"Stan aplikacji: tekstury={has_textures}, zaznaczone={has_selected}"
            )

            self.dialog.Enable(UIConstants.BTN_PROCESS_SELECTED, has_textures)
            self.dialog.Enable(UIConstants.BTN_IMPORT, True)  # Import zawsze dostępny
            self.dialog.Enable(UIConstants.BTN_EXPORT, has_selected)
            self.dialog.Enable(UIConstants.BTN_REFRESH, has_textures)
            self.dialog.Enable(UIConstants.BTN_CLEAR, has_textures)
            self.dialog.Enable(UIConstants.PROGRESS_BTN, has_selected)

            # Dodajemy dodatkowe logowanie
            logger.debug(f"Przycisk postępu aktywny: {has_selected}")

            logger.debug("Stan przycisków został zaktualizowany")
            return True
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji stanu UI: {str(e)}")
            return False

    def toggle_selection(self) -> bool:
        """Przełącza zaznaczenie wszystkich tekstur."""
        try:
            logger.debug("Przełączanie stanu zaznaczenia wszystkich tekstur")
            if self.texture_manager.are_all_selected():
                logger.debug("Odznaczanie wszystkich tekstur")
                self.texture_manager.deselect_all()
            else:
                logger.debug("Zaznaczanie wszystkich tekstur")
                self.texture_manager.select_all()

            self.handle_state_change("selection_changed")
            logger.debug("Zakończono przełączanie zaznaczenia")
            return True
        except Exception as e:
            logger.error(f"Błąd podczas przełączania zaznaczenia: {str(e)}")
            return False

    def clear_textures(self) -> bool:
        """Czyści listę tekstur."""
        try:
            logger.debug("Czyszczenie listy tekstur")
            self.texture_manager.clear()
            self.handle_state_change("textures_cleared")
            logger.debug("Lista tekstur została wyczyszczona")
            return True
        except Exception as e:
            logger.error(f"Błąd podczas czyszczenia tekstur: {str(e)}")
            return False

    def load_textures_from_directory(self, directory: str = None) -> bool:
        """Ładuje tekstury z wybranego katalogu i wykonuje analizę."""
        try:
            # Jeśli nie podano katalogu, użyj folderu tekstur aktywnego dokumentu C4D
            if not directory:
                doc_path, tex_path = files_worker.get_project_texture_path()
                if not tex_path:
                    logger.warning(
                        "Brak aktywnego dokumentu C4D lub brak folderu tekstur"
                    )
                    self.dialog.SetString(
                        UIConstants.STATUS_TOTAL_SIZE,
                        "Status: Brak aktywnego dokumentu C4D lub folderu tekstur",
                    )
                    return False
                directory = tex_path

            logger.debug(f"Rozpoczęcie analizy tekstur z katalogu: {directory}")
            self.dialog.SetString(
                UIConstants.STATUS_TOTAL_SIZE, "Status: Analizowanie tekstur..."
            )

            # Inicjalizacja kontrolera postępu
            progress_controller = ProgressController()

            # Tworzenie dialogu postępu w trybie ASYNC
            logger.debug("Otwieranie okna dialogu postępu...")
            progress_dialog = progress_controller.show_progress_dialog(
                title="Analiza tekstur",
                message=f"Rozpoczynam analizę tekstur z folderu: {os.path.basename(directory)}",
                action_button_text="Zatrzymaj",
                is_action_enabled=False,  # Przycisk akcji początkowo nieaktywny
                async_mode=True,  # Używamy trybu asynchronicznego
            )

            # Funkcja callback dla aktualizacji postępu
            def status_callback(etap, postęp, wiadomość):
                if progress_controller.is_canceled(progress_dialog):
                    return False
                progress_controller.update_progress(
                    progress_dialog, postęp, f"{etap}: {wiadomość}"
                )
                return True

            # Użyj funkcji analizy tekstur
            import core.texture_runner

            wyniki = core.texture_runner.analizuj_folder_tekstur(
                directory, False, status_callback
            )

            if not wyniki.get("sukces", False):
                logger.error(
                    f"Błąd analizy: {wyniki.get('komunikat', 'Nieznany błąd')}"
                )
                self.dialog.SetString(
                    UIConstants.STATUS_TOTAL_SIZE,
                    f"Status: Błąd analizy: {wyniki.get('komunikat', 'Nieznany błąd')}",
                )
                progress_controller.close_progress_dialog(progress_dialog)
                return False

            # Załaduj wyniki do menedżera tekstur
            self.texture_manager.load_textures_from_analysis(wyniki)

            # Aktualizuj UI
            self.handle_state_change("textures_loaded")

            # Aktualizuj status
            liczba_tekstur = self.texture_manager.get_texture_count()
            self.dialog.SetString(
                UIConstants.STATUS_TOTAL_SIZE,
                f"Status: Załadowano {liczba_tekstur} tekstur z analizy",
            )

            # Zamknięcie dialogu postępu
            progress_controller.close_progress_dialog(progress_dialog)

            logger.debug("Zakończono analizę i wczytywanie tekstur")
            return True
        except Exception as e:
            logger.error(f"Błąd podczas analizy i wczytywania tekstur: {str(e)}")
            self.dialog.SetString(
                UIConstants.STATUS_TOTAL_SIZE, f"Status: Błąd: {str(e)}"
            )
            return False

    def update_selection_info(self) -> bool:
        """Aktualizuje informacje o zaznaczeniu w interfejsie."""
        try:
            selected = self.texture_manager.count_selected()
            total = self.texture_manager.get_texture_count()
            size_sum = self.texture_manager.calculate_selected_size()

            logger.debug(
                f"Statystyki: zaznaczone={selected}, całkowite={total}, rozmiar={format_file_size(size_sum)}"
            )

            # Aktualizujemy licznik zaznaczonych elementów
            self.dialog.SetString(
                UIConstants.STATUS_SELECTION_COUNT, f"Selected: {selected} / {total}"
            )

            # Aktualizujemy status rozmiar tylko jeśli są zaznaczone elementy
            if selected > 0:
                self.dialog.SetString(
                    UIConstants.STATUS_TOTAL_SIZE,
                    f"Status: Zaznaczono {selected} z {total} - Rozmiar: {format_file_size(size_sum)}",
                )
            else:
                # Jeśli nic nie jest zaznaczone, ale są pliki, informujemy o tym
                if total > 0:
                    self.dialog.SetString(
                        UIConstants.STATUS_TOTAL_SIZE,
                        f"Status: Wczytano {total} plików (brak zaznaczonych)",
                    )
                else:
                    # Jeśli nie ma plików, wyświetlamy gotowość
                    self.dialog.SetString(
                        UIConstants.STATUS_TOTAL_SIZE, "Status: Ready"
                    )

            all_selected = selected == total and total > 0
            self.dialog.SetString(
                UIConstants.BTN_PROCESS_SELECTED,
                "Odznacz wszystkie" if all_selected else "Zaznacz wszystkie",
            )

            # Aktualizujemy stan przycisku postępu
            self.dialog.Enable(UIConstants.PROGRESS_BTN, selected > 0)

            return True
        except Exception as e:
            logger.error(
                f"Błąd podczas aktualizacji informacji o zaznaczeniu: {str(e)}"
            )
            return False

    def set_button_state(self, button_id, enabled) -> bool:
        """Ustawia stan pojedynczego przycisku."""
        try:
            logger.debug(f"Ustawianie stanu przycisku {button_id} na {enabled}")
            self.dialog.Enable(button_id, enabled)
            return True
        except Exception as e:
            logger.error(f"Błąd podczas ustawiania stanu przycisku: {str(e)}")
            return False

    def set_action_buttons_state(self, enabled) -> bool:
        """Ustawia stan wszystkich przycisków akcji."""
        try:
            logger.debug(f"Ustawianie stanu wszystkich przycisków akcji na: {enabled}")
            self.dialog.Enable(UIConstants.BTN_IMPORT, enabled)
            self.dialog.Enable(UIConstants.BTN_EXPORT, enabled)
            self.dialog.Enable(UIConstants.BTN_REFRESH, enabled)
            self.dialog.Enable(UIConstants.BTN_CLEAR, enabled)
            self.dialog.Enable(
                UIConstants.PROGRESS_BTN, enabled
            )  # Dodano przycisk postępu
            logger.debug("Zaktualizowano stan wszystkich przycisków akcji")
            return True
        except Exception as e:
            logger.error(f"Błąd podczas ustawiania stanu przycisków akcji: {str(e)}")
            return False

    def handle_state_change(self, change_type, data=None) -> bool:
        """Obsługuje zmiany stanu aplikacji."""
        try:
            logger.debug(f"Obsługa zmiany stanu aplikacji: {change_type}")

            self.dialog.treeview.Refresh()
            self.update_selection_info()
            self.update_ui_state()

            if change_type == "textures_loaded":
                texture_count = self.texture_manager.get_texture_count()
                selected_count = self.texture_manager.count_selected()
                logger.debug(f"Załadowano {texture_count} tekstur")
                if selected_count > 0:
                    self.dialog.SetString(
                        UIConstants.STATUS_TOTAL_SIZE,
                        f"Status: Zaznaczono {selected_count} z {texture_count} tekstur",
                    )
                else:
                    self.dialog.SetString(
                        UIConstants.STATUS_TOTAL_SIZE,
                        f"Status: Wczytano {texture_count} tekstur (brak zaznaczonych)",
                    )
            elif change_type == "textures_cleared":
                logger.debug("Wyczyszczono wszystkie tekstury")
                self.dialog.SetString(UIConstants.STATUS_TOTAL_SIZE, "Status: Ready")

            logger.debug("Zakończono obsługę zmiany stanu")
            return True
        except Exception as e:
            logger.error(f"Błąd podczas obsługi zmiany stanu: {str(e)}")
            return False

    def process_with_progress(self, action_type="Konwertuj"):
        """
        Przykładowa operacja z dialogiem postępu, działająca asynchronicznie.
        """
        try:
            logger.debug("Rozpoczynam operację z paskiem postępu")
            texture_count = self.texture_manager.count_selected()
            logger.debug(f"Liczba zaznaczonych tekstur: {texture_count}")

            if texture_count == 0:
                c4d.gui.MessageDialog("Nie wybrano żadnych tekstur do przetworzenia.")
                return False

            # Inicjalizacja kontrolera postępu
            progress_controller = ProgressController()

            # Tworzenie dialogu postępu w trybie ASYNC
            progress_dialog = progress_controller.show_progress_dialog(
                title=f"{action_type} tekstury",
                message=f"Przygotowanie do przetwarzania {texture_count} tekstur...",
                action_button_text=action_type,
                is_action_enabled=False,  # Przycisk akcji początkowo nieaktywny
                async_mode=True,  # Używamy trybu asynchronicznego
            )

            if progress_dialog is None:
                logger.error("Nie udało się utworzyć dialogu postępu")
                return False

            # Dodajemy flagę anulowania operacji
            processing_cancelled = [False]

            # Użycie c4d.threading zamiast standardowego threading
            # Uruchom przetwarzanie w osobnym wątku
            def processing_thread():
                try:
                    for i in range(texture_count):
                        # Sprawdź, czy operacja została anulowana
                        if (
                            progress_controller.is_canceled(progress_dialog)
                            or processing_cancelled[0]
                        ):
                            logger.debug("Operacja anulowana przez użytkownika")
                            return

                        # Bezpieczna aktualizacja dialogu poprzez wywołanie asynchroniczne
                        progress = (i + 1) / texture_count
                        message = f"Przetwarzanie tekstury {i + 1} z {texture_count}..."

                        # Użycie c4d.utils.ExecuteOnMainThread zamiast CallAsyncFunction
                        def update_ui():
                            if not processing_cancelled[0]:
                                if not progress_controller.update_progress(
                                    progress_dialog, progress, message
                                ):
                                    processing_cancelled[0] = True

                        c4d.utils.ExecuteOnMainThread(update_ui)

                        # Symulacja operacji
                        c4d.threading.GeThreadLock()
                        time.sleep(0.2)
                        c4d.threading.GeThreadUnlock()

                    # Operacja zakończona - bezpieczna aktualizacja UI
                    def complete_operation():
                        if not processing_cancelled[0]:
                            progress_controller.update_progress(
                                progress_dialog,
                                1.0,
                                f"Zakończono przetwarzanie {texture_count} tekstur.",
                            )

                            # Opóźnione zamknięcie dialogu
                            def close_dialog():
                                progress_controller.close_progress_dialog(
                                    progress_dialog
                                )

                            c4d.utils.ExecuteOnMainThread(close_dialog)

                    c4d.utils.ExecuteOnMainThread(complete_operation)
                except Exception as e:
                    logger.error(f"Błąd w wątku przetwarzania: {str(e)}")
                    processing_cancelled[0] = True

            # Użycie c4d.threading.C4DThread zamiast standardowego wątku
            thread = c4d.threading.C4DThread(processing_thread)
            thread.Start()

            return True
        except Exception as e:
            logger.error(f"Błąd podczas operacji z paskiem postępu: {str(e)}")
            return False


class StatusManager:
    """Klasa zarządzająca statusem aplikacji."""

    def __init__(self, dialog, initial_status):
        """Inicjalizacja managera statusu."""
        logger.debug("Inicjalizacja StatusManager")
        self.dialog = dialog
        self._selection_count = 0
        self._total_count = 0
        self._total_size = 0
        self._current_status = initial_status
        self._update_status_display(initial_status)
        logger.debug("StatusManager zainicjalizowany")

    def _update_status_display(self, status):
        """Aktualizuje wyświetlany status w interfejsie."""
        self.dialog.SetString(UIConstants.STATUS_TOTAL_SIZE, f"Status: {status}")

    def set_status(self, status):
        """Ustawia nowy status i aktualizuje interfejs."""
        logger.debug(f"Status: {status}")
        set_global_status(status)
        self._update_status_display(status)

        # Aktywuj przycisk Load Textures jeśli status to "Znaleziono folder tekstur"
        logger.debug("Sprawdzanie warunku aktywacji przycisku Load Textures")
        logger.debug(f"Status: {status}")
        if status == "Znaleziono folder tekstur":
            logger.debug("Aktywacja przycisku Load Textures - warunek spełniony")
            self.dialog.Enable(UIConstants.BTN_BROWSE, True)
        else:
            logger.warning(
                f"Aktywacja przycisku Load Textures - warunek nie spełniony. Status: {status}"
            )

    def update_selection_info(self, selected, total, size_sum):
        """Aktualizuje informacje o zaznaczeniu."""
        logger.debug(
            f"Aktualizacja informacji o zaznaczeniu: {selected}/{total} ({format_file_size(size_sum)})"
        )
        self._selection_count = selected
        self._total_count = total
        self._total_size = size_sum

        # Aktualizujemy licznik zaznaczonych elementów
        self.dialog.SetString(
            UIConstants.STATUS_SELECTION_COUNT, f"Selected: {selected} / {total}"
        )

        # Aktualizujemy status rozmiar tylko jeśli są zaznaczone elementy
        if selected > 0:
            self.dialog.SetString(
                UIConstants.STATUS_TOTAL_SIZE,
                f"Status: Zaznaczono {selected} z {total} - Rozmiar: {format_file_size(size_sum)}",
            )
        else:
            # Jeśli nic nie jest zaznaczone, ale są pliki, informujemy o tym
            if total > 0:
                self.dialog.SetString(
                    UIConstants.STATUS_TOTAL_SIZE,
                    f"Status: Wczytano {total} plików (brak zaznaczonych)",
                )
            else:
                # Jeśli nie ma plików, wyświetlamy gotowość
                self.dialog.SetString(UIConstants.STATUS_TOTAL_SIZE, "Status: Ready")

        # Aktualizacja stanu przycisku postępu
        self.dialog.Enable(UIConstants.PROGRESS_BTN, selected > 0)

    def set_loading(self):
        """Ustawia status na 'Loading'."""
        self.set_status(UIConstants.STATUS_LOADING)

    def set_ready(self):
        """Ustawia status na 'Ready'."""
        self.set_status(UIConstants.STATUS_READY)

    def set_error(self, error_msg=""):
        """Ustawia status błędu z opcjonalnym komunikatem."""
        error_status = (
            f"{UIConstants.STATUS_ERROR}: {error_msg}"
            if error_msg
            else UIConstants.STATUS_ERROR
        )
        logger.error(f"Błąd: {error_msg}" if error_msg else UIConstants.STATUS_ERROR)
        self.set_status(error_status)

    def set_processing(self):
        """Ustawia status na 'Processing'."""
        self.set_status(UIConstants.STATUS_PROCESSING)

    def refresh_status(self):
        """Odświeża status pobierając aktualną wartość z kontrolera."""
        self._update_status_display(get_global_status())


class ProgressController:
    """Kontroler zarządzający dialogiem postępu."""

    def __init__(self, dialog=None):
        """Inicjalizacja kontrolera dialogu postępu."""
        self.dialog = dialog
        logger.debug("Zainicjalizowano ProgressController")

    def show_progress_dialog(
        self,
        title="Postęp operacji",
        message="Trwa przetwarzanie...",
        action_button_text="Kontynuuj",
        is_action_enabled=True,
        async_mode=False,
    ):
        """
        Pokazuje dialog postępu.

        Args:
            title (str): Tytuł okna dialogu
            message (str): Początkowy komunikat
            action_button_text (str): Tekst na przycisku akcji
            is_action_enabled (bool): Czy przycisk akcji jest aktywny
            async_mode (bool): Czy otworzyć dialog w trybie asynchronicznym

        Returns:
            ProgressDialog: Instancja dialogu postępu lub None w przypadku błędu
        """
        try:
            from views.progress_dialog import ProgressDialog

            progress_dialog = ProgressDialog(
                title=title,
                message=message,
                action_button_text=action_button_text,
                is_action_enabled=is_action_enabled,
            )

            # Wybierz odpowiedni tryb dialogu
            dialog_type = c4d.DLG_TYPE_ASYNC if async_mode else c4d.DLG_TYPE_MODAL

            # Usunięto flagę BFV_FLOATING_DIALOG, która nie istnieje
            result = progress_dialog.Open(
                dialog_type,  # Dialog asynchroniczny lub modalny
                defaultw=400,  # Stała szerokość
                defaulth=150,  # Stała wysokość
                flags=c4d.BFH_CENTER,  # Tylko flaga centrowania
            )

            if result:
                logger.debug(f"Otwarto dialog postępu: {title}")
                progress_dialog.IsOpened = True  # Dodajemy atrybut IsOpened
                c4d.EventAdd()  # Upewniamy się, że C4D przetworzy zdarzenia
                return progress_dialog
            else:
                logger.error("Nie udało się otworzyć dialogu postępu")
                return None

        except Exception as e:
            logger.error(f"Błąd podczas tworzenia dialogu postępu: {str(e)}")
            return None

    def update_progress(self, dialog, progress, message=None):
        """
        Aktualizuje postęp i opcjonalnie komunikat w dialogu.

        Args:
            dialog (ProgressDialog): Dialog do zaktualizowania
            progress (float): Wartość postępu (0.0-1.0)
            message (str, optional): Nowy komunikat

        Returns:
            bool: True w przypadku powodzenia, False w przypadku błędu
        """
        try:
            if dialog is None:
                logger.warning("Próba aktualizacji nieistniejącego dialogu postępu")
                return False

            # Sprawdź czy dialog jeszcze istnieje i czy może być zaktualizowany
            if not hasattr(dialog, "IsOpened") or not dialog.IsOpened:
                logger.warning(
                    "Dialog postępu został już zamknięty i nie może być zaktualizowany"
                )
                return False

            # Aktualizacja wartości postępu
            dialog.SetProgress(progress)

            # Aktualizacja komunikatu, jeśli podano
            if message is not None:
                dialog.SetMessage(message)

            # Aktualizacja interfejsu - uproszczona wersja bez GetInputState
            c4d.DrawViews(c4d.DRAWFLAGS_FORCEFULLREDRAW)
            c4d.EventAdd()

            return True
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji dialogu postępu: {str(e)}")
            return False

    def close_progress_dialog(self, dialog):
        """
        Zamyka dialog postępu.

        Args:
            dialog (ProgressDialog): Dialog do zamknięcia

        Returns:
            bool: True w przypadku powodzenia, False w przypadku błędu
        """
        try:
            if dialog is None:
                return False

            # Sprawdzenie, czy dialog jest nadal otwarty
            if hasattr(dialog, "IsOpened") and dialog.IsOpened:
                dialog.Close()
                dialog.IsOpened = False  # Oznaczamy jako zamknięty
                logger.debug("Zamknięto dialog postępu")
                return True
            else:
                logger.warning("Próba zamknięcia dialogu, który nie jest już otwarty")
                return False
        except Exception as e:
            logger.error(f"Błąd podczas zamykania dialogu postępu: {str(e)}")
            return False

    def is_canceled(self, dialog):
        """
        Sprawdza, czy operacja została anulowana.

        Args:
            dialog (ProgressDialog): Dialog do sprawdzenia

        Returns:
            bool: True jeśli operacja została anulowana, False w przeciwnym razie
        """
        try:
            if dialog is None:
                return False

            return dialog.IsCanceled()
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania statusu anulowania: {str(e)}")
            return False

    def complete_progress(self, dialog, completion_message):
        """
        Aktualizuje komunikat po zakończeniu operacji.

        Args:
            dialog (ProgressDialog): Dialog do zaktualizowania
            completion_message (str): Komunikat po zakończeniu operacji

        Returns:
            bool: True w przypadku powodzenia, False w przypadku błędu
        """
        try:
            if dialog is None:
                return False

            dialog.SetMessage(completion_message)
            return True
        except Exception as e:
            logger.error(
                f"Błąd podczas aktualizacji komunikatu po zakończeniu operacji: {str(e)}"
            )
            return False
