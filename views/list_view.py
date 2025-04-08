import datetime  # Import przeniesiony na początek pliku
from typing import Any, Dict, Optional

import c4d

from core.constants import UIConstants
from core.logger import Logger
from core.models import TextureObject
from core.utils import format_file_size

logger = Logger()


class ListView(c4d.gui.TreeViewFunctions):
    """Implementacja widoku listy tekstur."""

    def __init__(self, host: c4d.gui.GeDialog, texture_manager):
        """Inicjalizacja widoku listy."""
        try:
            logger.debug("Inicjalizacja ListView")
            if not isinstance(host, c4d.gui.GeDialog):
                raise TypeError(
                    f"Oczekiwano {c4d.gui.GeDialog} dla argumentu 'host'. "
                    f"Otrzymano: {type(host)}"
                )
            self._host = host
            self._texture_manager = texture_manager
            self._text_width_cache = {}

            # Dodanie nowych pól do obsługi sortowania
            self._sort_column = (
                UIConstants.ID_TEXTURE_NAME
            )  # Domyślna kolumna sortowania
            self._sort_direction = True  # True = rosnąco, False = malejąco

            logger.debug("ListView zainicjalizowany pomyślnie")
        except Exception as e:
            logger.error(f"Błąd w inicjalizacji ListView: {str(e)}")
            raise

    def _update_dialog(self) -> None:
        """Aktualizuje dialog po zmianie stanu."""
        try:
            self._host.calc_selected()
            # Dodatkowo aktualizujemy stan przycisków
            if hasattr(self._host, "texture_controller"):
                self._host.texture_controller.update_ui_state()
        except Exception as e:
            logger.error(f"Błąd w _update_dialog: {str(e)}")

    def _get_cached_text_width(self, canvas, text: str) -> int:
        """Zwraca szerokość tekstu z cachowaniem wyników."""
        if text not in self._text_width_cache:
            self._text_width_cache[text] = canvas.DrawGetTextWidth(text)
        return self._text_width_cache[text]

    def GetColumnWidth(self, root, userdata, obj, col, area) -> int:
        """Zwraca szerokość kolumny."""
        # Domyślne szerokości dla kolumn z wyników analizy tekstur
        default_widths = {
            UIConstants.ID_SELECTION: 50,
            UIConstants.ID_TEXTURE_NAME: 180,
            UIConstants.ID_SZEROKOSC: 80,
            UIConstants.ID_WYSOKOSC: 80,
            UIConstants.ID_GLEBIA_BITOWA: 100,
            UIConstants.ID_PROFIL_KOLORU: 120,
            UIConstants.ID_ROZMIAR_MB: 100,
            UIConstants.ID_KANAL_ALPHA: 90,
            UIConstants.ID_FLAGA: 120,
            UIConstants.ID_DATA_UTWORZENIA: 150,
            UIConstants.ID_DATA_MODYFIKACJI: 150,
            UIConstants.ID_HASH: 330,
            UIConstants.ID_FULL_PATH: 250,
        }

        # Jeśli mamy zdefiniowaną domyślną szerokość, używamy jej
        if col in default_widths:
            return default_widths[col]

        # Mapowanie ID kolumn na atrybuty obiektu
        column_attrs = {
            UIConstants.ID_TEXTURE_NAME: "nazwa",
            UIConstants.ID_SZEROKOSC: "szerokosc",
            UIConstants.ID_WYSOKOSC: "wysokosc",
            UIConstants.ID_GLEBIA_BITOWA: "glebia_bitowa",
            UIConstants.ID_PROFIL_KOLORU: "profil_koloru",
            UIConstants.ID_ROZMIAR_MB: "rozmiar_mb",
            UIConstants.ID_KANAL_ALPHA: "kanal_alpha",
            UIConstants.ID_FLAGA: "flaga",
            UIConstants.ID_DATA_UTWORZENIA: "data_utworzenia",
            UIConstants.ID_DATA_MODYFIKACJI: "data_modyfikacji",
            UIConstants.ID_HASH: "hash_sha256",
            UIConstants.ID_FULL_PATH: "ścieżka",
        }

        if col in column_attrs:
            attr = getattr(obj, column_attrs[col], "")
            # Dla wartości logicznych i liczbowych zamieniamy na string
            if isinstance(attr, bool):
                attr = "Tak" if attr else "Nie"
            elif isinstance(attr, (int, float)):
                attr = str(attr)

            # Dodajemy margines do szerokości tekstu (minimum 60 pikseli)
            width = max(60, self._get_cached_text_width(area, str(attr)) + 20)
            return width

        return 80  # Domyślna szerokość

    def GetFirst(self, root, userdata) -> Optional[TextureObject]:
        """Zwraca pierwszy obiekt tekstury."""
        textures = self._texture_manager.get_textures()
        return None if not textures else textures[0]

    def GetNext(self, root, userdata, obj) -> Optional[TextureObject]:
        """Zwraca następny obiekt tekstury."""
        textures = self._texture_manager.get_textures()
        try:
            current_idx = textures.index(obj)
            next_idx = current_idx + 1
            return textures[next_idx] if next_idx < len(textures) else None
        except (ValueError, IndexError):
            return None

    def GetPred(self, root, userdata, obj) -> Optional[TextureObject]:
        """Zwraca poprzedni obiekt tekstury."""
        textures = self._texture_manager.get_textures()
        try:
            current_idx = textures.index(obj)
            pred_idx = current_idx - 1
            return textures[pred_idx] if 0 <= pred_idx < len(textures) else None
        except (ValueError, IndexError):
            return None

    def Select(self, root, userdata, obj, mode) -> None:
        """Obsługuje zaznaczanie obiektów."""
        if mode == c4d.SELECTION_NEW:
            self._texture_manager.deselect_all()
            obj.select()
        elif mode == c4d.SELECTION_ADD:
            obj.select()
        elif mode == c4d.SELECTION_SUB:
            obj.deselect()

        # Aktualizuj dialog po zmianie zaznaczenia
        self._update_dialog()

    def IsSelected(self, root, userdata, obj) -> bool:
        """Sprawdza, czy obiekt jest zaznaczony."""
        return obj.is_selected

    def SetCheck(self, root, userdata, obj, column, checked, msg) -> None:
        """Obsługuje zaznaczanie checkboxów."""
        if checked:
            obj.select()
        else:
            obj.deselect()

        # Aktualizuj dialog po zmianie zaznaczenia
        self._update_dialog()

    def IsChecked(self, root, userdata, obj, column) -> int:
        """Zwraca stan checkboxa."""
        if obj.is_selected:
            return c4d.LV_CHECKBOX_CHECKED | c4d.LV_CHECKBOX_ENABLED
        return c4d.LV_CHECKBOX_ENABLED

    def GetName(self, root, userdata, obj) -> str:
        """Zwraca nazwę obiektu."""
        return obj.nazwa if hasattr(obj, "nazwa") else str(obj)

    def DrawCell(self, root, userdata, obj, col, drawinfo, bgColor) -> None:
        """Rysuje komórkę widoku listy - zoptymalizowana wersja."""
        # Mapowanie ID kolumn na atrybuty obiektu i funkcje formatujące
        column_attrs = {
            UIConstants.ID_TEXTURE_NAME: ("nazwa", lambda x: str(x)),
            UIConstants.ID_SZEROKOSC: (
                "szerokosc",
                lambda x: f"{x:,}".replace(",", " ") if x is not None else "-",
            ),
            UIConstants.ID_WYSOKOSC: (
                "wysokosc",
                lambda x: f"{x:,}".replace(",", " ") if x is not None else "-",
            ),
            UIConstants.ID_GLEBIA_BITOWA: ("glebia_bitowa", lambda x: f"{x} bit"),
            UIConstants.ID_PROFIL_KOLORU: ("profil_koloru", lambda x: str(x)),
            UIConstants.ID_ROZMIAR_MB: ("rozmiar_mb", lambda x: f"{x:.2f} MB"),
            UIConstants.ID_KANAL_ALPHA: (
                "kanal_alpha",
                lambda x: "Tak" if x else "Nie",
            ),
            UIConstants.ID_FLAGA: ("flaga", lambda x: str(x)),
            UIConstants.ID_DATA_UTWORZENIA: ("data_utworzenia", lambda x: str(x)),
            UIConstants.ID_DATA_MODYFIKACJI: ("data_modyfikacji", lambda x: str(x)),
            UIConstants.ID_HASH: ("hash_sha256", lambda x: str(x)),
            UIConstants.ID_FULL_PATH: ("ścieżka", lambda x: str(x)),
        }

        # Dodajemy buforowanie atrybutów dla lepszej wydajności
        if not hasattr(obj, "_attr_cache"):
            obj._attr_cache = {}

        if col in column_attrs:
            attr_name, formatter = column_attrs[col]

            # Użyj buforowanej wartości, jeśli istnieje
            cache_key = f"{col}_{attr_name}"
            if cache_key not in getattr(obj, "_attr_cache", {}):
                value = getattr(obj, attr_name, "")
                formatted_value = formatter(value)
                obj._attr_cache[cache_key] = formatted_value
            else:
                formatted_value = obj._attr_cache[cache_key]

            self._draw_text_cell(drawinfo, formatted_value)
        elif col == UIConstants.ID_FILE_SIZE:
            # Specjalne formatowanie dla rozmiaru pliku
            cache_key = f"{col}_filesize"
            if cache_key not in getattr(obj, "_attr_cache", {}):
                obj._attr_cache[cache_key] = format_file_size(obj.filesize)
            self._draw_text_cell(drawinfo, obj._attr_cache[cache_key])

    def _draw_text_cell(self, drawinfo: Dict[str, Any], text: str) -> None:
        """Rysuje komórkę z tekstem."""
        canvas = drawinfo["frame"]
        text_width = self._get_cached_text_width(canvas, text)
        text_height = canvas.DrawGetFontHeight()
        xpos = drawinfo["xpos"]
        ypos = drawinfo["ypos"] + drawinfo["height"]

        if drawinfo["width"] < text_width:
            text = self._truncate_text(text, drawinfo["width"], canvas)

        canvas.DrawText(text, xpos, ypos - int(text_height * 1.1))

    def _draw_file_size_cell(self, drawinfo: Dict[str, Any], size: int) -> None:
        """Rysuje komórkę z rozmiarem pliku."""
        canvas = drawinfo["frame"]
        formatted_size = format_file_size(size)
        text_width = self._get_cached_text_width(canvas, formatted_size)
        h = canvas.DrawGetFontHeight()
        xpos = drawinfo["xpos"] + drawinfo["width"] - text_width - 5
        ypos = drawinfo["ypos"] + drawinfo["height"]
        canvas.DrawText(formatted_size, xpos, ypos - int(h * 1.1))

    def _truncate_text(self, text: str, max_width: int, canvas) -> str:
        """Skraca tekst, aby zmieścił się w dostępnej szerokości."""
        while max_width < self._get_cached_text_width(canvas, text):
            if len(text) <= 4:
                return "..."
            text = text[:-4] + "..."
        return text

    def SetSortColumn(self, column, reverse=False):
        """
        Ustawia kolumnę i kierunek sortowania.

        Args:
            column: ID kolumny do sortowania
            reverse: Czy sortować w kierunku odwrotnym (malejąco)
        """
        try:
            if column == UIConstants.ID_HASH:
                # Kolumna HASH nie jest sortowalna
                logger.debug("Próba sortowania po kolumnie HASH - zignorowano")
                return

            # Logowanie wartości przed zmianą
            old_column = self._sort_column
            old_direction = self._sort_direction

            self._sort_column = column
            self._sort_direction = not reverse

            logger.debug(
                f"Zmiana sortowania: kolumna {old_column}->{column}, "
                f"kierunek: {'rosnąco' if old_direction else 'malejąco'} -> "
                f"{'rosnąco' if self._sort_direction else 'malejąco'}"
            )

            # Posortowanie tekstur
            self._sort_textures()

            # Odświeżenie widoku
            if hasattr(self._host, "treeview") and self._host.treeview:
                logger.debug("Odświeżanie widoku po sortowaniu")
                self._host.treeview.Refresh()
            else:
                logger.warning("Nie można odświeżyć widoku - brak obiektu treeview")

        except Exception as e:
            logger.error(f"Błąd podczas ustawiania kolumny sortowania: {str(e)}")

    def _sort_textures(self):
        """Sortuje tekstury według aktualnie wybranej kolumny i kierunku."""
        try:
            # Mapowanie ID kolumn na atrybuty obiektu
            column_attrs = {
                UIConstants.ID_TEXTURE_NAME: "nazwa",
                UIConstants.ID_SZEROKOSC: "szerokosc",
                UIConstants.ID_WYSOKOSC: "wysokosc",
                UIConstants.ID_GLEBIA_BITOWA: "glebia_bitowa",
                UIConstants.ID_PROFIL_KOLORU: "profil_koloru",
                UIConstants.ID_ROZMIAR_MB: "rozmiar_mb",
                UIConstants.ID_KANAL_ALPHA: "kanal_alpha",
                UIConstants.ID_FLAGA: "flaga",
                UIConstants.ID_DATA_UTWORZENIA: "data_utworzenia",
                UIConstants.ID_DATA_MODYFIKACJI: "data_modyfikacji",
            }

            # Sprawdzenie czy wybrana kolumna jest obsługiwana
            if self._sort_column not in column_attrs:
                logger.warning(
                    f"Nieobsługiwana kolumna sortowania: {self._sort_column}"
                )
                return

            # Pobranie nazwy atrybutu
            attr_name = column_attrs[self._sort_column]

            # Funkcja sortująca uwzględniająca różne typy danych
            def sort_key(obj):
                value = getattr(obj, attr_name, None)

                # Specjalne przypadki dla różnych typów danych
                if attr_name in ["data_utworzenia", "data_modyfikacji"]:
                    # Dla dat zwracamy obiekt datetime
                    try:
                        return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    except (ValueError, TypeError):
                        return datetime.datetime(1970, 1, 1)
                elif attr_name == "kanal_alpha":
                    # Dla wartości boolean, sortujemy True przed False
                    return 0 if value else 1
                elif attr_name in [
                    "szerokosc",
                    "wysokosc",
                    "glebia_bitowa",
                    "rozmiar_mb",
                ]:
                    # Upewniamy się, że wartości numeryczne są traktowane jako liczby
                    try:
                        return float(value) if isinstance(value, str) else value
                    except (ValueError, TypeError):
                        return 0  # Wartość domyślna dla niepoprawnych liczb

                # Dla pozostałych typów zwracamy wartość bezpośrednio
                return value

            # Użycie metody sort_textures z menedżera tekstur
            success = self._texture_manager.sort_textures(
                sort_key, not self._sort_direction
            )

            if success:
                logger.debug(f"Posortowano tekstury według {attr_name}")
            else:
                logger.error(f"Nie udało się posortować tekstur według {attr_name}")

        except Exception as e:
            logger.error(f"Błąd podczas sortowania tekstur: {str(e)}")

    def HeaderClicked(self, root, userdata, col, flags):
        """
        Obsługuje kliknięcie w nagłówek kolumny.

        Args:
            root: Korzeń drzewa
            userdata: Dane użytkownika
            col: ID kolumny
            flags: Flagi zdarzenia

        Returns:
            True jeśli zdarzenie zostało obsłużone, False w przeciwnym przypadku
        """
        try:
            logger.debug(f"Kliknięto nagłówek kolumny: {col}")

            # Ignorowanie kolumny HASH
            if col == UIConstants.ID_HASH:
                return False

            # Zmiana kierunku sortowania jeśli kliknięto tę samą kolumnę
            if col == self._sort_column:
                logger.debug(f"Zmiana kierunku sortowania dla kolumny {col}")
                self._sort_direction = not self._sort_direction
            else:
                # Nowa kolumna, domyślnie sortowanie rosnąco
                logger.debug(
                    f"Zmiana kolumny sortowania z {self._sort_column} na {col}"
                )
                self._sort_column = col
                self._sort_direction = True

            # Sortowanie tekstur
            self._sort_textures()

            # Odświeżenie widoku
            if hasattr(self._host, "treeview") and self._host.treeview:
                self._host.treeview.Refresh()

            return True
        except Exception as e:
            logger.error(f"Błąd podczas obsługi kliknięcia nagłówka kolumny: {str(e)}")
            return False

    def GetHeaderSortArrow(self, root, userdata, col):
        """
        Określa tryb sortowania dla kolumny.

        Args:
            root: Korzeń drzewa
            userdata: Dane użytkownika
            col: ID kolumny

        Returns:
            Tryb sortowania:
            - 0: Sortowanie rosnące (LV_SORT_ASCENDING)
            - 1: Sortowanie malejące (LV_SORT_DESCENDING)
            - 2: Brak sortowania (LV_SORT_NONE)
        """
        try:
            # Dodajemy logowanie dla diagnostyki
            if col == self._sort_column:
                sort_type = 0 if self._sort_direction else 1
                logger.debug(f"Zwracam strzałkę typu {sort_type} dla kolumny {col}")
                return sort_type
            else:
                return 2  # LV_SORT_NONE
        except Exception as e:
            logger.error(f"Błąd podczas określania trybu sortowania: {str(e)}")
            return 2  # LV_SORT_NONE
