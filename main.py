"""VeriUnB - desktop interface for checking news at Universidade de Brasília."""

from __future__ import annotations

import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable

from services import DEMO_NEWS, DEMO_SOURCES, VerificationService, VerificationResult
from storage import SourceStorage
import theme


class Logo(tk.Canvas):
    def __init__(self, parent: tk.Misc, *, dark: bool = False) -> None:
        super().__init__(parent, width=220, height=68, highlightthickness=0,
                         bg=theme.BLUE if dark else theme.BG)
        filename = "logofundoazul.png" if dark else "logo.png"
        image_path = Path(__file__).resolve().with_name(filename)
        self.image = tk.PhotoImage(file=image_path).subsample(2, 2)
        self.create_image(110, 34, image=self.image)


class RoundedButton(tk.Canvas):
    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], None],
        *,
        kind: str = "primary",
        width: int | None = None,
    ) -> None:
        colors = {
            "primary": (theme.BLUE, "#174D80", theme.WHITE),
            "secondary": (theme.WHITE, theme.LIGHT_GREEN, theme.BLUE),
            "danger": (theme.WHITE, theme.ERROR_BG, theme.ERROR),
        }
        self.normal, self.hover, self.foreground = colors[kind]
        self.command = command
        self.label = text
        self.enabled = True
        self.kind = kind
        button_width = width or max(110, len(text) * 8 + 34)
        canvas_background = theme.WHITE if kind == "danger" else theme.BG
        super().__init__(parent, width=button_width, height=40, bg=canvas_background,
                         highlightthickness=0, cursor="hand2")
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self._draw(self.normal)

    def _draw(self, background: str) -> None:
        self.delete("all")
        width = int(self.cget("width"))
        height = int(self.cget("height"))
        radius = 18
        outline = theme.BORDER if self.kind != "primary" else background
        self.create_arc(0, 0, radius * 2, height, start=90, extent=180,
                        fill=background, outline=outline)
        self.create_arc(width - radius * 2, 0, width, height, start=270, extent=180,
                        fill=background, outline=outline)
        self.create_rectangle(radius, 0, width - radius, height, fill=background, outline=background)
        self.create_text(width // 2, height // 2, text=self.label,
                         fill=self.foreground, font=theme.font(10, self.kind == "primary"))

    def _on_enter(self, _event: tk.Event) -> None:
        if self.enabled:
            self._draw(self.hover)

    def _on_leave(self, _event: tk.Event) -> None:
        if self.enabled:
            self._draw(self.normal)

    def _on_click(self, _event: tk.Event) -> None:
        if self.enabled:
            self.command()

    def state(self, states: list[str]) -> None:
        self.enabled = "!disabled" not in states
        self.configure(cursor="hand2" if self.enabled else "arrow")
        self._draw(self.normal if self.enabled else "#AAB8C2")


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("VeriUnB — Verificador de Notícias da UnB")
        self.geometry("1280x800")
        self.minsize(900, 600)
        self.configure(bg=theme.BG)
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        theme.configure_ttk(self.style)
        self.verifier = VerificationService()
        self.sources = [source.copy() for source in DEMO_SOURCES]
        self.screens: dict[str, ttk.Frame] = {}
        self.nav_buttons: dict[str, tk.Button] = {}
        self._build_shell()
        self.show_screen("feed")

    def _build_shell(self) -> None:
        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=320)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        Logo(self.sidebar, dark=True).pack(padx=15, pady=(25, 30))
        tk.Label(self.sidebar, text="NAVEGAÇÃO", bg=theme.BLUE, fg="#9FBBD0",
                 font=theme.font(9, True), anchor="w").pack(fill="x", padx=25, pady=(0, 10))
        for key, label in (("feed", "▦  Feed de notícias"),
                           ("verifier", "✓  Verificador de boatos"),
                           ("sources", "⊕  Fontes de notícias")):
            button = tk.Button(self.sidebar, text=label, anchor="w", relief="flat",
                               borderwidth=0, padx=25, pady=13, bg=theme.BLUE,
                               fg=theme.WHITE, activebackground="#174D80",
                               activeforeground=theme.WHITE, font=theme.font(11),
                               cursor="hand2", command=lambda name=key: self.show_screen(name))
            button.pack(fill="x", pady=2)
            self.nav_buttons[key] = button
        ttk.Separator(self.sidebar).pack(fill="x", padx=25, pady=25)
        self.content = ttk.Frame(self, style="App.TFrame")
        self.content.pack(side="left", fill="both", expand=True)
        self._create_screens()

    def _create_screens(self) -> None:
        self.screens["feed"] = FeedScreen(self.content, self)
        self.screens["verifier"] = VerifierScreen(self.content, self)
        self.screens["sources"] = SourcesScreen(self.content, self)
        for frame in self.screens.values():
            frame.grid(row=0, column=0, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

    def show_screen(self, name: str) -> None:
        self.screens[name].tkraise()
        for key, button in self.nav_buttons.items():
            button.configure(bg="#174D80" if key == name else theme.BLUE,
                             font=theme.font(11, True) if key == name else theme.font(11))
        if name == "sources":
            self.screens[name].refresh()


class BaseScreen(ttk.Frame):
    def __init__(self, parent: tk.Misc, app: App) -> None:
        super().__init__(parent, style="App.TFrame", padding=(42, 30))
        self.app = app
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        header = ttk.Frame(self, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 25))
        header.columnconfigure(0, weight=1)
        Logo(header).grid(row=0, column=1, sticky="e")
        self.title_label = ttk.Label(header, style="Title.TLabel")
        self.title_label.grid(row=0, column=0, sticky="w")
        self.description_label = ttk.Label(self, style="Body.TLabel")
        self.description_label.grid(row=1, column=0, sticky="w", pady=(0, 20))


class FeedScreen(BaseScreen):
    def __init__(self, parent: tk.Misc, app: App) -> None:
        super().__init__(parent, app)
        self.title_label.configure(text="Feed de notícias")
        self.description_label.configure(text="Acompanhe informações selecionadas e identificadas para a comunidade da UnB.")
        outer = ttk.Frame(self, style="App.TFrame")
        outer.grid(row=2, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)
        canvas = tk.Canvas(outer, bg=theme.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        cards = ttk.Frame(canvas, style="App.TFrame")
        canvas.create_window((0, 0), window=cards, anchor="nw", tags="cards")
        cards.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure("cards", width=event.width))
        for item in DEMO_NEWS:
            self._card(cards, item)

    def _card(self, parent: tk.Misc, item: dict[str, str]) -> None:
        card = tk.Frame(parent, bg=theme.WHITE, highlightbackground=theme.BORDER,
                        highlightthickness=1, padx=22, pady=18)
        card.pack(fill="x", pady=(0, 14), padx=(2, 12))
        tk.Label(card, text="✓  VERIFICADO", bg=theme.LIGHT_GREEN, fg=theme.GREEN,
                 font=theme.font(9, True), padx=8, pady=4).pack(anchor="w")
        tk.Label(card, text=item["title"], bg=theme.WHITE, fg=theme.BLUE,
                 font=theme.font(14, True), anchor="w", justify="left",
                 wraplength=800).pack(fill="x", pady=(12, 6))
        tk.Label(card, text=item["summary"], bg=theme.WHITE, fg=theme.TEXT,
                 font=theme.font(10), anchor="w", justify="left",
                 wraplength=800).pack(fill="x")
        footer = tk.Frame(card, bg=theme.WHITE)
        footer.pack(fill="x", pady=(16, 0))
        tk.Label(footer, text=f'{item["source"]}  ·  {item["date"]}', bg=theme.WHITE,
                 fg=theme.MUTED, font=theme.font(9)).pack(side="left")
        tk.Button(footer, text="Abrir matéria  →", relief="flat", borderwidth=0,
                  bg=theme.WHITE, fg=theme.BLUE, activeforeground=theme.GREEN,
                  font=theme.font(10, True), cursor="hand2",
                  command=lambda url=item["url"]: webbrowser.open(url)).pack(side="right")


class VerifierScreen(BaseScreen):
    def __init__(self, parent: tk.Misc, app: App) -> None:
        super().__init__(parent, app)
        self.title_label.configure(text="Verificador de boatos")
        self.description_label.configure(text="Cole uma notícia ou afirmação para analisar.")
        self.columnconfigure(0, weight=1)
        body = ttk.Frame(self, style="App.TFrame")
        body.grid(row=2, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)
        self.text = tk.Text(body, height=8, wrap="word", relief="solid", bd=1,
                            highlightthickness=1, highlightcolor=theme.BLUE,
                            font=theme.font(11), padx=14, pady=12)
        self.text.grid(row=0, column=0, sticky="ew")
        controls = ttk.Frame(body, style="App.TFrame")
        controls.grid(row=1, column=0, sticky="ew", pady=(14, 20))
        self.verify_button = RoundedButton(controls, "Verificar", self.verify)
        self.verify_button.pack(side="left")
        RoundedButton(controls, "Limpar", self.clear, kind="secondary").pack(side="left", padx=10)
        self.status = ttk.Label(controls, style="Muted.TLabel")
        self.status.pack(side="left", padx=8)
        self.result = tk.Frame(body, bg=theme.WHITE, highlightbackground=theme.BORDER,
                               highlightthickness=1, padx=24, pady=20)
        self.result.grid(row=2, column=0, sticky="ew")
        self.result.columnconfigure(0, weight=1)
        self.result_title = tk.Label(self.result, bg=theme.WHITE, anchor="w")
        self.result_title.grid(row=0, column=0, sticky="ew")
        self.result_explanation = tk.Label(self.result, bg=theme.WHITE, fg=theme.TEXT,
                                           justify="left", anchor="w", wraplength=800,
                                           font=theme.font(10))
        self.result_explanation.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.sources_label = tk.Label(self.result, bg=theme.WHITE, fg=theme.MUTED,
                                      justify="left", anchor="w", wraplength=800,
                                      font=theme.font(9))
        self.sources_label.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        self.result.grid_remove()

    def verify(self) -> None:
        claim = self.text.get("1.0", "end").strip()
        if not claim:
            self.status.configure(text="Digite ou cole um texto antes de verificar.", foreground=theme.ERROR)
            self.text.focus_set()
            return
        self.verify_button.state(["disabled"])
        self.status.configure(text="Processando…", foreground=theme.BLUE)
        self.result.grid_remove()
        threading.Thread(target=self._worker, args=(claim,), daemon=True).start()

    def _worker(self, claim: str) -> None:
        result = self.app.verifier.verify(claim)
        self.after(0, lambda: self._show_result(result))

    def _show_result(self, result: VerificationResult) -> None:
        colors = {"Verdadeiro": theme.GREEN, "Falso": theme.ERROR,
                  "Inconclusivo": theme.WARNING, "Erro": theme.ERROR}
        icons = {"Verdadeiro": "✓", "Falso": "×", "Inconclusivo": "?", "Erro": "!"}
        color = colors[result.verdict]
        self.result_title.configure(text=f"{icons[result.verdict]}  {result.verdict}",
                                    fg=color, font=theme.font(18, True))
        self.result_explanation.configure(text=result.explanation)
        prefix = "Fontes e evidências:\n" if result.sources else ""
        self.sources_label.configure(text=prefix + "\n".join(f"• {source}" for source in result.sources))
        self.result.configure(bg=theme.LIGHT_GREEN if result.verdict == "Verdadeiro" else theme.WHITE)
        self.status.configure(text="Análise concluída.", foreground=theme.GREEN if result.verdict != "Erro" else theme.ERROR)
        self.verify_button.state(["!disabled"])
        self.result.grid()

    def clear(self) -> None:
        self.text.delete("1.0", "end")
        self.status.configure(text="")
        self.result.grid_remove()
        self.verify_button.state(["!disabled"])


class SourcesScreen(BaseScreen):
    def __init__(self, parent: tk.Misc, app: App) -> None:
        super().__init__(parent, app)
        self.title_label.configure(text="Fontes de notícias")
        self.description_label.configure(text="Adicione sites para organizar suas fontes de notícias.")
        self.columnconfigure(0, weight=1)
        toolbar = ttk.Frame(self, style="App.TFrame")
        toolbar.grid(row=2, column=0, sticky="new", pady=(0, 14))
        RoundedButton(toolbar, "+  Adicionar link", self.add_source, width=155).pack(side="left")
        self.feedback = ttk.Label(toolbar, style="Muted.TLabel")
        self.feedback.pack(side="left", padx=14)
        self.list_frame = ttk.Frame(self, style="App.TFrame")
        self.list_frame.grid(row=3, column=0, sticky="new")
        self.refresh()

    def refresh(self) -> None:
        if not hasattr(self, "list_frame"):
            return
        for child in self.list_frame.winfo_children():
            child.destroy()
        if not self.app.sources:
            tk.Label(self.list_frame, text="Nenhuma fonte cadastrada", bg=theme.LIGHT_GREEN,
                     fg=theme.BLUE, font=theme.font(13, True), padx=20, pady=22).pack(fill="x")
            tk.Label(self.list_frame, text="Adicione um site para começar a montar sua lista de fontes.",
                     bg=theme.BG, fg=theme.MUTED, font=theme.font(10)).pack(anchor="w", pady=12)
            return
        for index, source in enumerate(self.app.sources):
            self._source_row(index, source)

    def _source_row(self, index: int, source: dict[str, str]) -> None:
        row = tk.Frame(self.list_frame, bg=theme.WHITE, highlightbackground=theme.BORDER,
                       highlightthickness=1, padx=18, pady=14)
        row.pack(fill="x", pady=(0, 10))
        info = tk.Frame(row, bg=theme.WHITE)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=source["name"], bg=theme.WHITE, fg=theme.BLUE,
                 font=theme.font(12, True), anchor="w").pack(anchor="w")
        tk.Label(info, text=source["url"], bg=theme.WHITE, fg=theme.MUTED,
                 font=theme.font(10), anchor="w").pack(anchor="w", pady=(4, 0))
        RoundedButton(row, "Remover", lambda i=index: self.remove_source(i),
                      kind="danger", width=104).pack(side="right")

    def add_source(self) -> None:
        dialog = SourceDialog(self)
        self.wait_window(dialog)
        if dialog.value:
            self.app.sources.append(dialog.value)
            self.feedback.configure(text="Fonte adicionada à lista.")
            self.refresh()

    def remove_source(self, index: int) -> None:
        source = self.app.sources[index]
        if not messagebox.askyesno("Confirmar remoção", f'Remover a fonte "{source["name"]}"?', parent=self):
            return
        self.app.sources.pop(index)
        self.feedback.configure(text="Fonte removida da lista.")
        self.refresh()


class SourceDialog(tk.Toplevel):
    def __init__(self, parent: SourcesScreen) -> None:
        super().__init__(parent)
        self.title("Adicionar fonte")
        self.configure(bg=theme.BG)
        self.resizable(False, False)
        self.value: dict[str, str] | None = None
        frame = tk.Frame(self, bg=theme.BG, padx=25, pady=22)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text="Nova fonte de notícias", bg=theme.BG, fg=theme.BLUE,
                 font=theme.font(16, True)).pack(anchor="w")
        tk.Label(frame, text="Informe um nome e um endereço web válido.", bg=theme.BG,
                 fg=theme.MUTED, font=theme.font(10)).pack(anchor="w", pady=(5, 18))
        tk.Label(frame, text="Nome", bg=theme.BG, fg=theme.TEXT, font=theme.font(10, True)).pack(anchor="w")
        self.name = ttk.Entry(frame, width=48)
        self.name.pack(fill="x", pady=(4, 12))
        tk.Label(frame, text="Endereço do site", bg=theme.BG, fg=theme.TEXT,
                 font=theme.font(10, True)).pack(anchor="w")
        self.url = ttk.Entry(frame, width=48)
        self.url.pack(fill="x", pady=(4, 5))
        self.error = tk.Label(frame, bg=theme.BG, fg=theme.ERROR, font=theme.font(9))
        self.error.pack(anchor="w")
        buttons = tk.Frame(frame, bg=theme.BG)
        buttons.pack(fill="x", pady=(16, 0))
        RoundedButton(buttons, "Cancelar", self.destroy, kind="secondary").pack(side="right")
        RoundedButton(buttons, "Adicionar", self.submit).pack(side="right", padx=(0, 8))
        self.transient(parent)
        self.grab_set()
        self.name.focus_set()

    def submit(self) -> None:
        name, url = self.name.get().strip(), self.url.get().strip()
        if not name or not url:
            self.error.configure(text="Preencha o nome e o endereço.")
        elif not SourceStorage.is_valid_url(url):
            self.error.configure(text="Use uma URL iniciando com http:// ou https://.")
        else:
            self.value = {"name": name, "url": url}
            self.destroy()


if __name__ == "__main__":
    App().mainloop()
