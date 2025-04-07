#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Texture Runner - łącznik między TXM a biblioteką przetwarzania tekstur.
Dostosowany do działania w środowisku Cinema 4D.
"""

import argparse
import datetime
import json
import os
import sys

# Dodawanie ścieżki projektu do sys.path
KATALOG_PROGRAMU = os.path.dirname(os.path.abspath(__file__))
KATALOG_PROJEKTU = os.path.dirname(KATALOG_PROGRAMU)
if KATALOG_PROJEKTU not in sys.path:
    sys.path.append(KATALOG_PROJEKTU)

from core.logger import Logger

# Inicjalizacja loggera
logger = Logger()

# Teraz importujemy TextureWorker - po dodaniu ścieżek
try:  # Najpierw spróbuj zaimportować z katalogu projektu
    from core import files_worker
    from core.texture_worker import TextureWorker

    logger.debug("Zaimportowano TextureWorker z pakietu core")
except ImportError as e:
    logger.error(f"Nie można zaimportować TextureWorker: {str(e)}")
    raise


# Funkcja do ustalania folderu raportów
def get_raport_folder():
    """
    Zwraca folder do zapisywania raportów.
    Jeśli dokument C4D jest aktywny, używa folderu dokumentu,
    w przeciwnym razie używa folderu 'raports' w katalogu projektu.
    """
    doc_path, _ = files_worker.get_project_texture_path()

    if doc_path and os.path.exists(doc_path):
        logger.debug(f"Używam folderu dokumentu do zapisania raportu: {doc_path}")
        return doc_path
    else:
        fallback_path = os.path.join(KATALOG_PROJEKTU, "raports")
        logger.warning(
            f"Brak aktywnego dokumentu, używam folderu fallback: {fallback_path}"
        )
        return fallback_path


# Ścieżka do oiiotool.exe - bezpośrednio w katalogu oiiotool
ŚCIEŻKA_OIIOTOOL = os.path.join(KATALOG_PROGRAMU, "oiiotool", "oiiotool.exe")


def aktualizacja_statusu(etap, postęp, wiadomość):
    """
    Wyświetla status przetwarzania.

    Args:
        etap: Nazwa etapu przetwarzania.
        postęp: Wartość od 0.0 do 1.0 oznaczająca postęp.
        wiadomość: Dodatkowa informacja tekstowa.
    """
    logger.debug(f"[{etap}] {postęp*100:.1f}%: {wiadomość}")
    return True  # Dodana wartość zwracana, aby kontynuować przetwarzanie


def analizuj_folder_tekstur(
    ścieżka_folderu, przeszukuj_podfoldery=False, callback_statusu=None
):
    """
    Funkcja analizująca tekstury w podanym folderze.

    Args:
        ścieżka_folderu: Ścieżka do folderu z teksturami
        przeszukuj_podfoldery: Czy przeszukiwać również podfoldery
        callback_statusu: Opcjonalny callback do raportowania postępu

    Returns:
        dict: Słownik z wynikami analizy lub informacją o błędzie
    """
    # Sprawdź czy folder istnieje
    if not os.path.isdir(ścieżka_folderu):
        logger.error(f"Podany folder nie istnieje: {ścieżka_folderu}")
        return {
            "sukces": False,
            "komunikat": f"Podany folder nie istnieje: {ścieżka_folderu}",
        }

    # Ustalamy folder do zapisania raportu
    folder_raportów = get_raport_folder()

    # Tworzymy folder raportów, jeśli nie istnieje
    if not os.path.exists(folder_raportów):
        os.makedirs(folder_raportów)
        logger.debug(f"Utworzono folder raportów: {folder_raportów}")

    # Nazwa pliku raportu z datą - tylko dla statystyk
    nazwa_pliku = (
        f"statystyki_tekstur_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    # Pełna ścieżka do pliku wyjściowego
    ścieżka_wyjściowa = os.path.join(folder_raportów, nazwa_pliku)

    # Inicjalizacja workera
    logger.debug("Inicjalizacja TextureWorker")
    try:
        worker = TextureWorker()

        # Przekazujemy callback_statusu, jeśli został podany
        if callback_statusu:
            # Adapter do przekształcania wywołań między różnymi formatami callbacków
            def adapter_callback(etap, postep, wiadomosc):
                """Adapter dopasowujący format wywołania callbacku."""
                try:
                    logger.debug(
                        f"Otrzymano status: etap={etap}, postęp={postep}, wiadomość={wiadomosc}"
                    )

                    # Przekazujemy dane do oryginalnego callbacku
                    if callback_statusu is not None:
                        return callback_statusu(etap, postep, wiadomosc)
                    else:
                        # Jeśli nie ma callbacku, wyświetl komunikat w logu
                        logger.debug(f"[{etap}] {postep*100:.1f}%: {wiadomosc}")
                        return True
                except Exception as e:
                    logger.error(f"Błąd w adapter_callback: {str(e)}")
                    # Zwracamy True, żeby nie przerywać analizy
                    return True

            worker.ustaw_callback_aktualizacji(adapter_callback)
        else:
            worker.ustaw_callback_aktualizacji(aktualizacja_statusu)

    except Exception as e:
        logger.error(f"Błąd inicjalizacji TextureWorker: {str(e)}")
        return {
            "sukces": False,
            "komunikat": f"Błąd inicjalizacji TextureWorker: {str(e)}",
        }

    # Sprawdź czy oiiotool istnieje
    if os.path.isfile(ŚCIEŻKA_OIIOTOOL):
        logger.debug(f"Znaleziono oiiotool: {ŚCIEŻKA_OIIOTOOL}")
    else:
        logger.warning(f"Nie znaleziono oiiotool pod ścieżką: {ŚCIEŻKA_OIIOTOOL}")
        logger.warning(
            "Metadane dla specjalistycznych formatów tekstur (EXR, HDR, TX) mogą być niedostępne."
        )

    try:
        logger.debug(f"Rozpoczynam przetwarzanie folderu: {ścieżka_folderu}")
        logger.debug(
            f"Przeszukiwanie podfolderów: {'Tak' if przeszukuj_podfoldery else 'Nie'}"
        )
        logger.debug(f"Statystyki zostaną zapisane do: {ścieżka_wyjściowa}")

        # Przetwarzanie folderu - bez generowania pełnego raportu plików
        wyniki = worker.przetwarzaj_folder(
            ścieżka_folderu, przeszukuj_podfoldery, None, ŚCIEŻKA_OIIOTOOL
        )

        # Zapisujemy tylko statystyki
        if "statystyki" in wyniki:
            with open(ścieżka_wyjściowa, "w", encoding="utf-8") as f:
                json.dump(wyniki["statystyki"], f, indent=4, ensure_ascii=False)
                logger.debug(f"Zapisano statystyki do: {ścieżka_wyjściowa}")

        # Dodaj pola informacyjne
        wyniki["sukces"] = True
        wyniki["ścieżka_statystyk"] = ścieżka_wyjściowa

        logger.debug("Przetwarzanie zakończone pomyślnie!")
        logger.debug(f"Statystyki zapisano do: {ścieżka_wyjściowa}")

        return wyniki

    except Exception as e:
        logger.error(f"Błąd podczas przetwarzania tekstur: {str(e)}")
        return {"sukces": False, "komunikat": f"Błąd podczas przetwarzania: {str(e)}"}


def main():
    """
    Główna funkcja skryptu, wywoływana przy uruchomieniu z wiersza poleceń
    lub z Cinema 4D.
    """
    parser = argparse.ArgumentParser(description="Texture Runner dla TXM")
    parser.add_argument(
        "ścieżka_folderu", nargs="?", help="Ścieżka do folderu z teksturami"
    )
    parser.add_argument(
        "-r",
        "--recursive",
        dest="przeszukuj_podfoldery",
        action="store_true",
        help="Przeszukuj podfoldery",
    )

    args = parser.parse_args()

    # Jeśli nie podano ścieżki jako argument, próbujemy wykryć folder tekstur aktywnego dokumentu C4D
    if not args.ścieżka_folderu:
        _, tex_path = files_worker.get_project_texture_path()

        if tex_path and os.path.exists(tex_path):
            logger.debug(f"Wykryto folder tekstur aktywnego dokumentu: {tex_path}")
            args.ścieżka_folderu = tex_path
        else:
            logger.error(
                "Nie podano ścieżki do folderu tekstur i nie znaleziono aktywnego dokumentu"
            )
            return 1

    # Analiza tekstur
    wyniki = analizuj_folder_tekstur(args.ścieżka_folderu, args.przeszukuj_podfoldery)

    if wyniki.get("sukces", False):
        return 0
    else:
        logger.error(wyniki.get("komunikat", "Nieznany błąd"))
        return 1


if __name__ == "__main__":
    sys.exit(main())
