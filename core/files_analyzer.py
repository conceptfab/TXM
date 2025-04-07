#!/usr/bin/env python3
import os

from . import files_worker
from .logger import Logger

# Inicjalizacja loggera
logger = Logger()


def analyze_directory(dir_path):
    """
    Analizuje zawartość katalogu pod kątem plików tekstur.

    Args:
        dir_path: Ścieżka do analizowanego katalogu

    Returns:
        str: Opis zawartości katalogu
    """
    if not os.path.exists(dir_path):
        return f"Katalog {dir_path} " "nie istnieje"

    files = os.listdir(dir_path)
    image_files = [
        f for f in files if f.lower().endswith((".jpg", ".png", ".tif", ".tga"))
    ]

    return f"Znaleziono {len(image_files)} " f"plików tekstur w katalogu {dir_path}"


def run_analysis(dir_path):
    """
    Funkcja uruchamia analizę katalogu przy użyciu funkcji analyze_directory.

    Args:
        dir_path (str): Ścieżka do katalogu do przeanalizowania

    Returns:
        str: Wynik analizy katalogu
    """
    # Usuwam logowanie, żeby nie duplikować informacji w konsoli
    result = analyze_directory(dir_path)
    return result


def analyze_c4d_textures():
    """
    Analizuje tekstury projektu C4D w folderze tex.

    Zwraca:
        str: Informacja o stanie analizy z liczbą znalezionych plików
    """
    try:
        # Pobierz ścieżkę do folderu tekstur
        doc_path, tex_path = files_worker.get_project_texture_path()

        if not doc_path:
            return "Brak aktywnego dokumentu C4D"

        if not files_worker.ensure_directory_exists(tex_path):
            return "Nie znaleziono folderu tekstur"

        # Użyj istniejącej funkcji do analizy katalogu
        result = analyze_directory(tex_path)

        return result
    except Exception as e:
        logger.error(f"Błąd podczas analizy tekstur: {str(e)}")
        return f"Błąd analizy: {str(e)}"


# Przykład użycia:
# result = analyze_directory("ścieżka/do/folderu")
# logger.debug(result)
#
# Lub użycie nowej funkcji:
# run_analysis("ścieżka/do/folderu")
