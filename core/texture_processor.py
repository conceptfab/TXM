#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Texture Processor - biblioteka do analizy plików tekstur
"""

import concurrent.futures
import datetime
import hashlib
import json
import logging
import os
import platform
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import c4d

# Stała dla ukrywania okna konsoli na Windows
CREATE_NO_WINDOW = 0x08000000

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("TexPr")

# Formaty plików, które uznajemy za graficzne
GRAFICZNE_ROZSZERZENIA = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
    ".svg",
    ".exr",
    ".hdr",
    ".tx",
    ".tga",
    ".psd",
    ".heic",
    ".heif",
    ".dds",
    ".ico",
    ".raw",
    ".cr2",
    ".nef",
}

# Formaty plików wymagające oiiotool
FORMATY_OIIOTOOL = {".exr", ".hdr", ".tx"}


def uruchom_proces_w_tle(polecenie, **kwargs):
    """
    Uruchamia aplikację w tle, ukrywając okno konsoli na Windows.

    Args:
        polecenie: Lista zawierająca ścieżkę do pliku wykonywalnego i argumenty
        **kwargs: Dodatkowe argumenty dla subprocess.Popen

    Returns:
        Obiekt subprocess.Popen
    """
    # Na systemach Windows używamy flagi CREATE_NO_WINDOW
    if platform.system() == "Windows":
        kwargs["creationflags"] = CREATE_NO_WINDOW

    # Dla innych systemów nic nie robimy
    return subprocess.Popen(
        polecenie, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kwargs
    )


@dataclass
class StatusPostępu:
    """Klasa do raportowania postępu operacji."""

    etap: str
    postęp: float  # 0.0 do 1.0
    wiadomość: str = ""
    szczegóły: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetadanePliku:
    """Klasa przechowująca metadane pliku graficznego."""

    ścieżka: str
    rozszerzenie: str
    rozmiar_mb: float
    data_utworzenia: str
    data_modyfikacji: str
    hash_sha256: str
    szerokość: Optional[int] = None
    wysokość: Optional[int] = None
    kanał_alpha: Optional[bool] = None
    głębia_bitowa: Optional[int] = None
    profil_koloru: Optional[str] = None
    flaga: str = ""  # "oryginał", "możliwy duplikat", "duplikat" lub ""
    id_grupy: str = ""  # ID grupy duplikatów, np. "01-0", "01-D1" itp.
    narzędzie_analizy: str = ""  # Narzędzie użyte do analizy metadanych (PIL, oiiotool)
    błąd_analizy: str = ""  # Informacja o błędzie, jeśli wystąpił
    nazwa: str = ""  # Nazwa pliku bez ścieżki - NOWE POLE

    def __post_init__(self):
        """Wykonuje dodatkowe działania po inicjalizacji."""
        # Ekstrakcja nazwy pliku ze ścieżki
        self.nazwa = os.path.basename(self.ścieżka)

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje obiekt do słownika."""
        dane = asdict(self)
        # Zaokrąglanie rozmiaru_mb do 2 miejsc po przecinku
        if isinstance(dane["rozmiar_mb"], float):
            dane["rozmiar_mb"] = round(dane["rozmiar_mb"], 2)

        # Zmiana kolejności pól w słowniku na zgodną z oczekiwanym formatem
        nowa_kolejność = [
            "ścieżka",
            "nazwa",
            "rozszerzenie",
            "szerokość",
            "wysokość",
            "głębia_bitowa",
            "profil_koloru",
            "rozmiar_mb",
            "kanał_alpha",
            "flaga",
            "data_utworzenia",
            "data_modyfikacji",
            "hash_sha256",
            "id_grupy",
            "narzędzie_analizy",
            "błąd_analizy",
        ]

        # Tworzenie nowego słownika z określoną kolejnością kluczy
        posortowane_dane = {k: dane[k] for k in nowa_kolejność if k in dane}

        # Dodajemy pozostałe klucze, które mogły nie być uwzględnione w nowej_kolejności
        for k in dane:
            if k not in posortowane_dane:
                posortowane_dane[k] = dane[k]

        return posortowane_dane


class TextureProcessor:
    """
    Główna klasa do przetwarzania tekstur.
    """

    def __init__(self, ścieżka_oiiotool: str = "oiiotool"):
        """
        Inicjalizacja procesora tekstur.

        Args:
            ścieżka_oiiotool: Ścieżka do narzędzia oiiotool.
        """
        self.ścieżka_oiiotool = ścieżka_oiiotool
        self._callback_statusu = None
        self.oiiotool_dostępny = self._sprawdz_oiiotool()

    def _sprawdz_oiiotool(self) -> bool:
        """
        Sprawdza czy narzędzie oiiotool jest dostępne.

        Returns:
            True jeśli narzędzie jest dostępne, False w przeciwnym przypadku.
        """
        # Najpierw sprawdź pełną ścieżkę
        oiiotool_exe = self.ścieżka_oiiotool

        # Jeśli nie jest to pełna ścieżka, spróbuj znaleźć w katalogu programu
        if not os.path.isfile(oiiotool_exe):
            program_dir = os.path.dirname(os.path.abspath(__file__))
            candidate_paths = [
                os.path.join(program_dir, "oiiotool", "oiiotool.exe"),
                os.path.join(program_dir, "oiiotool.exe"),
                "oiiotool.exe",
            ]

            for path in candidate_paths:
                if os.path.isfile(path):
                    oiiotool_exe = path
                    break

        # Sprawdź, czy plik istnieje
        if os.path.isfile(oiiotool_exe):
            self.ścieżka_oiiotool = oiiotool_exe
            logger.debug(f"Znaleziono oiiotool: {oiiotool_exe}")

            # Sprawdź czy można uruchomić
            try:
                p = uruchom_proces_w_tle([oiiotool_exe, "--help"])
                stdout, stderr = p.communicate(timeout=5)

                if p.returncode == 0:
                    logger.debug("Narzędzie oiiotool działa poprawnie.")
                    return True
                else:
                    logger.warning(
                        f"Narzędzie oiiotool zwróciło kod błędu: {p.returncode}"
                    )
                    logger.warning(f"Wyjście stderr: {stderr}")
                    return False
            except Exception as e:
                logger.error(f"Błąd podczas testowania oiiotool: {str(e)}")
                return False
        else:
            logger.warning(
                f"Nie znaleziono narzędzia oiiotool. Sprawdzone ścieżki: {oiiotool_exe}, {candidate_paths}"
            )
            return False

    def ustaw_callback_statusu(self, callback):
        """
        Ustawia funkcję callback do raportowania postępu.

        Args:
            callback: Funkcja, która przyjmuje obiekt StatusPostępu.
        """
        self._callback_statusu = callback

    def _raportuj_status(
        self,
        etap: str,
        postęp: float,
        wiadomość: str = "",
        szczegóły: Dict[str, Any] = None,
    ):
        """
        Raportuje obecny status operacji poprzez callback.

        Args:
            etap: Nazwa etapu przetwarzania.
            postęp: Wartość od 0.0 do 1.0 oznaczająca postęp.
            wiadomość: Dodatkowa informacja tekstowa.
            szczegóły: Słownik z dodatkowymi informacjami.
        """
        if self._callback_statusu:
            status = StatusPostępu(
                etap=etap, postęp=postęp, wiadomość=wiadomość, szczegóły=szczegóły or {}
            )
            self._callback_statusu(status)

    def przetwarzaj_folder(
        self, ścieżka_folderu: str, przeszukuj_podfoldery: bool = False
    ) -> Dict[str, Any]:
        """
        Główna funkcja do przetwarzania folderu z teksturami.

        Args:
            ścieżka_folderu: Ścieżka do folderu z plikami.
            przeszukuj_podfoldery: Czy przeszukiwać również podfoldery.

        Returns:
            Słownik z wynikami analizy.
        """
        wyniki = {}

        # Etap 1: Znajdowanie i sortowanie plików
        self._raportuj_status("wyszukiwanie", 0.0, "Rozpoczęcie wyszukiwania plików...")
        pliki_według_rozszerzeń = self._znajdź_i_posortuj_pliki(
            ścieżka_folderu, przeszukuj_podfoldery
        )
        wyniki["pliki_według_rozszerzeń"] = {
            k: len(v) for k, v in pliki_według_rozszerzeń.items()
        }

        # Etap 2: Tworzenie metadanych podstawowych dla plików
        self._raportuj_status(
            "metadane_podstawowe", 0.0, "Tworzenie podstawowych metadanych..."
        )
        metadane_plików = self._utwórz_podstawowe_metadane(pliki_według_rozszerzeń)

        # Etap 3: Wykrywanie możliwych duplikatów na podstawie nazwy
        self._raportuj_status(
            "możliwe_duplikaty",
            0.0,
            "Wykrywanie możliwych duplikatów na podstawie nazwy...",
        )
        metadane_plików = self._oznacz_możliwe_duplikaty(metadane_plików)

        # Etap 4: Obliczanie hash'y SHA-256
        self._raportuj_status("hash", 0.0, "Obliczanie hash'y plików...")
        metadane_plików = self._oblicz_hashe(metadane_plików)

        # Etap 5: Wykrywanie dokładnych duplikatów na podstawie hash'y
        self._raportuj_status(
            "dokładne_duplikaty", 0.0, "Wykrywanie dokładnych duplikatów..."
        )
        metadane_plików = self._oznacz_dokładne_duplikaty(metadane_plików)

        # Etap 6: Pobieranie szczegółowych metadanych graficznych
        self._raportuj_status(
            "metadane_graficzne",
            0.0,
            "Pobieranie szczegółowych metadanych graficznych...",
        )
        metadane_plików, stats_narzędzia = self._pobierz_metadane_graficzne(
            metadane_plików
        )

        # Przygotowanie wyników końcowych
        wyniki["pliki"] = [m.to_dict() for m in metadane_plików]
        wyniki["statystyki"] = self._generuj_statystyki(
            metadane_plików, stats_narzędzia
        )

        # Dodanie informacji o oiiotool
        wyniki["konfiguracja"] = {
            "oiiotool_dostępny": self.oiiotool_dostępny,
            "ścieżka_oiiotool": self.ścieżka_oiiotool if self.oiiotool_dostępny else "",
            "formaty_specjalistyczne": list(FORMATY_OIIOTOOL),
        }

        self._raportuj_status("zakończono", 1.0, "Przetwarzanie zakończone.")
        return wyniki

    def _znajdź_i_posortuj_pliki(
        self, ścieżka_folderu: str, przeszukuj_podfoldery: bool
    ) -> Dict[str, List[str]]:
        """
        Znajduje i sortuje pliki według rozszerzeń.

        Args:
            ścieżka_folderu: Ścieżka do folderu z plikami.
            przeszukuj_podfoldery: Czy przeszukiwać również podfoldery.

        Returns:
            Słownik mapujący rozszerzenia na listy ścieżek plików.
        """
        pliki_według_rozszerzeń = {}
        liczba_znalezionych = 0

        # Funkcja do przetwarzania pojedynczego pliku
        def przetwórz_plik(ścieżka_pliku):
            rozszerzenie = os.path.splitext(ścieżka_pliku)[1].lower()

            if rozszerzenie in GRAFICZNE_ROZSZERZENIA:
                kategoria = rozszerzenie
            else:
                kategoria = "pozostałe"

            return kategoria, str(ścieżka_pliku)

        # Zbieranie plików
        pliki_do_przetworzenia = []

        if przeszukuj_podfoldery:
            for root, _, files in os.walk(ścieżka_folderu):
                for file in files:
                    pliki_do_przetworzenia.append(os.path.join(root, file))
        else:
            pliki_do_przetworzenia = [
                os.path.join(ścieżka_folderu, f)
                for f in os.listdir(ścieżka_folderu)
                if os.path.isfile(os.path.join(ścieżka_folderu, f))
            ]

        total_files = len(pliki_do_przetworzenia)

        # Przetwarzanie równoległe
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for i, (kategoria, ścieżka) in enumerate(
                executor.map(przetwórz_plik, pliki_do_przetworzenia)
            ):
                if kategoria not in pliki_według_rozszerzeń:
                    pliki_według_rozszerzeń[kategoria] = []

                pliki_według_rozszerzeń[kategoria].append(ścieżka)
                liczba_znalezionych += 1

                if i % 50 == 0 or i == total_files - 1:
                    postęp = (i + 1) / total_files if total_files > 0 else 1.0
                    self._raportuj_status(
                        "wyszukiwanie",
                        postęp,
                        f"Znaleziono {liczba_znalezionych} plików...",
                        {"znalezione": liczba_znalezionych},
                    )

        return pliki_według_rozszerzeń

    def _utwórz_podstawowe_metadane(
        self, pliki_według_rozszerzeń: Dict[str, List[str]]
    ) -> List[MetadanePliku]:
        """
        Tworzy podstawowe metadane dla wszystkich plików.

        Args:
            pliki_według_rozszerzeń: Słownik mapujący rozszerzenia na listy ścieżek plików.

        Returns:
            Lista obiektów MetadanePliku z podstawowymi informacjami.
        """
        metadane = []
        wszystkie_pliki = []

        for rozszerzenie, ścieżki in pliki_według_rozszerzeń.items():
            for ścieżka in ścieżki:
                wszystkie_pliki.append((ścieżka, rozszerzenie))

        total_files = len(wszystkie_pliki)

        def utwórz_metadane_pliku(args):
            ścieżka, rozszerzenie = args
            try:
                statinfo = os.stat(ścieżka)
                rozmiar_mb = round(statinfo.st_size / (1024 * 1024), 2)

                # Pobieranie czasów utworzenia i modyfikacji
                data_utworzenia = datetime.datetime.fromtimestamp(
                    statinfo.st_ctime
                ).strftime("%Y-%m-%d %H:%M:%S")
                data_modyfikacji = datetime.datetime.fromtimestamp(
                    statinfo.st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S")

                return MetadanePliku(
                    ścieżka=ścieżka,
                    rozszerzenie=rozszerzenie,
                    rozmiar_mb=rozmiar_mb,
                    data_utworzenia=data_utworzenia,
                    data_modyfikacji=data_modyfikacji,
                    hash_sha256="",  # Wypełniane później
                )
            except Exception as e:
                logger.error(f"Błąd podczas przetwarzania pliku {ścieżka}: {str(e)}")
                return None

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for i, metadane_pliku in enumerate(
                executor.map(utwórz_metadane_pliku, wszystkie_pliki)
            ):
                if metadane_pliku:
                    metadane.append(metadane_pliku)

                if i % 50 == 0 or i == total_files - 1:
                    postęp = (i + 1) / total_files if total_files > 0 else 1.0
                    self._raportuj_status(
                        "metadane_podstawowe",
                        postęp,
                        f"Przetworzono podstawowe metadane dla {i+1} z {total_files} plików...",
                    )

        return metadane

    def _oznacz_możliwe_duplikaty(
        self, metadane_plików: List[MetadanePliku]
    ) -> List[MetadanePliku]:
        """
        Oznacza możliwe duplikaty na podstawie nazwy pliku.

        Args:
            metadane_plików: Lista obiektów MetadanePliku.

        Returns:
            Zaktualizowana lista obiektów MetadanePliku.
        """
        # Grupowanie plików według nazwy bez rozszerzenia
        grupy_plików = {}

        for i, meta in enumerate(metadane_plików):
            nazwa_bez_rozszerzenia = os.path.splitext(os.path.basename(meta.ścieżka))[0]

            if nazwa_bez_rozszerzenia not in grupy_plików:
                grupy_plików[nazwa_bez_rozszerzenia] = []

            grupy_plików[nazwa_bez_rozszerzenia].append((i, meta))

            if i % 100 == 0 or i == len(metadane_plików) - 1:
                postęp = (i + 1) / len(metadane_plików)
                self._raportuj_status(
                    "możliwe_duplikaty",
                    postęp * 0.5,  # Pierwsza połowa etapu
                    f"Grupowanie plików według nazwy: {i+1} z {len(metadane_plików)}...",
                )

        # Oznaczanie możliwych duplikatów
        liczba_grup = len(grupy_plików)
        for i, (nazwa, grupa) in enumerate(grupy_plików.items()):
            if len(grupa) > 1:
                # Sortowanie według daty utworzenia (od najstarszego)
                grupa.sort(
                    key=lambda x: datetime.datetime.strptime(
                        x[1].data_utworzenia, "%Y-%m-%d %H:%M:%S"
                    )
                )

                # Najstarszy plik w grupie
                metadane_plików[grupa[0][0]].flaga = "oryginał"

                # Pozostałe pliki w grupie
                for idx, _ in grupa[1:]:
                    metadane_plików[idx].flaga = "możliwy duplikat"

            if i % 50 == 0 or i == liczba_grup - 1:
                postęp = (i + 1) / liczba_grup
                self._raportuj_status(
                    "możliwe_duplikaty",
                    0.5 + postęp * 0.5,  # Druga połowa etapu
                    f"Oznaczanie możliwych duplikatów: {i+1} z {liczba_grup} grup...",
                )

        return metadane_plików

    def _oblicz_hashe(
        self, metadane_plików: List[MetadanePliku]
    ) -> List[MetadanePliku]:
        """
        Oblicza hash SHA-256 dla wszystkich plików.

        Args:
            metadane_plików: Lista obiektów MetadanePliku.

        Returns:
            Zaktualizowana lista obiektów MetadanePliku.
        """

        def oblicz_hash_pliku(index_meta):
            index, meta = index_meta
            try:
                with open(meta.ścieżka, "rb") as file:
                    sha256 = hashlib.sha256()
                    for blok in iter(lambda: file.read(4096), b""):
                        sha256.update(blok)
                    return index, sha256.hexdigest()
            except Exception as e:
                logger.error(
                    f"Błąd podczas obliczania hash'a dla pliku {meta.ścieżka}: {str(e)}"
                )
                return index, ""

        total_files = len(metadane_plików)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            for i, (index, hash_value) in enumerate(
                executor.map(oblicz_hash_pliku, enumerate(metadane_plików))
            ):
                metadane_plików[index].hash_sha256 = hash_value

                if i % 20 == 0 or i == total_files - 1:
                    postęp = (i + 1) / total_files
                    self._raportuj_status(
                        "hash",
                        postęp,
                        f"Obliczono hash dla {i+1} z {total_files} plików...",
                    )

        return metadane_plików

    def _oznacz_dokładne_duplikaty(
        self, metadane_plików: List[MetadanePliku]
    ) -> List[MetadanePliku]:
        """
        Oznacza dokładne duplikaty na podstawie hash'y SHA-256.

        Args:
            metadane_plików: Lista obiektów MetadanePliku.

        Returns:
            Zaktualizowana lista obiektów MetadanePliku.
        """
        # Grupowanie według rozszerzeń
        pliki_według_rozszerzeń = {}

        for i, meta in enumerate(metadane_plików):
            if meta.hash_sha256:  # Pomijamy pliki bez hash'a
                if meta.rozszerzenie not in pliki_według_rozszerzeń:
                    pliki_według_rozszerzeń[meta.rozszerzenie] = []

                pliki_według_rozszerzeń[meta.rozszerzenie].append((i, meta))

            if i % 100 == 0 or i == len(metadane_plików) - 1:
                postęp = (i + 1) / len(metadane_plików)
                self._raportuj_status(
                    "dokładne_duplikaty",
                    postęp * 0.3,  # Pierwsze 30% etapu
                    f"Grupowanie plików według rozszerzeń: {i+1} z {len(metadane_plików)}...",
                )

        # Dla każdego rozszerzenia znajdujemy duplikaty
        licznik_grup = 0
        liczba_rozszerzeń = len(pliki_według_rozszerzeń)

        for i, (rozszerzenie, pliki) in enumerate(pliki_według_rozszerzeń.items()):
            hashe = {}

            # Grupowanie według hash'y
            for idx, meta in pliki:
                if meta.hash_sha256 not in hashe:
                    hashe[meta.hash_sha256] = []
                hashe[meta.hash_sha256].append((idx, meta))

            # Oznaczanie duplikatów
            for hash_value, grupa in hashe.items():
                if len(grupa) > 1:
                    # Sortowanie według daty utworzenia (od najstarszego)
                    grupa.sort(
                        key=lambda x: datetime.datetime.strptime(
                            x[1].data_utworzenia, "%Y-%m-%d %H:%M:%S"
                        )
                    )

                    # Generuj ID grupy
                    licznik_grup += 1
                    id_grupy = f"{licznik_grup:02d}"

                    # Oryginał
                    org_idx, _ = grupa[0]
                    metadane_plików[org_idx].flaga = "oryginał"
                    metadane_plików[org_idx].id_grupy = f"{id_grupy}-o"

                    # Duplikaty
                    for j, (dup_idx, _) in enumerate(grupa[1:]):
                        metadane_plików[dup_idx].flaga = "duplikat"
                        metadane_plików[dup_idx].id_grupy = f"{id_grupy}-D{j+1}"

            postęp = (i + 1) / liczba_rozszerzeń
            self._raportuj_status(
                "dokładne_duplikaty",
                0.3 + postęp * 0.7,  # Pozostałe 70% etapu
                f"Oznaczanie dokładnych duplikatów dla rozszerzenia {rozszerzenie}...",
            )

        return metadane_plików

    def _pobierz_metadane_graficzne(
        self, metadane_plików: List[MetadanePliku]
    ) -> Tuple[List[MetadanePliku], Dict[str, Any]]:
        """
        Pobiera szczegółowe metadane graficzne dla plików.

        Args:
            metadane_plików: Lista obiektów MetadanePliku.

        Returns:
            Tuple zawierające zaktualizowaną listę obiektów MetadanePliku i statystyki narzędzi.
        """

        # Statystyki dla narzędzi
        stats_narzędzia = {
            "oiiotool": 0,
            "PIL": 0,
            "brak": 0,
            "błąd": 0,
            "formaty_oiiotool": {"poprawnie": 0, "niepoprawnie": 0},
        }

        # Ograniczamy liczbę wątków do stałej wartości zamiast pobierania jej z nieistniejącej funkcji
        max_workers = 4  # Używamy bezpiecznej stałej wartości
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Przetwarzanie plików w puli wątków
            futures = []
            for i, meta in enumerate(metadane_plików):
                futures.append(
                    executor.submit(self._pobierz_metadane_graficzne_pliku, (i, meta))
                )

            # Zbieranie wyników
            for future in concurrent.futures.as_completed(futures):
                try:
                    index, metadane, narzędzie, błąd = future.result()
                    if metadane:
                        metadane_plików[index].__dict__.update(metadane)
                        metadane_plików[index].narzędzie_analizy = narzędzie
                        if błąd:
                            metadane_plików[index].błąd_analizy = błąd
                            stats_narzędzia["błąd"] += 1
                        else:
                            if narzędzie == "oiiotool":
                                stats_narzędzia["formaty_oiiotool"]["poprawnie"] += 1
                            else:
                                stats_narzędzia["formaty_pil"]["poprawnie"] += 1
                except Exception as e:
                    logger.error(f"Błąd podczas przetwarzania pliku: {str(e)}")
                    stats_narzędzia["błąd"] += 1

        return metadane_plików, stats_narzędzia

    def _pobierz_metadane_graficzne_pliku(
        self, index_meta: Tuple[int, MetadanePliku]
    ) -> Tuple[int, Dict[str, Any], str, str]:
        """
        Pobiera metadane graficzne dla pojedynczego pliku.

        Args:
            index_meta: Krotka zawierająca indeks pliku i obiekt MetadanePliku.

        Returns:
            Krotka (indeks, słownik_metadanych, nazwa_narzędzia, błąd).
        """
        index, meta = index_meta

        if meta.rozszerzenie == "pozostałe":
            return index, None, "", ""

        try:
            # Strategia: preferuj oiiotool dla wszystkich formatów, jeśli jest dostępny
            if self.oiiotool_dostępny:
                try:
                    metadane, narzędzie, błąd = self._pobierz_metadane_oiiotool(meta)
                    if metadane:
                        return index, metadane, narzędzie, błąd
                    # Jeśli oiiotool nie zwrócił metadanych, spróbuj użyć PIL
                except Exception as e:
                    logger.error(
                        f"Błąd podczas używania oiiotool dla {meta.ścieżka}: {e}"
                    )
                    # Kontynuuj i spróbuj użyć PIL jako zapasowego rozwiązania

            # Dla standardowych formatów lub gdy oiiotool zawiódł, użyj PIL
            try:
                metadane, narzędzie, błąd = self._pobierz_metadane_pil(meta)
                return index, metadane, narzędzie, błąd
            except Exception as e:
                logger.error(f"Błąd podczas używania PIL dla {meta.ścieżka}: {e}")

                # Jeśli rozszerzenie wymaga oiiotool, a nie użyliśmy go wcześniej
                if (
                    meta.rozszerzenie.lower() in FORMATY_OIIOTOOL
                    and not self.oiiotool_dostępny
                ):
                    return (
                        index,
                        None,
                        "błąd",
                        f"PIL: {str(e)}, oiiotool: niedostępny",
                    )
                else:
                    return index, None, "błąd", f"PIL: {str(e)}"

        except Exception as e:
            logger.exception(
                f"Krytyczny błąd podczas pobierania metadanych dla {meta.ścieżka}"
            )
            return index, None, "błąd", str(e)

    def _pobierz_metadane_pil(
        self, meta: MetadanePliku
    ) -> Tuple[Dict[str, Any], str, str]:
        """
        Pobiera metadane przy użyciu biblioteki PIL.

        Args:
            meta: Metadane pliku.

        Returns:
            Krotka (słownik_metadanych, nazwa_narzędzia, błąd).
        """
        try:
            from PIL import Image

            # Normalizacja ścieżki
            ścieżka_pliku = os.path.normpath(meta.ścieżka)

            # Logowanie próby otwarcia pliku
            logger.debug(f"Próba otwarcia pliku przez PIL: {ścieżka_pliku}")

            # Otwórz obraz z zachowaniem dodatkowych informacji
            img = Image.open(ścieżka_pliku)

            # Pobierz podstawowe informacje
            szerokość, wysokość = img.size

            # Sprawdzanie kanału alpha - ZOPTYMALIZOWANE
            img_mode = img.mode
            ma_alpha = (
                img_mode.endswith("A") or "A" in img_mode or img_mode in ["RGBA", "LA"]
            )

            # Głębia bitowa i tryb koloru
            głębia_bitowa = 8  # Domyślnie
            if img_mode in ["I", "F"]:
                głębia_bitowa = 32
            elif img_mode in ["I;16", "RGB;16", "LA;16"]:
                głębia_bitowa = 16

            # Profil koloru
            profil_koloru = "sRGB"  # Domyślnie
            if "icc_profile" in img.info:
                profil_koloru = "Embedded ICC"

            # Dodatkowe informacje diagnostyczne
            logger.debug(
                f"PIL informacje o pliku {ścieżka_pliku}: tryb={img_mode}, format={img.format}, info={str(img.info)[:100]}..."
            )

            return (
                {
                    "szerokość": szerokość,
                    "wysokość": wysokość,
                    "kanał_alpha": ma_alpha,
                    "głębia_bitowa": głębia_bitowa,
                    "profil_koloru": profil_koloru,
                },
                "PIL",
                "",
            )
        except ImportError as e:
            logger.error(f"Biblioteka PIL jest niedostępna: {e}")
            return None, "brak", "Biblioteka PIL jest niedostępna"
        except Exception as e:
            logger.exception(
                f"Błąd podczas analizy pliku {meta.ścieżka} przez PIL: {e}"
            )
            return None, "błąd", f"PIL: {str(e)}"

    def _pobierz_metadane_oiiotool(
        self, meta: MetadanePliku
    ) -> Tuple[Dict[str, Any], str, str]:
        """
        Pobiera metadane przy użyciu oiiotool dla plików graficznych.

        Args:
            meta: Metadane pliku.

        Returns:
            Krotka (słownik_metadanych, nazwa_narzędzia, błąd).
        """
        try:
            # Normalizacja ścieżki (zamiana backslashy na forwardslasze)
            ścieżka_pliku = os.path.normpath(meta.ścieżka).replace("\\", "/")

            # Przygotowanie komendy dla oiiotool z opcją --info -v (verbose)
            cmd = [self.ścieżka_oiiotool, "--info", "-v", ścieżka_pliku]
            logger.debug(f"Wykonuję komendę: {' '.join(cmd)}")

            # Uruchom oiiotool w tle bez pokazywania okna
            proces = uruchom_proces_w_tle(cmd)
            stdout, stderr = proces.communicate()

            if proces.returncode != 0:
                logger.error(
                    f"Błąd wywołania oiiotool (kod wyjścia {proces.returncode}): {stderr}"
                )
                return (
                    None,
                    "błąd",
                    f"oiiotool zwróciło kod błędu: {proces.returncode}, stderr: {stderr}",
                )

            wyjście = stdout

            # Parsujemy tekstowy output z 'oiiotool --info -v'
            parsed_meta = self._parsuj_wyjście_oiiotool(wyjście, meta.ścieżka)

            if (
                not parsed_meta
                or not parsed_meta.get("szerokość")
                or not parsed_meta.get("wysokość")
            ):
                # Jeśli nie udało się sparsować wyników, spróbujmy dodatkowo z flagą --stats
                cmd_stats = [self.ścieżka_oiiotool, "--stats", ścieżka_pliku]
                logger.debug(f"Próba alternatywna: {' '.join(cmd_stats)}")

                # Uruchom oiiotool z opcją --stats w tle
                proces_stats = uruchom_proces_w_tle(cmd_stats)
                stdout_stats, stderr_stats = proces_stats.communicate()

                if proces_stats.returncode == 0:
                    # Próbujemy sparsować wyniki z --stats
                    stats_meta = self._parsuj_wyjście_oiiotool(
                        stdout_stats, meta.ścieżka
                    )

                    # Łączymy wyniki jeśli coś udało się znaleźć
                    if stats_meta:
                        for key, value in stats_meta.items():
                            if value and (
                                not parsed_meta.get(key)
                                or parsed_meta[key] == "Nie znaleziono"
                            ):
                                parsed_meta[key] = value

            # Jeśli nadal nie mamy szerokości i wysokości, to znaczy, że coś poszło nie tak
            if (
                not parsed_meta
                or not parsed_meta.get("szerokość")
                or not parsed_meta.get("wysokość")
            ):
                logger.warning(
                    f"Nie udało się odczytać wymiarów obrazu dla pliku: {ścieżka_pliku}"
                )
                return None, "błąd", "Nie udało się odczytać wymiarów obrazu"

            return (
                {
                    "szerokość": parsed_meta.get("szerokość"),
                    "wysokość": parsed_meta.get("wysokość"),
                    "kanał_alpha": parsed_meta.get("kanał_alpha") == "Tak",
                    "głębia_bitowa": self._konwertuj_głębię_bitową(
                        parsed_meta.get("głębia_bitowa")
                    ),
                    "profil_koloru": parsed_meta.get("profil_koloru"),
                },
                "oiiotool",
                "",
            )
        except Exception as e:
            logger.exception(
                f"Krytyczny błąd podczas używania oiiotool dla pliku {meta.ścieżka}"
            )
            return None, "błąd", f"oiiotool: {str(e)}"

    def _parsuj_wyjście_oiiotool(
        self, output: str, ścieżka_pliku: str
    ) -> Dict[str, Any]:
        """
        Parsuje tekstowy output z 'oiiotool --info -v' lub 'oiiotool --stats'.
        Implementacja oparta na kodzie z oiiotool_test.py.

        Args:
            output: Wyjście z oiiotool.
            ścieżka_pliku: Ścieżka do pliku dla logów.

        Returns:
            Słownik z metadanymi.
        """
        metadata = {
            "szerokość": None,
            "wysokość": None,
            "kanał_alpha": "Nie",  # Domyślnie nie
            "głębia_bitowa": None,
            "profil_koloru": None,
        }

        # Szerokość i wysokość (szuka linii typu "1920 x 1080")
        res_match = re.search(r"(\d+)\s*x\s*(\d+)", output)
        if res_match:
            metadata["szerokość"] = int(res_match.group(1))
            metadata["wysokość"] = int(res_match.group(2))

        # Kanał Alpha (szuka 'A' w liście kanałów lub informacji o 4 kanałach)
        pattern = r"channel list:\s*(.*)"
        channel_list_match = re.search(pattern, output, re.IGNORECASE)
        if channel_list_match:
            channels = channel_list_match.group(1).upper()
            if "A" in channels.split(","):
                metadata["kanał_alpha"] = "Tak"
        else:
            # Sprawdź pierwszą linię (alternatywa)
            pattern = r"^\S+?\s*:\s*\d+\s*x\s*\d+,\s*(\d+)\s*channel"
            first_line_match = re.search(pattern, output, re.MULTILINE)
            if first_line_match:
                num_channels = int(first_line_match.group(1))
                # Założenie: 4 lub więcej kanałów często oznacza RGBA lub więcej
                if num_channels >= 4:
                    metadata["kanał_alpha"] = "Tak"
            # Jeszcze jedna próba - szukanie "Alpha" w metadanych
            elif re.search(r"Alpha", output, re.IGNORECASE):
                metadata["kanał_alpha"] = "Tak"

        # Głębia bitowa (szuka "format:")
        format_match = re.search(r"format:\s*(\S+)", output, re.IGNORECASE)
        if format_match:
            oiio_format = format_match.group(1).lower()
            # Mapowanie formatów OIIO na bardziej opisowe nazwy
            format_map = {
                "uint8": "8-bit integer",
                "int8": "8-bit integer (signed)",
                "uint16": "16-bit integer",
                "int16": "16-bit integer (signed)",
                "uint32": "32-bit integer",
                "int32": "32-bit integer (signed)",
                "half": "16-bit float (half)",
                "float": "32-bit float",
                "double": "64-bit float (double)",
            }
            metadata["głębia_bitowa"] = format_map.get(oiio_format, oiio_format)

        # Profil koloru (szuka "oiio:ColorSpace")
        pattern = r'oiio:ColorSpace:\s*"([^"]+)"'
        colorspace_match = re.search(pattern, output, re.IGNORECASE)
        if colorspace_match:
            metadata["profil_koloru"] = colorspace_match.group(1)
        else:
            # Czasem może być w innym atrybucie lub wnioskowany
            if ".exr" in output.lower() and "scene_linear" in output.lower():
                metadata["profil_koloru"] = "scene_linear"
            elif re.search(r"sRGB", output, re.IGNORECASE):
                metadata["profil_koloru"] = "sRGB"

        # Jeśli nie znaleźliśmy profilu koloru, ustaw domyślny na podstawie rozszerzenia
        if not metadata["profil_koloru"]:
            ext = os.path.splitext(ścieżka_pliku)[1].lower()
            if ext == ".exr":
                metadata["profil_koloru"] = "scene_linear"
            else:
                metadata["profil_koloru"] = "sRGB"

        # Jeśli nie udało się określić głębi bitowej, ustaw domyślne dla znanych formatów
        if not metadata["głębia_bitowa"]:
            ext = os.path.splitext(ścieżka_pliku)[1].lower()
            if ext == ".exr":
                metadata["głębia_bitowa"] = "32-bit float"
            elif ext == ".hdr":
                metadata["głębia_bitowa"] = "32-bit float"
            elif ext == ".tx":
                metadata["głębia_bitowa"] = "16-bit float (half)"
            else:
                metadata["głębia_bitowa"] = "8-bit integer"

        return metadata

    def _konwertuj_głębię_bitową(self, głębia_str: Optional[str]) -> Optional[int]:
        """
        Konwertuje opisową głębię bitową na wartość liczbową.

        Args:
            głębia_str: Opisowa głębia bitowa.

        Returns:
            Wartość liczbowa głębi bitowej lub None.
        """
        if not głębia_str:
            return None

        if "8-bit" in głębia_str:
            return 8
        elif "16-bit" in głębia_str or "half" in głębia_str:
            return 16
        elif "32-bit" in głębia_str or "float" in głębia_str:
            return 32
        elif "64-bit" in głębia_str or "double" in głębia_str:
            return 64

        # Próba ekstrahowania liczby z stringa
        match = re.search(r"(\d+)-bit", głębia_str)
        if match:
            return int(match.group(1))

        return None

    def _generuj_statystyki(
        self, metadane_plików: List[MetadanePliku], stats_narzędzia: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generuje statystyki dotyczące przetworzonych plików.

        Args:
            metadane_plików: Lista obiektów MetadanePliku.
            stats_narzędzia: Statystyki użycia narzędzi do analizy.

        Returns:
            Słownik ze statystykami.
        """
        statystyki = {
            "liczba_plików_ogółem": len(metadane_plików),
            "liczba_plików_graficznych": sum(
                1 for m in metadane_plików if m.rozszerzenie != "pozostałe"
            ),
            "liczba_pozostałych_plików": sum(
                1 for m in metadane_plików if m.rozszerzenie == "pozostałe"
            ),
            "liczba_oryginałów": sum(
                1 for m in metadane_plików if m.flaga == "oryginał"
            ),
            "liczba_duplikatów": sum(
                1 for m in metadane_plików if m.flaga == "duplikat"
            ),
            "liczba_możliwych_duplikatów": sum(
                1 for m in metadane_plików if m.flaga == "możliwy duplikat"
            ),
            "liczba_grup_duplikatów": len(
                set(m.id_grupy.split("-")[0] for m in metadane_plików if m.id_grupy)
            ),
            "rozszerzenia": {},
            "narzędzia_analizy": stats_narzędzia,
            "liczba_plików_specjalistycznych": sum(
                1 for m in metadane_plików if m.rozszerzenie.lower() in FORMATY_OIIOTOOL
            ),
            "rozszerzenia_z_błędami": {},
        }

        # Statystyki według rozszerzeń
        for meta in metadane_plików:
            if meta.rozszerzenie not in statystyki["rozszerzenia"]:
                statystyki["rozszerzenia"][meta.rozszerzenie] = 0
            statystyki["rozszerzenia"][meta.rozszerzenie] += 1

            # Zbierz statystyki błędów według rozszerzeń
            if meta.narzędzie_analizy == "błąd":
                if meta.rozszerzenie not in statystyki["rozszerzenia_z_błędami"]:
                    statystyki["rozszerzenia_z_błędami"][meta.rozszerzenie] = 0
                statystyki["rozszerzenia_z_błędami"][meta.rozszerzenie] += 1

        return statystyki

    def zapisz_wyniki_do_json(
        self,
        wyniki: Dict[str, Any],
        ścieżka_wyjściowa: str,
        rozdziel_raporty: bool = True,
    ) -> Dict[str, str]:
        """
        Zapisuje wyniki analizy do plików JSON.

        Args:
            wyniki: Słownik z wynikami analizy.
            ścieżka_wyjściowa: Ścieżka do głównego pliku wyjściowego.
            rozdziel_raporty: Czy rozdzielać dane plików od statystyk.

        Returns:
            Dict[str, str]: Słownik z ścieżkami do zapisanych plików.
        """
        try:
            zapisane_pliki = {}

            if rozdziel_raporty:
                # Tworzymy ścieżki dla obu plików
                katalog = os.path.dirname(ścieżka_wyjściowa)
                nazwa_pliku = os.path.basename(ścieżka_wyjściowa)
                nazwa_bez_rozszerzenia = os.path.splitext(nazwa_pliku)[0]

                # Ścieżka do pliku z danymi plików
                pliki_ścieżka = os.path.join(
                    katalog, f"{nazwa_bez_rozszerzenia}_pliki.json"
                )

                # Ścieżka do pliku ze statystykami
                statystyki_ścieżka = os.path.join(
                    katalog, f"{nazwa_bez_rozszerzenia}_statystyki.json"
                )

                # Przygotowanie danych do zapisu
                dane_plików = {"pliki": wyniki.get("pliki", [])}

                dane_statystyk = {
                    "statystyki": wyniki.get("statystyki", {}),
                    "konfiguracja": wyniki.get("konfiguracja", {}),
                }

                # Zapisanie plików
                with open(pliki_ścieżka, "w", encoding="utf-8") as f:
                    json.dump(dane_plików, f, ensure_ascii=False, indent=2)
                zapisane_pliki["pliki"] = pliki_ścieżka

                with open(statystyki_ścieżka, "w", encoding="utf-8") as f:
                    json.dump(dane_statystyk, f, ensure_ascii=False, indent=2)
                zapisane_pliki["statystyki"] = statystyki_ścieżka

                # Zapisujemy także kompletny raport dla zgodności wstecznej
                with open(ścieżka_wyjściowa, "w", encoding="utf-8") as f:
                    json.dump(wyniki, f, ensure_ascii=False, indent=2)
                zapisane_pliki["kompletny"] = ścieżka_wyjściowa

                return zapisane_pliki
            else:
                # Stary sposób - wszystko w jednym pliku
                with open(ścieżka_wyjściowa, "w", encoding="utf-8") as f:
                    json.dump(wyniki, f, ensure_ascii=False, indent=2)
                zapisane_pliki["kompletny"] = ścieżka_wyjściowa
                return zapisane_pliki

        except Exception as e:
            logger.error(f"Błąd podczas zapisywania wyników do pliku JSON: {str(e)}")
            return {"błąd": str(e)}


# Funkcja pomocnicza do korzystania z biblioteki bez tworzenia instancji klasy
def przetwarzaj_folder_tekstur(
    ścieżka_folderu: str,
    ścieżka_wyjściowa: str = None,
    przeszukuj_podfoldery: bool = False,
    ścieżka_oiiotool: str = "oiiotool",
    callback_statusu=None,
    rozdziel_raporty: bool = True,
) -> Dict[str, Any]:
    """
    Funkcja pomocnicza do przetwarzania folderu z teksturami.

    Args:
        ścieżka_folderu: Ścieżka do folderu z plikami.
        ścieżka_wyjściowa: Opcjonalna ścieżka do pliku wyjściowego JSON.
        przeszukuj_podfoldery: Czy przeszukiwać również podfoldery.
        ścieżka_oiiotool: Ścieżka do narzędzia oiiotool.
        callback_statusu: Opcjonalna funkcja do raportowania postępu.
        rozdziel_raporty: Czy rozdzielić raporty na pliki i statystyki.

    Returns:
        Słownik z wynikami analizy.
    """
    # Sprawdzanie, czy folder istnieje
    if not os.path.isdir(ścieżka_folderu):
        raise ValueError(
            f"Podana ścieżka '{ścieżka_folderu}' nie jest folderem lub nie istnieje."
        )

    # Tworzenie i konfiguracja procesora
    procesor = TextureProcessor(ścieżka_oiiotool)

    if callback_statusu:
        procesor.ustaw_callback_statusu(callback_statusu)

    # Przetwarzanie folderu
    wyniki = procesor.przetwarzaj_folder(ścieżka_folderu, przeszukuj_podfoldery)

    # Zapisywanie wyników, jeśli podano ścieżkę wyjściową
    if ścieżka_wyjściowa:
        zapisane_pliki = procesor.zapisz_wyniki_do_json(
            wyniki, ścieżka_wyjściowa, rozdziel_raporty
        )
        # Dodajemy informacje o ścieżkach do zapisanych plików
        wyniki["ścieżki_raportów"] = zapisane_pliki

    return wyniki


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Narzędzie do przetwarzania tekstur")
    parser.add_argument("ścieżka_folderu", help="Ścieżka do folderu z teksturami")
    parser.add_argument(
        "-o",
        "--output",
        dest="ścieżka_wyjściowa",
        help="Ścieżka do pliku wyjściowego JSON",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        dest="przeszukuj_podfoldery",
        action="store_true",
        help="Przeszukuj podfoldery",
    )
    parser.add_argument(
        "--oiiotool",
        dest="ścieżka_oiiotool",
        default="oiiotool",
        help="Ścieżka do narzędzia oiiotool",
    )
    parser.add_argument(
        "--verbose", dest="verbose", action="store_true", help="Szczegółowe logowanie"
    )

    args = parser.parse_args()

    # Ustawienie poziomu logowania
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Prosta funkcja do wyświetlania postępu w konsoli
    def wyświetl_postęp(status):
        print(f"[{status.etap}] {status.postęp*100:.1f}%: {status.wiadomość}")

    # Domyślna ścieżka wyjściowa, jeśli nie podano
    if not args.ścieżka_wyjściowa:
        args.ścieżka_wyjściowa = os.path.join(
            os.path.dirname(args.ścieżka_folderu),
            f"wyniki_tekstur_{int(time.time())}.json",
        )

    # Przetwarzanie
    try:
        wyniki = przetwarzaj_folder_tekstur(
            args.ścieżka_folderu,
            args.ścieżka_wyjściowa,
            args.przeszukuj_podfoldery,
            args.ścieżka_oiiotool,
            wyświetl_postęp,
            args.rozdziel_raporty,
        )

        print(
            f"\nPrzetwarzanie zakończone. Znaleziono {wyniki['statystyki']['liczba_plików_graficznych']} plików graficznych."
        )

        # Dodatkowa informacja o przetwarzaniu specjalistycznych formatów
        if "konfiguracja" in wyniki and "oiiotool_dostępny" in wyniki["konfiguracja"]:
            if wyniki["konfiguracja"]["oiiotool_dostępny"]:
                print(
                    f"Narzędzie oiiotool było dostępne i użyte do analizy specjalistycznych formatów."
                )
                if "formaty_oiiotool" in wyniki["statystyki"]["narzędzia_analizy"]:
                    print(
                        f"Poprawnie przeanalizowane pliki specjalistyczne: {wyniki['statystyki']['narzędzia_analizy']['formaty_oiiotool']['poprawnie']}"
                    )
                    print(
                        f"Niepoprawnie przeanalizowane pliki specjalistyczne: {wyniki['statystyki']['narzędzia_analizy']['formaty_oiiotool']['niepoprawnie']}"
                    )
            else:
                print(
                    f"Narzędzie oiiotool nie było dostępne, niektóre specjalistyczne formaty mogły nie zostać przeanalizowane."
                )

        # Informacje o rozszerzeniach z błędami
        if (
            "rozszerzenia_z_błędami" in wyniki["statystyki"]
            and wyniki["statystyki"]["rozszerzenia_z_błędami"]
        ):
            print("\nRozszerzenia z błędami:")
            for rozszerzenie, liczba in wyniki["statystyki"][
                "rozszerzenia_z_błędami"
            ].items():
                print(f"  {rozszerzenie}: {liczba} plików")

        print(f"Wyniki zapisano do: {args.ścieżka_wyjściowa}")
        print(
            f"Szczegółowe logi znajdują się w pliku: texture_processor.log oraz logs/oiiotool_log.txt"
        )

    except Exception as e:
        logger.exception(f"Wystąpił błąd: {str(e)}")
        print(f"Wystąpił błąd: {str(e)}")
        print("Szczegółowe informacje znajdują się w logu: texture_processor.log")
        exit(1)
