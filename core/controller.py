from . import files_worker
from .files_analyzer import analyze_c4d_textures
from .logger import Logger

# Inicjalizacja loggera
logger = Logger()


def status():
    """
    Funkcja pomocnicza na poziomie modułu,
    sprawdza status folderu tex.
    """
    controller = Controller()
    return controller.status()


def analyze_textures():
    """
    Funkcja pomocnicza na poziomie modułu,
    analizuje folder tekstur otwartego dokumentu.
    """
    controller = Controller()
    return controller.analyze_textures()


class Controller:
    """
    Klasa kontrolera do zarządzania operacjami
    na plikach w Cinema 4D.
    """

    def __init__(self):
        """
        Inicjalizacja kontrolera.
        """
        pass

    def status(self):
        """
        Sprawdza czy istnieje folder tex w katalogu
        projektu Cinema 4D.

        Zwraca:
            str: Status sprawdzenia - "OK" jeśli folder istnieje,
                 "NO_TEX_FOLDER" jeśli nie istnieje,
                 "NO_DOCUMENT" jeśli nie ma aktywnego dokumentu
        """
        doc_path, tex_path = files_worker.get_project_texture_path()

        if doc_path is None:
            logger.debug("Brak aktywnego dokumentu C4D")
            return "Brak aktywnego dokumentu C4D"

        if files_worker.ensure_directory_exists(tex_path):
            logger.debug("Znaleziono folder tekstur")
            return "Znaleziono folder tekstur"
        else:
            logger.debug("Nie znaleziono folderu tekstur")
            return "Nie znaleziono folderu tekstur"

    def analyze_textures(self):
        """
        Analizuje folder tekstur aktualnie otwartego dokumentu.

        Zwraca:
            str: Wynik analizy folderu tekstur
        """
        # Pobierz ścieżkę do folderu tekstur
        doc_path, tex_path = files_worker.get_project_texture_path()

        if doc_path is None:
            logger.debug("Brak aktywnego dokumentu C4D")
            return "Brak aktywnego dokumentu C4D"

        if not files_worker.ensure_directory_exists(tex_path):
            logger.debug("Nie znaleziono folderu tekstur")
            return "Nie znaleziono folderu tekstur"

        try:
            # Importuj analizę tekstur
            from .texture_runner import analizuj_folder_tekstur

            # Uruchom analizę tekstur
            logger.debug(f"Uruchamiam analizę folderu tekstur: {tex_path}")
            wyniki = analizuj_folder_tekstur(tex_path, False)

            if wyniki.get("sukces", False):
                raport = wyniki.get("ścieżka_raportu", "")
                logger.debug(f"Analiza zakończona pomyślnie, raport: {raport}")

                # Wyprowadź informację o liczbie znalezionych plików
                if "statystyki" in wyniki:
                    liczba_tekstur = wyniki["statystyki"].get(
                        "liczba_plików_graficznych", 0
                    )
                    return (
                        f"Znaleziono {liczba_tekstur} plików tekstur. Raport zapisano."
                    )
                else:
                    return "Analiza zakończona pomyślnie. Raport zapisano."
            else:
                logger.error(
                    f"Błąd analizy: {wyniki.get('komunikat', 'Nieznany błąd')}"
                )
                return f"Błąd analizy: {wyniki.get('komunikat', 'Nieznany błąd')}"

        except Exception as e:
            logger.error(f"Błąd podczas analizy tekstur: {str(e)}")
            return f"Błąd analizy: {str(e)}"


if __name__ == "__main__":
    logger.debug(status())
