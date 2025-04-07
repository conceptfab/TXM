import datetime
import os
import random
from typing import List, Optional

from core.logger import Logger

logger = Logger()


class TextureObject:
    """Reprezentuje obiekt tekstury z metadanymi."""

    def __init__(self, texture_path="", other_data="", file_size=0, is_selected=False):
        try:
            self.texturePath = texture_path or self._generate_random_string(5, 10)
            self.otherData = other_data or self._generate_random_string(5, 20)
            self.longfilename = "-"
            self._selected = is_selected
            self.filesize = file_size or self._generate_random_number()

            # Ekstrakcja nazwy pliku ze ścieżki
            self.nazwa = os.path.basename(self.texturePath)

            # Właściwości dla procesowania tekstur
            self.szerokosc = random.randint(1000, 8000)
            self.wysokosc = random.randint(500, 4000)
            self.glebia_bitowa = random.choice([8, 16, 24, 32])
            self.profil_koloru = random.choice(
                ["sRGB", "Adobe RGB", "ProPhoto RGB", "lin_srgb", "scene_linear"]
            )
            self.rozmiar_mb = round(random.uniform(1.0, 500.0), 2)
            self.kanal_alpha = random.choice([True, False])
            self.flaga = random.choice(["oryginał", "duplikat", "możliwy duplikat", ""])

            # Daty utworzenia i modyfikacji
            now = datetime.datetime.now()
            self.data_utworzenia = now.strftime("%Y-%m-%d %H:%M:%S")

            # Data modyfikacji (losowo w przeszłości)
            days_ago = random.randint(1, 2000)
            modification_date = now - datetime.timedelta(days=days_ago)
            self.data_modyfikacji = modification_date.strftime("%Y-%m-%d %H:%M:%S")

            # Hash SHA-256
            self.hash_sha256 = "".join(
                random.choice("0123456789abcdef") for _ in range(64)
            )

            # Dodajemy przykładowe dane z zainicjowanego obiektu
            if self.nazwa == "06-09_Sunset_B.hdr":
                self.szerokosc = 15000
                self.wysokosc = 7500
                self.glebia_bitowa = 32
                self.profil_koloru = "lin_srgb"
                self.rozmiar_mb = 312.42
                self.kanal_alpha = False
                self.flaga = "oryginał"
                self.data_utworzenia = "2025-04-06 18:35:44"
                self.data_modyfikacji = "2019-07-14 20:05:10"
                self.hash_sha256 = (
                    "ac10686245b34977ff48850b75b48553efd9d20dad9ed342e713ebeb7f792ebc"
                )

            # Dodajemy nowe właściwości dla kolumn A5-A11
            self.a5 = self._generate_random_string(3, 7)
            self.a6 = self._generate_random_string(3, 7)
            self.a7 = self._generate_random_string(3, 7)
            self.a8 = self._generate_random_string(3, 7)
            self.a9 = self._generate_random_string(3, 7)
            self.a10 = self._generate_random_string(3, 7)
            self.a11 = self._generate_random_string(3, 7)

            if not hasattr(TextureObject, "_count"):
                TextureObject._count = 0
            TextureObject._count += 1
        except Exception as e:
            logger.error(f"Błąd podczas tworzenia TextureObject: {str(e)}")
            raise

    @classmethod
    def log_creation_count(cls):
        """Loguje liczbę utworzonych elementów."""
        if hasattr(cls, "_count") and cls._count > 0:
            logger.debug(f"Utworzono {cls._count} elementów TextureObject")

    @staticmethod
    def _generate_random_string(min_length: int, max_length: int) -> str:
        """Generuje losowy ciąg znaków o określonej długości."""
        CHARACTERS = tuple(chr(n) for n in range(97, 122))
        length = random.randint(min_length, max_length)
        return "".join(random.choice(CHARACTERS) for _ in range(length))

    @staticmethod
    def _generate_random_number() -> int:
        """Generuje losową liczbę dla rozmiaru pliku."""
        return random.randrange(1, 99)

    @property
    def is_selected(self) -> bool:
        """Zwraca informację czy tekstura jest zaznaczona."""
        return self._selected

    def select(self) -> None:
        """Zaznacza teksturę."""
        self._selected = True

    def deselect(self) -> None:
        """Odznacza teksturę."""
        self._selected = False

    def __str__(self) -> str:
        return self.texturePath


class TextureManager:
    """Zarządza kolekcją obiektów tekstur."""

    def __init__(self):
        self._textures: List[TextureObject] = []

    def load_random_textures(self, count: int = 10) -> None:
        """Ładuje określoną liczbę losowych tekstur do testów."""
        if hasattr(TextureObject, "_count"):
            delattr(TextureObject, "_count")
        if hasattr(TextureObject, "_is_first_log"):
            delattr(TextureObject, "_is_first_log")
        self._textures = [TextureObject() for _ in range(count)]
        TextureObject.log_creation_count()

    def load_textures_from_directory(
        self, directory: str, extensions: List[str] = [".jpg", ".png", ".tif", ".tga"]
    ) -> None:
        """Ładuje tekstury z podanego katalogu z określonymi rozszerzeniami."""
        if not os.path.exists(directory) or not os.path.isdir(directory):
            logger.error(f"Katalog nie istnieje: {directory}")
            return

        self._textures = []
        try:
            for filename in os.listdir(directory):
                if os.path.splitext(filename)[1].lower() in extensions:
                    file_path = os.path.join(directory, filename)
                    file_size = os.path.getsize(file_path)
                    texture_obj = TextureObject(
                        texture_path=file_path,  # Używamy pełnej ścieżki
                        other_data=os.path.splitext(filename)[0],
                        file_size=file_size,
                    )
                    texture_obj.nazwa = filename  # Ustawiamy właściwą nazwę pliku
                    self._textures.append(texture_obj)
            logger.debug(
                f"Załadowano {len(self._textures)} tekstur z katalogu {directory}"
            )
        except Exception as e:
            logger.error(f"Błąd podczas ładowania tekstur z katalogu: {str(e)}")

    def get_textures(self) -> List[TextureObject]:
        """Zwraca listę wszystkich tekstur."""
        return self._textures

    def get_texture(self, index: int) -> Optional[TextureObject]:
        """Zwraca teksturę o podanym indeksie."""
        if 0 <= index < len(self._textures):
            return self._textures[index]
        return None

    def get_texture_count(self) -> int:
        """Zwraca liczbę tekstur."""
        return len(self._textures)

    def clear(self) -> None:
        """Usuwa wszystkie tekstury."""
        self._textures = []

    def select_all(self) -> None:
        """Zaznacza wszystkie tekstury."""
        for texture in self._textures:
            texture.select()

    def deselect_all(self) -> None:
        """Odznacza wszystkie tekstury."""
        for texture in self._textures:
            texture.deselect()

    def are_all_selected(self) -> bool:
        """Sprawdza, czy wszystkie tekstury są zaznaczone."""
        return all(texture.is_selected for texture in self._textures)

    def count_selected(self) -> int:
        """Zlicza liczbę zaznaczonych tekstur."""
        return sum(1 for texture in self._textures if texture.is_selected)

    def calculate_selected_size(self) -> int:
        """Oblicza łączny rozmiar zaznaczonych tekstur."""
        return sum(
            texture.filesize for texture in self._textures if texture.is_selected
        )

    def load_sample_textures(self):
        """Ładuje przykładowe tekstury z danymi testowymi."""
        example_data = [
            {
                "nazwa": "06-09_Sunset_B.hdr",
                "szerokosc": 15000,
                "wysokosc": 7500,
                "glebia_bitowa": 32,
                "profil_koloru": "lin_srgb",
                "rozmiar_mb": 312.42,
                "kanal_alpha": False,
                "flaga": "oryginał",
                "data_utworzenia": "2025-04-06 18:35:44",
                "data_modyfikacji": "2019-07-14 20:05:10",
                "hash_sha256": "ac10686245b34977ff48850b75b48553efd9d20dad9ed342e713ebeb7f792ebc",
            },
            {
                "nazwa": "concrete_wall_001.jpg",
                "szerokosc": 4096,
                "wysokosc": 4096,
                "glebia_bitowa": 8,
                "profil_koloru": "sRGB",
                "rozmiar_mb": 8.75,
                "kanal_alpha": False,
                "flaga": "",
                "data_utworzenia": "2025-04-06 10:22:33",
                "data_modyfikacji": "2023-11-05 14:32:18",
                "hash_sha256": "e9b7c48294b2726a1e50b1ed822b93ab83a2b48c82b5f59f2278e247ec51f982",
            },
            {
                "nazwa": "metal_plate_diff.tif",
                "szerokosc": 2048,
                "wysokosc": 2048,
                "glebia_bitowa": 16,
                "profil_koloru": "Adobe RGB",
                "rozmiar_mb": 24.0,
                "kanal_alpha": True,
                "flaga": "",
                "data_utworzenia": "2025-04-05 22:15:04",
                "data_modyfikacji": "2022-08-17 09:45:26",
                "hash_sha256": "f7da45632e158a93bd128e6b09831f1d956e2d64b1b72991d32271d0189bc124",
            },
            {
                "nazwa": "hdri_studio_small.exr",
                "szerokosc": 8192,
                "wysokosc": 4096,
                "glebia_bitowa": 32,
                "profil_koloru": "scene_linear",
                "rozmiar_mb": 128.36,
                "kanal_alpha": False,
                "flaga": "oryginał",
                "data_utworzenia": "2025-04-01 11:25:14",
                "data_modyfikacji": "2024-12-03 09:12:56",
                "hash_sha256": "7a4c63e5f921b8a8d7858d39ec19c766a743f1dbeac08e9ad9baed958f3724c9",
            },
        ]

        # Słownik do mapowania kategorii na podstawie rozszerzenia
        category_map = {
            "exr": "HDR",
            "hdr": "HDR",
            "jpg": "Obraz",
            "jpeg": "Obraz",
            "png": "Obraz",
            "tif": "Obraz",
            "tiff": "Obraz",
        }

        # Dla każdego przykładu dodajemy nowe pola
        for data in example_data:
            # Szerokość i wysokość są już dostępne, tworzymy "rozdzielczość"
            if "szerokosc" in data and "wysokosc" in data:
                data["a7"] = f"{data['szerokosc']}x{data['wysokosc']}"

            # Format pliku na podstawie nazwy
            if "nazwa" in data:
                ext = os.path.splitext(data["nazwa"])[1].lower()
                data["a6"] = ext[1:] if ext else ""

            # Kategoria na podstawie rozszerzenia lub rozmiaru
            ext_key = data["a6"] if "a6" in data else ""
            if ext_key in category_map:
                if (
                    "szerokosc" in data
                    and "wysokosc" in data
                    and data["szerokosc"] == data["wysokosc"]
                    and ext_key in ["jpg", "jpeg", "png", "tif", "tiff"]
                ):
                    data["a5"] = "Tekstura"
                else:
                    data["a5"] = category_map[ext_key]
            else:
                data["a5"] = "Inny"

            # Status na podstawie flagi
            if "flaga" in data:
                flaga = data["flaga"]
                if flaga == "oryginał":
                    data["a8"] = "Oryginalny"
                elif flaga == "duplikat":
                    data["a8"] = "Duplikat"
                elif flaga == "możliwy duplikat":
                    data["a8"] = "Możliwy duplikat"
                elif flaga:
                    data["a8"] = flaga
                else:
                    data["a8"] = "Nowy"
            else:
                data["a8"] = "Nowy"

            # Przykładowe wartości dla pozostałych pól
            data["a9"] = "Sprawdź"
            data["a10"] = "System"
            data["a11"] = "1.0"

        # Tworzenie obiektów TextureObject z przykładowych danych
        self._textures = []
        for data in example_data:
            texture = TextureObject()
            for key, value in data.items():
                setattr(texture, key, value)
            self._textures.append(texture)

        # logger.debug(f"Załadowano {len(self._textures)} przykładowych tekstur")

    def sort_textures(self, key_func, reverse=False):
        """
        Sortuje tekstury według podanej funkcji klucza.

        Args:
            key_func: Funkcja zwracająca klucz sortowania dla obiektu
            reverse: Czy sortować malejąco
        """
        try:
            self._textures.sort(key=key_func, reverse=reverse)
            return True
        except Exception as e:
            logger.error(f"Błąd podczas sortowania tekstur: {str(e)}")
            return False

    def load_textures_from_analysis(self, analysis_data):
        """
        Ładuje tekstury z danych analizy (wyniki_tekstur*.json).

        Args:
            analysis_data (dict): Dane analizy z pliku wyniki_tekstur*.json
        """
        self._textures = []

        if not analysis_data or "pliki" not in analysis_data:
            logger.warning("Brak danych tekstur w analizie")
            return

        try:
            for texture_data in analysis_data["pliki"]:
                texture_obj = TextureFromAnalysis(texture_data)
                self._textures.append(texture_obj)

            logger.debug(f"Załadowano {len(self._textures)} tekstur z analizy")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania tekstur z analizy: {str(e)}")


# Dodaj nową klasę dla reprezentacji tekstury z analizy
class TextureFromAnalysis(TextureObject):
    """Reprezentuje obiekt tekstury utworzony z danych z analizy."""

    def __init__(self, texture_data=None):
        """
        Inicjalizacja obiektu tekstury z danych z analizy.

        Args:
            texture_data (dict): Dane tekstury z pliku wyniki_tekstur*.json
        """
        super().__init__()

        if texture_data:
            # Mapowanie kluczy z wyników analizy na atrybuty obiektu
            self.nazwa = texture_data.get("nazwa", "")
            self.texturePath = texture_data.get(
                "ścieżka", ""
            )  # Dla kompatybilności z ListView
            self.ścieżka = texture_data.get("ścieżka", "")
            self.szerokosc = texture_data.get("szerokość")
            self.wysokosc = texture_data.get("wysokość")
            self.glebia_bitowa = texture_data.get("głębia_bitowa")
            self.profil_koloru = texture_data.get("profil_koloru", "")
            self.rozmiar_mb = texture_data.get("rozmiar_mb", 0)
            self.kanal_alpha = texture_data.get("kanał_alpha", False)
            self.flaga = texture_data.get("flaga", "")
            self.data_utworzenia = texture_data.get("data_utworzenia", "")
            self.data_modyfikacji = texture_data.get("data_modyfikacji", "")
            self.hash_sha256 = texture_data.get("hash_sha256", "")
            self._selected = False
            self.filesize = int(self.rozmiar_mb * 1024 * 1024) if self.rozmiar_mb else 0

            # Dodatkowe atrybuty dla kolumn A5-A11
            # Te wartości moglibyśmy też wygenerować bazując na innych polach
            rozszerzenie = os.path.splitext(self.nazwa)[1].lower() if self.nazwa else ""

            # A5 - Kategoria
            if rozszerzenie in [".exr", ".hdr"]:
                self.a5 = "HDR"
            elif rozszerzenie in [".tx"]:
                self.a5 = "TX"
            elif rozszerzenie in [".jpg", ".jpeg", ".png", ".tif", ".tiff"]:
                if self.szerokosc == self.wysokosc:
                    self.a5 = "Tekstura"
                else:
                    self.a5 = "Obraz"
            else:
                self.a5 = "Inny"

            # A6 - Format (rozszerzenie bez kropki)
            self.a6 = rozszerzenie[1:] if rozszerzenie else ""

            # A7 - Rozdzielczość
            self.a7 = (
                f"{self.szerokosc}x{self.wysokosc}"
                if self.szerokosc and self.wysokosc
                else ""
            )

            # A8 - Status bazujący na fladze
            if self.flaga == "oryginał":
                self.a8 = "Oryginalny"
            elif self.flaga == "duplikat":
                self.a8 = "Duplikat"
            elif self.flaga == "możliwy duplikat":
                self.a8 = "Możliwy duplikat"
            else:
                self.a8 = "Nowy"

            # Pozostałe pola wypełniane przykładowymi wartościami
            self.a9 = "Sprawdź"
            self.a10 = texture_data.get("narzędzie_analizy", "System")
            self.a11 = "1.0"
