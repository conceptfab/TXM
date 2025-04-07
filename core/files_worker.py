"""
filesWorker

Moduł do obsługi operacji na plikach często używanych
w skryptach Cinema 4D. Zawiera funkcje do zarządzania
ścieżkami, weryfikacji plików i obsługi ustawień.
"""

import json
import os
import shutil
from typing import Dict

import c4d
from c4d import storage

from .logger import Logger

# Inicjalizacja loggera
logger = Logger()


def get_folder_separator() -> str:
    """
    Zwraca odpowiedni separator folderów dla bieżącego
    systemu operacyjnego.

    Zwraca:
        str: Znak separatora folderów ('\\' dla Windows,
             '/' dla Mac/Linux)
    """
    return os.path.sep


def get_c4d_path(path_type=c4d.C4D_PATH_PREFS):
    """
    Pobiera ścieżkę Cinema 4D określonego typu.

    Argumenty:
        path_type (int): Typ ścieżki C4D do pobrania
                        (domyślnie C4D_PATH_PREFS)
                        - C4D_PATH_PREFS: Katalog preferencji Cinema 4D
                        - C4D_PATH_RESOURCE: Katalog zasobów Cinema 4D
                        - C4D_PATH_LIBRARY: Katalog wbudowanej biblioteki
                        - C4D_PATH_LIBRARY_USER: Katalog biblioteki użytkownika
                        - C4D_PATH_DESKTOP: Katalog pulpitu systemu
                        - C4D_PATH_HOME: Katalog domowy systemu
                        - C4D_PATH_STARTUPWRITE: Zapisywalny katalog startowy
                        - C4D_PATH_MYDOCUMENTS: Katalog dokumentów użytkownika
                        - C4D_PATH_APPLICATION: Katalog aplikacji systemu

    Zwraca:
        str: Ścieżka do żądanego katalogu lub None,
             jeśli ścieżka nie istnieje
    """
    path = storage.GeGetC4DPath(path_type)
    return path if os.path.exists(path) else None


def ensure_directory_exists(directory_path: str) -> bool:
    """
    Upewnia się, że katalog istnieje, tworząc go
    w razie potrzeby.

    Args:
        directory_path (str): Ścieżka do katalogu

    Returns:
        bool: True jeśli katalog istnieje lub został
              utworzony, False w przypadku błędu
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        return True
    except OSError as e:
        error_msg = "Błąd tworzenia katalogu " f"{directory_path}: " f"{e}"
        logger.error(error_msg)
        return False


def get_project_texture_path():
    """
    Znajduje ścieżkę dokumentu i folder tekstur dla
    bieżącego projektu.

    Zwraca:
        tuple: (doc_path, texture_path) lub (None, None),
               jeśli brak aktywnego dokumentu
    """
    doc = c4d.documents.GetActiveDocument()
    if doc is None:
        return None, None

    doc_path = doc.GetDocumentPath()
    if not doc_path:
        return None, None

    tex_path = os.path.join(doc_path, "tex")
    return doc_path, tex_path


def create_settings_file(file_path: str, default_settings: Dict) -> bool:
    """
    Tworzy plik ustawień z domyślnymi wartościami.

    Args:
        file_path (str): Ścieżka do pliku ustawień
        default_settings (dict): Domyślne ustawienia

    Returns:
        bool: True jeśli plik został utworzony,
              False w przypadku błędu
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(default_settings, f, indent=4, ensure_ascii=False)
        return True
    except OSError as e:
        error_msg = f"Błąd tworzenia pliku ustawień {file_path}: " f"{e}"
        logger.error(error_msg)
        return False


def load_settings(file_path: str) -> Dict:
    """
    Wczytuje ustawienia z pliku JSON.

    Args:
        file_path (str): Ścieżka do pliku ustawień

    Returns:
        dict: Wczytane ustawienia lub pusty słownik
              w przypadku błędu
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except OSError as e:
        error_msg = f"Błąd wczytywania ustawień z {file_path}: " f"{e}"
        logger.error(error_msg)
        return {}


def save_settings(file_path: str, settings: Dict) -> bool:
    """
    Zapisuje ustawienia do pliku JSON.

    Args:
        file_path (str): Ścieżka do pliku ustawień
        settings (dict): Ustawienia do zapisania

    Returns:
        bool: True jeśli ustawienia zostały zapisane,
              False w przypadku błędu
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        return True
    except OSError as e:
        error_msg = f"Błąd zapisywania ustawień do {file_path}: " f"{e}"
        logger.error(error_msg)
        return False


def copy_file(source_path: str, destination_path: str) -> bool:
    """
    Kopiuje plik z jednej lokalizacji do drugiej.

    Args:
        source_path (str): Ścieżka do pliku źródłowego
        destination_path (str): Ścieżka docelowa

    Returns:
        bool: True jeśli plik został skopiowany,
              False w przypadku błędu
    """
    try:
        shutil.copy2(source_path, destination_path)
        return True
    except OSError as e:
        error_msg = (
            "Błąd kopiowania pliku z " f"{source_path} do " f"{destination_path}: {e}"
        )
        logger.error(error_msg)
        return False


def generate_unique_filename(filename, folder_path):
    """
    Generuje unikalną nazwę pliku, jeśli plik już
    istnieje.

    Argumenty:
        filename (str): Oryginalna nazwa pliku
        folder_path (str): Ścieżka do folderu

    Zwraca:
        str: Unikalna nazwa pliku
    """
    base_name, extension = os.path.splitext(filename)

    # Sprawdź, czy nazwa podstawowa już ma licznik
    if "_" in base_name:
        parts = base_name.split("_")
        last_part = parts[-1]
        if last_part.isdigit():
            counter = int(last_part) + 1
            base_name = "_".join(parts[:-1])
        else:
            counter = 1
    else:
        counter = 1

    # Wygeneruj unikalną nazwę pliku
    while True:
        new_filename = f"{base_name}_{counter}{extension}"
        new_path = os.path.join(folder_path, new_filename)
        if not os.path.exists(new_path):
            return new_filename
        counter += 1


def show_in_explorer(path):
    """
    Otwiera eksplorator plików w określonej ścieżce.

    Argumenty:
        path (str): Ścieżka do pokazania w eksploratorze

    Zwraca:
        bool: True, jeśli operacja powiodła się,
              False w przeciwnym razie
    """
    if not os.path.exists(path):
        return False

    try:
        storage.ShowInFinder(path, True)
        return True
    except Exception as e:
        logger.error(f"Błąd podczas otwierania eksploratora: {e}")
        return False


def ensure_reports_directory(base_path=None):
    """
    Upewnia się, że katalog raportów istnieje.

    Args:
        base_path (str): Opcjonalna bazowa ścieżka. Jeśli nie podano,
                        używa katalogu aktywnego dokumentu lub katalogu projektu.

    Returns:
        str: Ścieżka do katalogu raportów
    """
    if not base_path:
        doc_path, _ = get_project_texture_path()
        if doc_path:
            base_path = doc_path
        else:
            # Fallback do katalogu projektu
            import os

            script_dir = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.dirname(script_dir)

    reports_dir = os.path.join(base_path, "raports")
    ensure_directory_exists(reports_dir)
    return reports_dir


def get_files_by_extension(directory, extensions=None, include_directories=False):
    """
    Pobiera listę plików w katalogu z określonymi
    rozszerzeniami.

    Argumenty:
        directory (str): Katalog do przeszukania
        extensions (list): Lista rozszerzeń do filtrowania
                          (np. ['.jpg', '.png'])
                          Jeśli None, wszystkie pliki są
                          zwracane
        include_directories (bool): Czy uwzględniać
                                   katalogi w wynikach

    Zwraca:
        list: Lista ścieżek plików, które pasują do
              kryteriów
    """
    if not os.path.exists(directory) or not os.path.isdir(directory):
        return []

    results = []

    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)

        if os.path.isdir(item_path):
            if include_directories:
                results.append(item_path)
        else:
            file_ext = os.path.splitext(item)[1].lower()
            if extensions is None or file_ext in extensions:
                results.append(item_path)

    return results
