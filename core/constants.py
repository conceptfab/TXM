import c4d
import c4d.gui


class UIConstants:
    APP_NAME = "TXM"
    APP_VERSION = "0.43"
    WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"

    # ID elementów interfejsu
    ID_SELECTION = 1
    ID_TEXTURE_NAME = 2
    ID_SZEROKOSC = 3
    ID_WYSOKOSC = 4
    ID_GLEBIA_BITOWA = 5
    ID_PROFIL_KOLORU = 6
    ID_ROZMIAR_MB = 7
    ID_KANAL_ALPHA = 8
    ID_FLAGA = 9
    ID_DATA_UTWORZENIA = 10
    ID_DATA_MODYFIKACJI = 11
    ID_HASH = 12
    ID_METADATA = 13
    ID_FULL_PATH = 14
    BTN_PROCESS_SELECTED = 15
    STATUS_SELECTION_COUNT = 16
    ID_FILE_SIZE = 17
    STATUS_TOTAL_SIZE = 18
    ID_CALCULATION = 19
    STATUS_BAR_TEXT = 20  # Nowy identyfikator dla tekstu statusu

    # Dodajemy identyfikatory dla nowych kolumn
    ID_COLUMN_A5 = 10
    ID_COLUMN_A6 = 11
    ID_COLUMN_A7 = 12
    ID_COLUMN_A8 = 13
    ID_COLUMN_A9 = 14
    ID_COLUMN_A10 = 15
    ID_COLUMN_A11 = 16

    ACTION_BUTTONS_GROUP = 100
    BTN_IMPORT = 101
    BTN_EXPORT = 102
    BTN_REFRESH = 103
    BTN_CLEAR = 104

    # Nowy przycisk do obsługi dialogu postępu
    PROGRESS_BTN = 105

    TEXTURE_LOAD_GROUP = 200
    TEXTURE_ACTIONS_GROUP = 201
    TEXTURE_OPTIONS_GROUP = 202
    BTN_LOAD_TEXTURES = 203
    BTN_BROWSE = 204

    SPACER_HEADER = 205
    SPACER_FOOTER = 206
    SPACER_LEFT_MARGIN = 207
    SPACER_RIGHT_MARGIN = 208

    TEXTURE_LIST_VIEW = 99

    # Dodajemy stałe dla sortowania
    SORT_ASCENDING = 0
    SORT_DESCENDING = 1

    # Flagi dla TreeView
    TREEVIEW_FLAGS = {
        "border": c4d.TREEVIEW_BORDER,
        "header": c4d.TREEVIEW_HAS_HEADER,
        "hide_lines": c4d.TREEVIEW_HIDE_LINES,
        "move_column": c4d.TREEVIEW_MOVE_COLUMN,
        "resize_header": c4d.TREEVIEW_RESIZE_HEADER,
        "fixed_layout": c4d.TREEVIEW_FIXED_LAYOUT,
        "alternate_bg": c4d.TREEVIEW_ALTERNATE_BG,
        "cursor_keys": c4d.TREEVIEW_CURSORKEYS,
        "no_enter_rename": c4d.TREEVIEW_NOENTERRENAME,
    }

    # Wymiary interfejsu
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    SPACING_BUTTONS = 16
    SPACING_BOTTOM = 27
    MARGIN_GROUP = 5

    # Dialog postępu
    PROGRESS_DIALOG_WIDTH = 400
    PROGRESS_DIALOG_HEIGHT = 150

    # Stałe dla statusu
    STATUS_READY = "Ready"
    STATUS_LOADING = "Loading..."
    STATUS_ERROR = "Error"
    STATUS_PROCESSING = "Processing..."


# Stałe globalne dla układu interfejsu
GROUP_V_CENTER = 1000
GROUP_H_CENTER = 1001
BUTTON_CENTERED = 2000
SPACER_TOP = 1002
SPACER_BOTTOM = 1003
SPACER_LEFT = 1004
SPACER_RIGHT = 1005
