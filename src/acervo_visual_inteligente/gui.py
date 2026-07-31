import importlib.util
import types
import ctypes
import os
import sys
import io
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk, ImageDraw, ImageOps

try:
    from acervo_visual_inteligente import __version__
except Exception:
    __version__ = "2.0.0"


APP_VERSION = __version__
APP_USER_MODEL_ID = "EdTech.AcervoImagens"
UI_FONT = "MS Sans Serif"
PIXEL_FONT = "Press Start 2P"
CURRENT_THEME_NAME = "dark"

THEMES = {
    "light": {
        "bg": "#c0c0c0",
        "panel": "#d8d8d8",
        "text": "#000000",
        "subtext": "#333333",
        "muted": "#777777",
        "button_bg": "#dcdcdc",
        "button_active": "#eeeeee",
        "entry_bg": "#ffffff",
        "entry_fg": "#000000",
        "log_bg": "#ffffff",
        "log_fg": "#000000",
        "accent": "#8b35f6",
        "progress": "#8b35f6",
        "progress_trough": "#d8d8d8",
    },
    "dark": {
        "bg": "#202020",
        "panel": "#303030",
        "text": "#f2f2f2",
        "subtext": "#d8d8d8",
        "muted": "#9a9a9a",
        "button_bg": "#3a3a3a",
        "button_active": "#4a4a4a",
        "entry_bg": "#101010",
        "entry_fg": "#f2f2f2",
        "log_bg": "#080808",
        "log_fg": "#39ff77",
        "accent": "#a66cff",
        "progress": "#39ff77",
        "progress_trough": "#101010",
    },
}


def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _resource_path(*parts):
    base = getattr(sys, "_MEIPASS", _app_dir())
    return os.path.join(base, *parts)


BASE_DIR = _app_dir()
RESOURCE_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
APP_DIR = BASE_DIR
ASSET_DIR = _resource_path("LAYOUT")
FONT_DIR = _resource_path("Font")
ICON_PATH = _resource_path("acervo.ico")
PARENT_MAIN = _resource_path("catalogo_logic.py")

# Ajuste manual da posicao dos textos do cabecalho.
# Quanto menor o Y, mais para cima. Quanto maior o Y, mais para baixo.
ACERVO_Y = 0
EDTECH_Y = 30
USUARIO_Y = 8
EMAIL_Y = 20
SAIR_Y = 35
USUARIO_TEXT_WIDTH = 270
USUARIO_TEXT_HEIGHT = 44
LIMITE_ALERTA_ARQUIVOS = 100
TAMANHO_LOTE_CHECKPOINT = 10
TOOLBAR_CONTROL_HEIGHT = 28


def setup_windows_app_id():
    if os.name != "nt":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass


def load_local_fonts():
    if os.name != "nt" or not os.path.isdir(FONT_DIR):
        return
    add_font = ctypes.windll.gdi32.AddFontResourceExW
    private_font = 0x10
    for filename in os.listdir(FONT_DIR):
        if filename.lower().endswith((".ttf", ".otf")):
            try:
                add_font(os.path.join(FONT_DIR, filename), private_font, 0)
            except Exception:
                pass


def _set_window_icon(window):
    if not os.path.exists(ICON_PATH):
        return
    try:
        window.iconbitmap(ICON_PATH)
    except Exception:
        pass
    try:
        window.iconbitmap(default=ICON_PATH)
    except Exception:
        pass
    try:
        window.wm_iconbitmap(default=ICON_PATH)
    except Exception:
        pass
    try:
        icon = ImageTk.PhotoImage(Image.open(ICON_PATH))
        window.iconphoto(True, icon)
        window._app_icon_photo = icon
    except Exception:
        pass


def apply_window_icon(window):
    _set_window_icon(window)
    try:
        window.after(250, lambda: _set_window_icon(window))
    except Exception:
        pass


def center_window(window, width=None, height=None):
    window.update_idletasks()
    width = width or window.winfo_width()
    height = height or window.winfo_height()
    x = max(0, (window.winfo_screenwidth() - width) // 2)
    y = max(0, (window.winfo_screenheight() - height) // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")


def current_theme():
    return THEMES[CURRENT_THEME_NAME]


def blend_hex_color(fg, bg, alpha):
    fg = fg.lstrip("#")
    bg = bg.lstrip("#")
    fr, fg_g, fb = int(fg[0:2], 16), int(fg[2:4], 16), int(fg[4:6], 16)
    br, bg_g, bb = int(bg[0:2], 16), int(bg[2:4], 16), int(bg[4:6], 16)
    r = round(fr * alpha + br * (1 - alpha))
    g = round(fg_g * alpha + bg_g * (1 - alpha))
    b = round(fb * alpha + bb * (1 - alpha))
    return f"#{r:02x}{g:02x}{b:02x}"


def toggle_theme_name():
    global CURRENT_THEME_NAME
    CURRENT_THEME_NAME = "dark" if CURRENT_THEME_NAME == "light" else "light"
    return CURRENT_THEME_NAME


def _color_role(color):
    value = str(color).lower()
    for role in ("bg", "panel", "button_bg", "entry_bg", "log_bg"):
        if any(value == theme[role].lower() for theme in THEMES.values()):
            return role
    return None


def _fg_role(color):
    value = str(color).lower()
    for role in ("text", "subtext", "muted", "entry_fg", "log_fg", "accent"):
        if any(value == theme[role].lower() for theme in THEMES.values()):
            return role
    if value in ("white", "#ffffff"):
        return "text"
    return None


def _theme_widget_tree(widget, theme):
    widget_class = widget.winfo_class()
    try:
        if isinstance(widget, (tk.Frame, tk.Toplevel, tk.Tk)):
            role = _color_role(widget.cget("bg")) or "bg"
            widget.configure(bg=theme.get(role, theme["bg"]))
        elif isinstance(widget, tk.Button):
            widget.configure(
                bg=theme["button_bg"],
                activebackground=theme["button_active"],
                fg=theme["text"],
                activeforeground=theme["text"],
            )
        elif isinstance(widget, tk.Entry):
            widget.configure(
                bg=theme["entry_bg"],
                fg=theme["entry_fg"],
                insertbackground=theme["entry_fg"],
            )
        elif isinstance(widget, tk.Text):
            widget.configure(
                bg=theme["log_bg"],
                fg=theme["log_fg"],
                insertbackground=theme["log_fg"],
            )
        elif isinstance(widget, tk.Label):
            bg_role = _color_role(widget.cget("bg")) or "bg"
            fg_role = _fg_role(widget.cget("fg")) or "text"
            text = widget.cget("text")
            fg = theme.get(fg_role, theme["text"])
            if text == "\u2713":
                fg = "#39ff77" if CURRENT_THEME_NAME == "dark" else "#149b20"
            elif text == "!":
                fg = "#ff4d6a" if CURRENT_THEME_NAME == "dark" else "#b00020"
            elif text == "\u27f3":
                fg = theme["text"]
            widget.configure(bg=theme.get(bg_role, theme["bg"]), fg=fg)
    except tk.TclError:
        pass

    for child in widget.winfo_children():
        _theme_widget_tree(child, theme)


def place_pixel_words(parent, words, font_size, x, y, gap=5):
    frame = tk.Frame(parent, bg="#c0c0c0")
    frame.place(x=x, y=y)
    for index, word in enumerate(words):
        padx = (0, gap) if index < len(words) - 1 else (0, 0)
        tk.Label(
            frame,
            text=word,
            bg="#c0c0c0",
            fg="#000000",
            font=(PIXEL_FONT, font_size),
        ).pack(side="left", padx=padx)
    return frame


def load_catalogo_logic():
    for path in (RESOURCE_DIR, APP_DIR):
        if path and path not in sys.path:
            sys.path.insert(0, path)
    module = types.ModuleType("catalogo_logic")
    module.__file__ = PARENT_MAIN
    with open(PARENT_MAIN, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()
    interface_start = source.find("# INTERFACE")
    helpers_start = source.find("# FUN", interface_start)
    if interface_start != -1 and helpers_start != -1:
        source = (
            source[:interface_start]
            + "arquivos_encontrados = []\n"
            + "token_usuario = None\n"
            + "email_usuario = None\n"
            + "ultimo_erro_openai = None\n\n"
            + "PAUSADO = False\n"
            + "PAUSA_LOGADA = False\n\n"
            + source[helpers_start:]
        )
    marker = "\nframe_botoes = tk.Frame"
    index = source.find(marker)
    if index != -1:
        source = source[:index]
    pause_hook_target = "    for idx in range(inicio_processamento, total):\n        caminho = arquivos_encontrados[idx]"
    pause_hook = (
        "    for idx in range(inicio_processamento, total):\n"
        "        while globals().get('PAUSADO', False):\n"
        "            if not globals().get('PAUSA_LOGADA', False):\n"
        "                log('Processamento pausado. Clique em Pausar novamente para continuar.')\n"
        "                globals()['PAUSA_LOGADA'] = True\n"
        "            try:\n"
        "                janela.update()\n"
        "            except Exception:\n"
        "                pass\n"
        "            time.sleep(0.2)\n"
        "        if globals().get('PAUSA_LOGADA', False):\n"
        "            globals()['PAUSA_LOGADA'] = False\n"
        "            log('Processamento retomado.')\n"
        "        caminho = arquivos_encontrados[idx]"
    )
    source = source.replace(pause_hook_target, pause_hook)
    exec(compile(source, PARENT_MAIN, "exec"), module.__dict__)
    module.BASE_DIR = APP_DIR
    module.TOKEN_FILE = os.path.join(APP_DIR, "token.json")
    auth_module = sys.modules.get("auth_server")
    if auth_module is not None:
        auth_module.TOKEN_FILE = module.TOKEN_FILE
    return module


class RetroButton(tk.Button):
    def __init__(self, master, **kwargs):
        theme = current_theme()
        kwargs.setdefault("bg", theme["button_bg"])
        kwargs.setdefault("activebackground", theme["button_active"])
        kwargs.setdefault("fg", theme["text"])
        kwargs.setdefault("activeforeground", theme["text"])
        kwargs.setdefault("font", (UI_FONT, 9))
        kwargs.setdefault("cursor", "hand2")
        super().__init__(
            master,
            bd=2,
            relief="raised",
            **kwargs,
        )


class ThemeSwitch(tk.Canvas):
    def __init__(self, master, command, **kwargs):
        self.command = command
        super().__init__(
            master,
            width=58,
            height=26,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            **kwargs,
        )
        self.bind("<Button-1>", lambda _event: self.command())
        self.draw()

    def draw(self):
        theme = current_theme()
        is_dark = CURRENT_THEME_NAME == "dark"
        self.configure(bg=theme["bg"])
        self.delete("all")
        track_bg = theme["button_bg"]
        outline_light = "#f2f2f2" if is_dark else "#ffffff"
        outline_dark = "#050505" if is_dark else "#808080"
        self.create_rectangle(1, 1, 57, 25, fill=track_bg, outline=outline_dark)
        self.create_line(1, 1, 57, 1, fill=outline_light)
        self.create_line(1, 1, 1, 25, fill=outline_light)
        self.create_line(1, 25, 57, 25, fill=outline_dark)
        self.create_line(57, 1, 57, 25, fill=outline_dark)
        knob_x = 32 if is_dark else 2
        self.create_rectangle(knob_x, 3, knob_x + 24, 23, fill=theme["panel"], outline=outline_dark)
        self.create_line(knob_x, 3, knob_x + 24, 3, fill=outline_light)
        self.create_line(knob_x, 3, knob_x, 23, fill=outline_light)
        self.create_line(knob_x, 23, knob_x + 24, 23, fill=outline_dark)
        self.create_line(knob_x + 24, 3, knob_x + 24, 23, fill=outline_dark)
        inactive_alpha = 0.20
        inactive_sun = blend_hex_color("#cc9500", track_bg, inactive_alpha)
        inactive_moon = blend_hex_color("#ffffff", track_bg, inactive_alpha)
        if is_dark:
            self._draw_sun(14, 13, inactive_sun)
            self._draw_moon(44, 13, "#ffffff", theme["panel"])
        else:
            self._draw_sun(14, 13, "#cc9500")
            self._draw_moon(44, 13, inactive_moon, track_bg)

    def _draw_sun(self, cx, cy, color):
        for dx, dy in ((0, -8), (0, 8), (-8, 0), (8, 0), (-6, -6), (6, -6), (-6, 6), (6, 6)):
            self.create_line(cx, cy, cx + dx, cy + dy, fill=color)
        self.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill=color, outline=color)

    def _draw_moon(self, cx, cy, color, cutout_color=None):
        cutout_color = cutout_color or current_theme()["button_bg"]
        self.create_oval(cx - 6, cy - 7, cx + 6, cy + 7, fill=color, outline=color)
        self.create_oval(cx - 1, cy - 7, cx + 9, cy + 7, fill=cutout_color, outline=cutout_color)


class Tooltip:
    def __init__(self, widget, text, delay_ms=450):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self.after_id = None
        self.tooltip = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)

    def _schedule(self, _event=None):
        self._cancel()
        self.after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None

    def _show(self):
        if self.tooltip or not self.text:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tooltip,
            text=self.text,
            bg="#ffffe1",
            fg="#111111",
            bd=1,
            relief="solid",
            font=(UI_FONT, 8),
            padx=6,
            pady=3,
        )
        label.pack()

    def _hide(self, _event=None):
        self._cancel()
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class MetricValueAdapter:
    def __init__(self, label):
        self.label = label

    def config(self, **kwargs):
        text = kwargs.get("text")
        if isinstance(text, str) and ":" in text:
            kwargs["text"] = text.split(":", 1)[1].strip()
        self.label.config(**kwargs)


class FoundValueAdapter:
    def __init__(self, label):
        self.label = label

    def config(self, **kwargs):
        text = kwargs.get("text")
        if isinstance(text, str):
            if ":" in text:
                value = text.split(":", 1)[1].strip()
            else:
                value = text.strip()
            value = value.replace("arq.", "").replace("arq", "").strip()
            kwargs["text"] = value
        self.label.config(**kwargs)


class LoginScreen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Cat\u00e1logo Inteligente de Imagens v{APP_VERSION}")
        self.root.configure(bg=current_theme()["bg"])
        self.root.resizable(True, True)
        self.root.minsize(900, 560)
        apply_window_icon(self.root)

        self.logic = load_catalogo_logic()
        self.authenticated_logic = None
        self.images = {}
        self.status_var = tk.StringVar(value="")
        self._install_login_log()
        self._build_ui()
        self._apply_theme()
        center_window(self.root, 1180, 680)

    def _install_login_log(self):
        self.logic.janela = self.root
        self._original_logic_log = self.logic.log

        def login_log(message):
            text = str(message)
            lowered = text.lower()
            if "abrindo" in lowered or "login" in lowered:
                self.status_var.set("Aguardando login no navegador...")
            elif "usuario:" in lowered or "usu" in lowered:
                self.status_var.set("Login confirmado. Abrindo catalogo...")
            elif "token" in lowered:
                self.status_var.set(text)
            try:
                self.root.update_idletasks()
            except tk.TclError:
                pass

        self.logic.log = login_log

    def _asset(self, filename, size=None):
        path = os.path.join(ASSET_DIR, filename)
        img = Image.open(path).convert("RGBA")
        if size:
            img = img.resize(size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self.images[filename, size] = photo
        return photo

    def _build_ui(self):
        shell = tk.Frame(self.root, bg="#c0c0c0", bd=2, relief="sunken")
        shell.pack(fill="both", expand=True, padx=10, pady=10)
        self.theme_switch = ThemeSwitch(shell, command=self._toggle_theme)
        self.theme_switch.place(relx=1.0, x=-16, y=16, anchor="ne")
        Tooltip(self.theme_switch, "Alternar tema")

        center = tk.Frame(shell, bg="#c0c0c0")
        center.place(relx=0.5, rely=0.47, anchor="center")

        brand = tk.Frame(center, bg="#c0c0c0")
        brand.pack()
        tk.Label(
            brand,
            image=self._asset("Icon_Acervo.png", (58, 58)),
            bg="#c0c0c0",
        ).pack(side="left", padx=(0, 12))

        brand_text = tk.Frame(brand, bg="#c0c0c0", width=420, height=58)
        brand_text.pack_propagate(False)
        brand_text.pack(side="left")
        place_pixel_words(brand_text, ("Acervo", "de", "Imagens"), 17, 0, 2, gap=4)
        tk.Label(
            brand_text,
            text="EdTech",
            bg="#c0c0c0",
            fg="#8b35f6",
            font=(PIXEL_FONT, 11),
        ).place(x=0, y=34)

        self.btn_entrar = RetroButton(
            center,
            text="ENTRAR",
            width=12,
            height=2,
            font=(UI_FONT, 11, "bold"),
            command=self._entrar,
        )
        self.btn_entrar.pack(pady=(54, 0))

        tk.Label(
            center,
            textvariable=self.status_var,
            bg="#c0c0c0",
            fg="#333333",
            font=(UI_FONT, 9),
        ).pack(pady=(14, 0))

    def _apply_theme(self):
        theme = current_theme()
        self.root.configure(bg=theme["bg"])
        _theme_widget_tree(self.root, theme)
        if hasattr(self, "theme_switch"):
            self.theme_switch.draw()

    def _toggle_theme(self):
        toggle_theme_name()
        self._apply_theme()

    def _entrar(self):
        self.status_var.set("Abrindo login...")
        self.btn_entrar.config(state="disabled", relief="sunken")
        self.root.update_idletasks()
        token = self.logic.obter_token()
        if token:
            self.logic.log = self._original_logic_log
            self.authenticated_logic = self.logic
            self.root.destroy()
            return
        self.status_var.set("Login nao concluido. Tente novamente.")
        self.btn_entrar.config(state="normal", relief="raised")

    def run(self):
        self.root.mainloop()
        return self.authenticated_logic


class CatalogoLayout:
    def __init__(self, logic=None):
        self.root = tk.Tk()
        self.root.title(f"Cat\u00e1logo Inteligente de Imagens v{APP_VERSION}")
        self.root.geometry("1180x680")
        self.root.minsize(1120, 640)
        self.root.configure(bg=current_theme()["bg"])
        apply_window_icon(self.root)

        self.images = {}
        self.processando = False
        self.return_reason = "closed"
        self._build_ui()
        self._apply_theme()
        self.logic = logic or self._load_logic()
        self._bind_logic_widgets()
        if not getattr(self.logic, "token_usuario", None):
            self.logic.token_usuario = self.logic.obter_token()
        self._atualizar_usuario_logado()

    def _asset(self, filename, size=None):
        path = os.path.join(ASSET_DIR, filename)
        img = Image.open(path).convert("RGBA")
        if size:
            img = img.resize(size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self.images[filename, size] = photo
        return photo

    def _asset_tinted(self, filename, size, color):
        path = os.path.join(ASSET_DIR, filename)
        img = Image.open(path).convert("RGBA")
        if size:
            img = img.resize(size, Image.Resampling.LANCZOS)
        alpha = img.getchannel("A")
        tinted = Image.new("RGBA", img.size, color)
        tinted.putalpha(alpha)
        photo = ImageTk.PhotoImage(tinted)
        self.images[filename, size, color] = photo
        return photo

    def _action_icon_color(self):
        return "#ffffff" if CURRENT_THEME_NAME == "dark" else "#111111"

    def _refresh_action_icons(self):
        if not hasattr(self, "btn_pendentes"):
            return
        icon_size = (15, 15)
        color = self._action_icon_color()
        self.pendentes_icon = self._asset_tinted("Reprocessar Pendentes.png", icon_size, color)
        self.pausar_icon = self._asset_tinted("Pausar Processo.png", icon_size, color)
        self.exportar_icon = self._asset_tinted("Baixar Excel.png", icon_size, color)
        self.vitrine_icon = self._asset_tinted("Abrir Vitrine (2).png", icon_size, color)
        self.btn_pendentes.config(image=self.pendentes_icon)
        self.btn_pausar.config(image=self.pausar_icon)
        self.btn_exportar.config(image=self.exportar_icon)
        self.btn_vitrine.config(image=self.vitrine_icon)

    def _criar_avatar_padrao(self, initials=""):
        size = 44
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((3, 3, size - 3, size - 3), fill="#8b35f6", outline="#8b35f6")
        if initials:
            draw.text((size // 2, size // 2), initials[:2].upper(), fill="white", anchor="mm")
        photo = ImageTk.PhotoImage(img)
        self.images["avatar_default", initials] = photo
        return photo

    def _criar_avatar_foto(self, image_bytes):
        size = 44
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        img = ImageOps.fit(img, (size, size), method=Image.Resampling.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        photo = ImageTk.PhotoImage(img)
        self.images["avatar_photo"] = photo
        return photo

    def _criar_lupa_icon(self, size=15):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        scale = size / 15
        draw.ellipse(
            (2 * scale, 2 * scale, 9 * scale, 9 * scale),
            outline="#1f4a7a",
            width=max(2, int(2 * scale)),
        )
        draw.line(
            (8 * scale, 8 * scale, 13 * scale, 13 * scale),
            fill="#1f4a7a",
            width=max(2, int(2 * scale)),
        )
        draw.ellipse((4 * scale, 4 * scale, 7 * scale, 7 * scale), fill="#31c5f6")
        photo = ImageTk.PhotoImage(img)
        self.images["lupa_icon", size] = photo
        return photo

    def _criar_alerta_icon(self, size=32):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        pad = max(2, size // 12)
        points = ((size // 2, pad), (size - pad, size - pad), (pad, size - pad))
        draw.polygon(points, fill="#ffd44d", outline="#111111")
        line_width = max(2, size // 12)
        draw.line(
            (size // 2, size // 3, size // 2, int(size * 0.64)),
            fill="#111111",
            width=line_width,
        )
        dot = max(2, size // 14)
        cx, cy = size // 2, int(size * 0.78)
        draw.ellipse((cx - dot, cy - dot, cx + dot, cy + dot), fill="#111111")
        photo = ImageTk.PhotoImage(img)
        self.images["alerta_icon", size] = photo
        return photo

    def _build_ui(self):
        self.window = tk.Frame(self.root, bg="#c0c0c0", bd=2, relief="raised")
        self.window.pack(fill="both", expand=True, padx=10, pady=10)

        titlebar = tk.Frame(self.window, bg="#0a247b", height=24)
        titlebar.pack(fill="x")
        titlebar.pack_propagate(False)

        tk.Label(
            titlebar,
            text=f" Cat\u00e1logo Inteligente de Imagens v{APP_VERSION}",
            bg="#0a247b",
            fg="white",
            font=(UI_FONT, 9, "bold"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        for label in ("_", "\u25a1", "\u00d7"):
            tk.Label(
                titlebar,
                text=label,
                width=3,
                bg="#d8d8d8",
                fg="#000000",
                bd=1,
                relief="raised",
                font=("Arial", 8, "bold"),
            ).pack(side="right", padx=(1, 0), pady=2)

        titlebar.destroy()

        header = tk.Frame(self.window, bg="#c0c0c0")
        header.pack(fill="x", padx=18, pady=(26, 18))

        brand = tk.Frame(header, bg="#c0c0c0")
        brand.pack(side="left")
        tk.Label(brand, image=self._asset("Icon_Acervo.png", (58, 58)), bg="#c0c0c0").pack(side="left", padx=(0, 12))
        brand_text = tk.Frame(brand, bg="#c0c0c0")
        brand_text.config(width=620, height=58)
        brand_text.pack_propagate(False)
        brand_text.pack(side="left")
        place_pixel_words(brand_text, ("Acervo", "de", "Imagens"), 17, 0, ACERVO_Y, gap=4)
        lbl_edtech = tk.Label(
            brand_text,
            text="EdTech",
            bg="#c0c0c0",
            fg="#8b35f6",
            font=(PIXEL_FONT, 11),
        )
        lbl_edtech.place(x=0, y=EDTECH_Y)

        user = tk.Frame(header, bg="#c0c0c0")
        user.pack(side="right")
        user_text = tk.Frame(user, bg="#c0c0c0")
        user_text.config(width=USUARIO_TEXT_WIDTH, height=USUARIO_TEXT_HEIGHT)
        user_text.pack_propagate(False)
        user_text.pack(side="left", padx=(0, 10))
        self.lbl_email = tk.Label(user_text, text="Carregando...", bg="#c0c0c0", fg="#8b35f6", font=(UI_FONT, 8, "bold"), anchor="e", bd=0, relief="flat", highlightthickness=0)
        self.lbl_email.pack(fill="x", pady=(7, 1))
        self.lbl_sair = tk.Label(user_text, text="Sair", bg="#c0c0c0", fg="#222222", font=(UI_FONT, 8), cursor="hand2", bd=0, relief="flat", highlightthickness=0)
        self.lbl_sair.pack(anchor="e")
        self.lbl_sair.bind("<Button-1>", lambda _event: self._sair())
        self.lbl_sair.bind("<Enter>", lambda _event: self.lbl_sair.config(fg=current_theme()["accent"]))
        self.lbl_sair.bind("<Leave>", lambda _event: self.lbl_sair.config(fg=current_theme()["subtext"]))
        self.avatar_label = tk.Label(user, image=self._criar_avatar_padrao(), bg="#c0c0c0")
        self.avatar_label.pack(side="left")

        toolbar = tk.Frame(self.window, bg="#c0c0c0")
        toolbar.pack(fill="x", padx=18, pady=(0, 12))

        select_slot = tk.Frame(toolbar, bg="#c0c0c0", width=154, height=TOOLBAR_CONTROL_HEIGHT)
        select_slot.pack(side="left")
        select_slot.pack_propagate(False)
        self.btn_selecionar = RetroButton(
            select_slot,
            text="  Selecionar Pasta",
            image=self._asset("Selecionar Pasta.png", (14, 14)),
            compound="left",
            pady=0,
        )
        self.btn_selecionar.pack(fill="both", expand=True)
        Tooltip(self.btn_selecionar, "Selecionar pasta")

        self.path_var = tk.StringVar(value="")
        self.path_entry = tk.Entry(toolbar, textvariable=self.path_var, bd=2, relief="sunken", font=(UI_FONT, 9))
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(8, 4), ipady=4)

        action_bar = tk.Frame(toolbar, bg="#c0c0c0")
        action_bar.pack(side="left", padx=(12, 8))

        icon_size = (15, 15)
        self.play_icon = self._asset_tinted("Iniciar Processamento.png", icon_size, "#149b20")
        self.play_icon_disabled = self._asset_tinted("Iniciar Processamento.png", icon_size, "#777777")
        self.btn_iniciar = RetroButton(
            action_bar,
            image=self.play_icon,
            width=30,
            height=TOOLBAR_CONTROL_HEIGHT,
        )
        self.btn_iniciar.pack(side="left", padx=2)
        Tooltip(self.btn_iniciar, "Play / Iniciar processamento")

        action_icon_color = self._action_icon_color()
        self.pendentes_icon = self._asset_tinted("Reprocessar Pendentes.png", icon_size, action_icon_color)
        self.pausar_icon = self._asset_tinted("Pausar Processo.png", icon_size, action_icon_color)
        self.exportar_icon = self._asset_tinted("Baixar Excel.png", icon_size, action_icon_color)
        self.vitrine_icon = self._asset_tinted("Abrir Vitrine (2).png", icon_size, action_icon_color)

        self.btn_pendentes = RetroButton(action_bar, image=self.pendentes_icon, width=30, height=TOOLBAR_CONTROL_HEIGHT)
        self.btn_pendentes.pack(side="left", padx=2)
        Tooltip(self.btn_pendentes, "Reprocessar pendentes")
        self.btn_pausar = RetroButton(action_bar, image=self.pausar_icon, width=30, height=TOOLBAR_CONTROL_HEIGHT)
        self.btn_pausar.pack(side="left", padx=2)
        Tooltip(self.btn_pausar, "Pause / Pausar processamento")
        self.btn_exportar = RetroButton(action_bar, image=self.exportar_icon, width=30, height=TOOLBAR_CONTROL_HEIGHT)
        self.btn_exportar.pack(side="left", padx=2)
        Tooltip(self.btn_exportar, "Download Excel")
        self.btn_vitrine = RetroButton(action_bar, image=self.vitrine_icon, width=30, height=TOOLBAR_CONTROL_HEIGHT)
        self.btn_vitrine.pack(side="left", padx=2)
        Tooltip(self.btn_vitrine, "Abrir vitrine")

        main = tk.Frame(self.window, bg="#c0c0c0")
        main.pack(fill="both", expand=True, padx=18, pady=(0, 8))

        log_panel = tk.Frame(main, bg="#c0c0c0")
        log_panel.pack(side="left", fill="both", expand=True)
        log_title = tk.Frame(log_panel, bg="#c0c0c0")
        log_title.pack(anchor="w", pady=(0, 7))
        for index, word in enumerate(("Log", "do", "Processo")):
            padx = (0, 3) if index < 2 else (0, 0)
            tk.Label(log_title, text=word, bg="#c0c0c0", fg="#000000", font=(PIXEL_FONT, 10)).pack(side="left", padx=padx)
        self.log_texto = tk.Text(log_panel, height=18, bd=2, relief="sunken", wrap="char", bg="#ffffff", fg="#000000", font=("Courier New", 10))
        self.log_texto.pack(fill="both", expand=True)
        self.log_texto.config(state="disabled")

        metrics = tk.Frame(main, bg="#c0c0c0", width=184)
        metrics.pack(side="right", fill="y", padx=(12, 0), pady=(31, 0))
        metrics.pack_propagate(False)
        self.lbl_encontrados = self._metric(metrics, None, "Encontrados", "0", icon_image=self._criar_lupa_icon(15))
        self.lbl_processados = self._metric(metrics, "\u2713", "Processados", "0")
        self.lbl_duplicados = self._metric(metrics, "\u27f3", "Duplicados", "0")
        self.lbl_erros = self._metric(metrics, "!", "Erros", "0")

        bottom = tk.Frame(self.window, bg="#c0c0c0")
        bottom.pack(fill="x", padx=18, pady=(0, 14))
        bottom_tools = tk.Frame(bottom, bg="#c0c0c0")
        bottom_tools.pack(fill="x", pady=(0, 8))
        self.theme_switch = ThemeSwitch(bottom_tools, command=self._toggle_theme)
        self.theme_switch.pack(side="right")
        Tooltip(self.theme_switch, "Alternar tema")
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Retro.Horizontal.TProgressbar", troughcolor="#d8d8d8", background="#8b35f6", bordercolor="#8f8f8f", lightcolor="#8b35f6", darkcolor="#8b35f6")
        self.progresso = ttk.Progressbar(bottom, orient="horizontal", mode="determinate", style="Retro.Horizontal.TProgressbar")
        self.progresso.pack(fill="x")
        status = tk.Frame(bottom, bg="#c0c0c0")
        status.pack(fill="x", pady=(7, 0))
        self.lbl_progresso = tk.Label(status, text="Progresso: 0%", bg="#c0c0c0", font=(UI_FONT, 9))
        self.lbl_progresso.pack(side="left")
        tk.Label(status, text=f"Produ\u00e7\u00e3o Digital / Vers\u00e3o {APP_VERSION}", bg="#c0c0c0", fg="#777777", font=(PIXEL_FONT, 7)).pack(side="right")

    def _apply_theme(self):
        theme = current_theme()
        self.root.configure(bg=theme["bg"])
        _theme_widget_tree(self.root, theme)
        style = ttk.Style()
        style.configure(
            "Retro.Horizontal.TProgressbar",
            troughcolor=theme["progress_trough"],
            background=theme["progress"],
            bordercolor=theme["muted"],
            lightcolor=theme["progress"],
            darkcolor=theme["progress"],
        )
        if hasattr(self, "lbl_sair"):
            self.lbl_sair.config(fg=theme["subtext"])
        self._refresh_action_icons()
        if hasattr(self, "theme_switch"):
            self.theme_switch.draw()

    def _toggle_theme(self):
        toggle_theme_name()
        self._apply_theme()

    def _metric(self, master, icon, title, value, icon_image=None):
        row = tk.Frame(master, bg="#d8d8d8", bd=2, relief="raised", width=184, height=38)
        row.pack(fill="x", pady=(0, 6))
        row.pack_propagate(False)
        if icon_image is not None:
            tk.Label(row, image=icon_image, bg="#d8d8d8").pack(side="left", padx=(8, 5))
        else:
            icon_color = {"\u2713": "#149b20", "\u27f3": "#111111", "!": "#b00020"}.get(icon, "#111111")
            tk.Label(row, text=icon, bg="#d8d8d8", fg=icon_color, font=("Segoe UI Symbol", 9, "bold")).pack(side="left", padx=(7, 4))
        tk.Label(row, text=title, bg="#d8d8d8", font=(UI_FONT, 8, "bold")).pack(side="left")
        label = tk.Label(row, text=value, bg="#d8d8d8", font=(UI_FONT, 8), width=7, anchor="e")
        label.pack(side="right", padx=(4, 10))
        return label

    def _load_logic(self):
        return load_catalogo_logic()

    def _bind_logic_widgets(self):
        self.logic.janela = self.root
        self.logic.lista_arquivos = tk.Listbox(self.root)
        self.logic.log_texto = self.log_texto
        self.logic.progresso = self.progresso
        self.logic.lbl_encontrados = FoundValueAdapter(self.lbl_encontrados)
        self.logic.lbl_processados = MetricValueAdapter(self.lbl_processados)
        self.logic.lbl_duplicados = MetricValueAdapter(self.lbl_duplicados)
        self.logic.lbl_erros = MetricValueAdapter(self.lbl_erros)
        self.logic.DISPLAY_FILE_LIMIT = 0
        self.logic.PAUSADO = False
        self.logic.PAUSA_LOGADA = False
        self.logic.QUEUE_CHECKPOINT_INTERVAL = TAMANHO_LOTE_CHECKPOINT

        original_log = self.logic.log

        def ui_log(message):
            original_log(message)
            if str(message).startswith("Processamento retomado"):
                self.btn_pausar.config(relief="raised", bg=current_theme()["button_bg"])
            self.lbl_progresso.config(text=f"Progresso: {int(float(self.progresso['value']))}%")
            try:
                self.root.update()
            except tk.TclError:
                pass

        self.logic.log = ui_log
        self.btn_selecionar.config(command=self._selecionar_pasta)
        self.btn_iniciar.config(command=self._iniciar)
        self.btn_pendentes.config(command=self._reprocessar_pendentes)
        self.btn_pausar.config(command=self._pausar)
        self.btn_exportar.config(command=self.logic.exportar_para_excel)
        self.btn_vitrine.config(command=self.logic.abrir_vitrine)

    def _buscar_perfil_usuario(self):
        token = getattr(self.logic, "token_usuario", None)
        if not token:
            return None
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={self.logic.FIREBASE_API_KEY}"
            response = self.logic.requests.post(url, json={"idToken": token}, timeout=10)
            if response.status_code != 200:
                return None
            dados = response.json()
            usuarios = dados.get("users", [])
            if not usuarios:
                return None
            usuario = usuarios[0]
            photo_url = usuario.get("photoUrl", "")
            if not photo_url:
                for provider in usuario.get("providerUserInfo", []):
                    photo_url = provider.get("photoUrl", "")
                    if photo_url:
                        break
            return {
                "email": usuario.get("email", ""),
                "display_name": usuario.get("displayName", ""),
                "photo_url": photo_url,
            }
        except Exception as exc:
            self.logic.log(f"Nao foi possivel carregar perfil do usuario: {exc}")
            return None

    def _atualizar_usuario_logado(self):
        perfil = self._buscar_perfil_usuario()
        email = ""
        photo_url = ""
        display_name = ""
        if perfil:
            email = perfil.get("email", "")
            photo_url = perfil.get("photo_url", "")
            display_name = perfil.get("display_name", "")
        if not email:
            email = getattr(self.logic, "email_usuario", "") or "Nao autenticado"

        self.lbl_email.config(text=email)
        initials = ""
        if display_name:
            initials = "".join(part[0] for part in display_name.split()[:2])
        elif email and "@" in email:
            initials = email[:1]

        avatar = None
        if photo_url:
            try:
                response = self.logic.requests.get(photo_url, timeout=10)
                if response.status_code == 200:
                    avatar = self._criar_avatar_foto(response.content)
            except Exception as exc:
                self.logic.log(f"Nao foi possivel carregar foto do usuario: {exc}")

        if avatar is None:
            avatar = self._criar_avatar_padrao(initials)
        self.avatar_label.config(image=avatar)

    def _sair(self):
        if self.processando:
            self.logic.log("Aguarde o processamento terminar antes de sair.")
            return
        token_file = getattr(self.logic, "TOKEN_FILE", None)
        if token_file and os.path.exists(token_file):
            try:
                os.remove(token_file)
            except Exception as exc:
                self.logic.log(f"Nao foi possivel remover o token local: {exc}")
                return
        self.logic.token_usuario = None
        self.logic.email_usuario = None
        self.return_reason = "logout"
        self.root.destroy()

    def _selecionar_pasta(self):
        self.logic.escolher_pasta()
        if self.logic.arquivos_encontrados:
            pasta = os.path.dirname(self.logic.arquivos_encontrados[0])
            self.path_var.set(pasta)
        self.lbl_encontrados.config(text=str(len(self.logic.arquivos_encontrados)))

    def _total_arquivos_para_processar(self):
        total = len(getattr(self.logic, "arquivos_encontrados", []) or [])
        if total:
            return total
        try:
            fila = self.logic.carregar_fila_processamento()
            if fila and not fila.get("completed") and fila.get("files"):
                return len(fila.get("files", []))
        except Exception:
            pass
        return 0

    def _perguntar_modo_arquivos_grandes(self, total):
        popup = tk.Toplevel(self.root)
        popup.title("Muitos arquivos encontrados")
        popup.configure(bg=current_theme()["bg"])
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        try:
            popup.iconphoto(False, self._criar_alerta_icon(32))
        except tk.TclError:
            pass

        escolha = {"valor": None}

        tk.Label(
            popup,
            text=f"Foram encontrados {total} arquivos.",
            bg="#c0c0c0",
            fg="#111111",
            font=(UI_FONT, 10, "bold"),
        ).pack(padx=24, pady=(18, 4))
        tk.Label(
            popup,
            text="Deseja continuar o processamento?",
            bg="#c0c0c0",
            fg="#111111",
            font=(UI_FONT, 9),
        ).pack(padx=24, pady=(0, 14))

        botoes = tk.Frame(popup, bg="#c0c0c0")
        botoes.pack(padx=18, pady=(0, 18))

        def selecionar(valor):
            escolha["valor"] = valor
            popup.destroy()

        RetroButton(
            botoes,
            text="Continuar sem pausa",
            command=lambda: selecionar("sem_pausa"),
            width=20,
            height=2,
        ).pack(side="left", padx=6)

        popup.protocol("WM_DELETE_WINDOW", lambda: selecionar(None))
        _theme_widget_tree(popup, current_theme())
        popup.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (popup.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
        self.root.wait_window(popup)
        return escolha["valor"]

    def _preparar_modo_processamento(self):
        self.logic.QUEUE_CHECKPOINT_INTERVAL = TAMANHO_LOTE_CHECKPOINT
        total = self._total_arquivos_para_processar()
        if total <= LIMITE_ALERTA_ARQUIVOS:
            return True

        escolha = self._perguntar_modo_arquivos_grandes(total)
        if escolha == "sem_pausa":
            self.logic.QUEUE_CHECKPOINT_INTERVAL = TAMANHO_LOTE_CHECKPOINT
            self.logic.log(f"Modo escolhido: continuar sem pausa. A fila continua sendo salva a cada {TAMANHO_LOTE_CHECKPOINT} arquivos.")
            return True

        self.logic.log("Processamento cancelado antes de iniciar.")
        return False

    def _iniciar(self):
        if self.processando:
            return
        if not self._preparar_modo_processamento():
            return
        self.processando = True
        self.logic.PAUSADO = False
        self.logic.PAUSA_LOGADA = False
        self.btn_pausar.config(relief="raised", bg=current_theme()["button_bg"])
        self.btn_iniciar.config(state="disabled", image=self.play_icon_disabled, bg=current_theme()["button_bg"], activebackground=current_theme()["button_bg"])
        self.root.update_idletasks()
        try:
            self.logic.iniciar_processamento()
        finally:
            self.processando = False
            self.logic.PAUSADO = False
            self.logic.PAUSA_LOGADA = False
            self.btn_pausar.config(relief="raised", bg=current_theme()["button_bg"])
            self.btn_iniciar.config(state="normal", image=self.play_icon, bg=current_theme()["button_bg"], activebackground=current_theme()["button_active"])

    def _reprocessar_pendentes(self):
        if self.processando:
            return
        self.processando = True
        self.logic.PAUSADO = False
        self.logic.PAUSA_LOGADA = False
        self.btn_pausar.config(relief="raised", bg=current_theme()["button_bg"])
        self.btn_iniciar.config(state="disabled", image=self.play_icon_disabled, bg=current_theme()["button_bg"], activebackground=current_theme()["button_bg"])
        self.root.update_idletasks()
        try:
            self.logic.reprocessar_pendentes()
        finally:
            self.processando = False
            self.logic.PAUSADO = False
            self.logic.PAUSA_LOGADA = False
            self.btn_pausar.config(relief="raised", bg=current_theme()["button_bg"])
            self.btn_iniciar.config(state="normal", image=self.play_icon, bg=current_theme()["button_bg"], activebackground=current_theme()["button_active"])

    def _pausar(self):
        if not self.processando:
            self.logic.log("A pausa fica disponivel durante o processamento.")
            return
        self.logic.PAUSADO = not getattr(self.logic, "PAUSADO", False)
        if self.logic.PAUSADO:
            self.btn_pausar.config(relief="sunken", bg=current_theme()["panel"])
            self.logic.log("Pausa solicitada. O programa vai parar antes da proxima imagem.")
        else:
            self.btn_pausar.config(relief="raised", bg=current_theme()["button_bg"])
            self.logic.log("Retomada solicitada.")

    def run(self):
        self.root.mainloop()
        return self.return_reason


def main() -> None:
    """Executa a interface gráfica do Acervo Visual Inteligente."""
    setup_windows_app_id()
    load_local_fonts()
    while True:
        logic = LoginScreen().run()
        if logic is None:
            break
        result = CatalogoLayout(logic=logic).run()
        if result != "logout":
            break


if __name__ == "__main__":
    main()
