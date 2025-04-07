#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Texture Worker - pośrednik między głównym programem a biblioteką przetwarzania tekstur
"""

import json
import logging
import os
import sys
import threading
import time
from typing import Any, Callable, Dict, Optional

from core import texture_processor

logger = logging.getLogger(__name__)


class TextureWorker:
    """
    Klasa zarządzająca przetwarzaniem tekstur i komunikacją z głównym programem.
    """

    def __init__(self):
        """Inicjalizacja klasy worker."""
        self.postęp_globalny = 0.0
        self.etap_obecny = ""
        self.wiadomość_obecna = ""
        self.wyniki = None
        self.callback_aktualizacji = None
        self._wątek_przetwarzania = None
        self._przetwarzanie_aktywne = False
        self._callback_ukończenia = None

    def ustaw_callback_aktualizacji(self, callback):
        """
        Ustawia funkcję callback do aktualizacji statusu.

        Args:
            callback: Funkcja przyjmująca (etap, postęp, wiadomość).
        """
        self.callback_aktualizacji = callback
        # Prześlij callback również do procesora tekstur
        self._obsługa_aktualizacji_statusu_wrapper = (
            lambda status: self._obsługa_aktualizacji_statusu(status)
        )

    def _obsługa_aktualizacji_statusu(self, status):
        """
        Obsługuje aktualizacje statusu od procesora tekstur.

        Args:
            status: Obiekt StatusPostępu z informacjami o postępie.
        """
        try:
            self.etap_obecny = status.etap
            self.postęp_globalny = status.postęp
            self.wiadomość_obecna = status.wiadomość

            kontynuuj = True
            if self.callback_aktualizacji:
                # Logowanie dla debugowania
                logger.debug(
                    f"Wywołanie callbacku: {status.etap}, {status.postęp}, {status.wiadomość}"
                )

                # Wywołaj callback i sprawdź, czy zwrócił wartość
                wynik = self.callback_aktualizacji(
                    status.etap, status.postęp, status.wiadomość
                )

                # Logowanie wyniku
                logger.debug(f"Wynik callbacku: {wynik}")

                # Jeśli callback zwrócił False, to anuluj operację
                if wynik is False:
                    kontynuuj = False
            else:
                # Domyślne wyjście na konsolę
                logger.debug(
                    f"[{status.etap}] {status.postęp*100:.1f}%: {status.wiadomość}"
                )

            return kontynuuj
        except Exception as e:
            print(f"BŁĄD w _obsługa_aktualizacji_statusu: {str(e)}")
            # Zwracamy True, żeby nie przerywać analizy
            return True

    def przetwarzaj_folder(
        self,
        ścieżka_folderu: str,
        przeszukuj_podfoldery: bool = False,
        ścieżka_wyjściowa: Optional[str] = None,
        ścieżka_oiiotool: str = "oiiotool",
    ) -> Dict[str, Any]:
        """
        Przetwarza folder z teksturami.

        Args:
            ścieżka_folderu: Ścieżka do folderu z plikami.
            przeszukuj_podfoldery: Czy przeszukiwać również podfoldery.
            ścieżka_wyjściowa: Opcjonalna ścieżka do pliku wyjściowego JSON (tylko dla statystyk).
            ścieżka_oiiotool: Ścieżka do narzędzia oiiotool.

        Returns:
            Słownik z wynikami analizy.
        """
        # Resetuj stan
        self.postęp_globalny = 0.0
        self.etap_obecny = "inicjalizacja"
        self.wiadomość_obecna = "Inicjalizacja przetwarzania tekstur..."

        # Wrapper dla obsługi anulowania operacji
        canceled = [False]

        def callback_z_obsługą_anulowania(status):
            try:
                result = self._obsługa_aktualizacji_statusu(status)
                if result is False:
                    canceled[0] = True
                    logger.debug("Operacja anulowana przez użytkownika")
                return result
            except Exception as e:
                logger.error(f"Błąd w callback_z_obsługą_anulowania: {str(e)}")
                return True

        try:
            # Wywołaj funkcję przetwarzania z procesora
            self.wyniki = texture_processor.przetwarzaj_folder_tekstur(
                ścieżka_folderu,
                ścieżka_wyjściowa,  # Może być None - wtedy nie zapisujemy raportu plików
                przeszukuj_podfoldery,
                ścieżka_oiiotool,
                callback_z_obsługą_anulowania,
            )

            # Jeśli operacja została anulowana
            if canceled[0]:
                self.etap_obecny = "anulowano"
                self.wiadomość_obecna = "Operacja została anulowana przez użytkownika"
                return {
                    "sukces": False,
                    "komunikat": "Operacja anulowana przez użytkownika",
                }

            return self.wyniki

        except AttributeError as e:
            if "GeMaxThreadCount" in str(e):
                self.etap_obecny = "błąd"
                self.wiadomość_obecna = (
                    "Błąd modułu threading. Używam alternatywnej metody."
                )

                if self.callback_aktualizacji:
                    self.callback_aktualizacji(
                        self.etap_obecny, self.postęp_globalny, self.wiadomość_obecna
                    )

                return {
                    "sukces": False,
                    "komunikat": "Błąd modułu threading. Spróbuj ponownie.",
                }
            else:
                raise
        except Exception as e:
            self.etap_obecny = "błąd"
            self.wiadomość_obecna = f"Wystąpił błąd: {str(e)}"

            if self.callback_aktualizacji:
                self.callback_aktualizacji(
                    self.etap_obecny, self.postęp_globalny, self.wiadomość_obecna
                )

            raise

    def pobierz_obecny_status(self) -> Dict[str, Any]:
        """
        Pobiera obecny status przetwarzania.

        Returns:
            Słownik ze statusem przetwarzania.
        """
        return {
            "etap": self.etap_obecny,
            "postęp": self.postęp_globalny,
            "wiadomość": self.wiadomość_obecna,
        }

    def pobierz_wyniki(self) -> Dict[str, Any]:
        """
        Pobiera wyniki przetwarzania.

        Returns:
            Słownik z wynikami analizy lub None, jeśli nie zakończono przetwarzania.
        """
        return self.wyniki

    def przetwarzaj_folder_async(
        self,
        ścieżka_folderu: str,
        callback_ukończenia: Optional[Callable[[Dict[str, Any]], None]] = None,
        przeszukuj_podfoldery: bool = False,
        ścieżka_wyjściowa: Optional[str] = None,
        ścieżka_oiiotool: str = "oiiotool",
    ) -> bool:
        """
        Przetwarza folder z teksturami asynchronicznie w osobnym wątku.

        Args:
            ścieżka_folderu: Ścieżka do folderu z plikami.
            callback_ukończenia: Funkcja do wywołania po zakończeniu przetwarzania.
            przeszukuj_podfoldery: Czy przeszukiwać również podfoldery.
            ścieżka_wyjściowa: Opcjonalna ścieżka do pliku wyjściowego JSON.
            ścieżka_oiiotool: Ścieżka do narzędzia oiiotool.

        Returns:
            bool: True jeśli uruchomiono przetwarzanie, False w przypadku błędu.
        """
        if self._przetwarzanie_aktywne:
            logger.warning("Przetwarzanie jest już aktywne")
            return False

        self._callback_ukończenia = callback_ukończenia
        self._przetwarzanie_aktywne = True

        def process_thread():
            try:
                wyniki = self.przetwarzaj_folder(
                    ścieżka_folderu,
                    przeszukuj_podfoldery,
                    ścieżka_wyjściowa,
                    ścieżka_oiiotool,
                )

                # Powiadom o zakończeniu w głównym wątku
                if self._callback_ukończenia:
                    import c4d

                    c4d.CallAsyncFunction(lambda: self._callback_ukończenia(wyniki))

            except Exception as e:
                logger.error(f"Błąd w wątku przetwarzania: {str(e)}")
                if self._callback_ukończenia:
                    import c4d

                    c4d.CallAsyncFunction(
                        lambda: self._callback_ukończenia({"błąd": str(e)})
                    )
            finally:
                self._przetwarzanie_aktywne = False

        # Uruchom wątek przetwarzania
        self._wątek_przetwarzania = threading.Thread(target=process_thread, daemon=True)
        self._wątek_przetwarzania.start()

        return True

    def czy_przetwarzanie_aktywne(self) -> bool:
        """
        Sprawdza, czy przetwarzanie jest aktywne.

        Returns:
            bool: True jeśli przetwarzanie jest aktywne, False w przeciwnym razie.
        """
        return self._przetwarzanie_aktywne

    def anuluj_przetwarzanie(self) -> bool:
        """
        Anuluje aktywne przetwarzanie.

        Returns:
            bool: True jeśli anulowano przetwarzanie, False w przeciwnym razie.
        """
        if not self._przetwarzanie_aktywne:
            return False

        self._przetwarzanie_aktywne = False
        if self._wątek_przetwarzania and self._wątek_przetwarzania.is_alive():
            self._wątek_przetwarzania.join(timeout=1.0)

        return True


def main():
    """
    Główna funkcja do uruchomienia workera z linii poleceń.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Worker do przetwarzania tekstur")
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

    args = parser.parse_args()

    # Tworzenie workera
    worker = TextureWorker()

    # Przetwarzanie
    try:
        wyniki = worker.przetwarzaj_folder(
            args.ścieżka_folderu,
            args.przeszukuj_podfoldery,
            args.ścieżka_wyjściowa,
            args.ścieżka_oiiotool,
        )

        print(
            f"\nPrzetwarzanie zakończone. Znaleziono {wyniki['statystyki']['liczba_plików_graficznych']} plików graficznych."
        )
        print(f"Wyniki zapisano do: {args.ścieżka_wyjściowa}")

        return 0

    except Exception as e:
        print(f"Wystąpił krytyczny błąd: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
