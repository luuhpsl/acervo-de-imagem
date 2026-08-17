from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

from app_template.features.notes.model import Note
from app_template.features.notes.services import NoteStorageError
from app_template.features.notes.use_cases import add_note, list_notes, remove_note

if TYPE_CHECKING:
    import tkinter as tk
    from tkinter import ttk


class NotesController:
    """Orquestra ações da GUI sem depender de widgets ou de um display real."""

    def __init__(
        self,
        list_fn: Callable[[], list[Note]] = list_notes,
        add_fn: Callable[[str], Note] = add_note,
        remove_fn: Callable[[str], bool] = remove_note,
    ) -> None:
        self._list = list_fn
        self._add = add_fn
        self._remove = remove_fn

    def get_notes(self) -> list[Note]:
        return self._list()

    def add(self, title: str) -> list[Note]:
        self._add(title)
        return self._list()

    def remove(self, note_ids: Sequence[str]) -> list[Note]:
        for note_id in note_ids:
            self._remove(note_id)
        return self._list()


def create_notes_panel(parent: tk.Misc) -> ttk.Frame:  # pragma: no cover - exige display real
    """Monta o painel de notas.

    Fora da medição de cobertura porque só executa com display. Toda a lógica
    fica em `NotesController`, testado sem widgets: mantenha este corpo restrito
    a montagem de widgets e tradução de eventos em chamadas do controlador.
    """
    import tkinter as tk
    from tkinter import messagebox, ttk

    controller = NotesController()
    panel = ttk.Frame(parent, padding=16)
    add_frame = ttk.Frame(panel)
    add_frame.pack(fill="x", pady=(0, 16))

    ttk.Label(add_frame, text="Nova nota:").pack(side="left", padx=(0, 8))
    title_var = tk.StringVar(master=add_frame)
    entry = ttk.Entry(add_frame, textvariable=title_var)
    entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

    list_frame = ttk.Frame(panel)
    list_frame.pack(fill="both", expand=True)
    columns = ("id", "title", "date")
    tree = ttk.Treeview(list_frame, columns=columns, show="headings")
    tree.heading("id", text="ID")
    tree.heading("title", text="Título")
    tree.heading("date", text="Data")
    tree.column("id", width=250)
    tree.column("title", width=300)
    tree.column("date", width=150)

    scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def render_notes(notes: Sequence[Note]) -> None:
        for item in tree.get_children():
            tree.delete(item)
        for note in notes:
            tree.insert("", "end", values=(note.id, note.title, note.created_at))

    def refresh_list() -> None:
        try:
            render_notes(controller.get_notes())
        except NoteStorageError as exc:
            messagebox.showerror("Erro de armazenamento", str(exc))

    def on_add() -> None:
        try:
            notes = controller.add(title_var.get())
            title_var.set("")
            render_notes(notes)
        except ValueError as exc:
            messagebox.showerror("Erro de validação", str(exc))
        except NoteStorageError as exc:
            messagebox.showerror("Erro de armazenamento", str(exc))

    def on_remove() -> None:
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma nota para remover.")
            return
        note_ids = [str(tree.item(item, "values")[0]) for item in selected]
        try:
            render_notes(controller.remove(note_ids))
        except NoteStorageError as exc:
            messagebox.showerror("Erro de armazenamento", str(exc))

    ttk.Button(add_frame, text="Adicionar", command=on_add).pack(side="left")
    btn_frame = ttk.Frame(panel)
    btn_frame.pack(fill="x", pady=(16, 0))
    ttk.Button(btn_frame, text="Remover selecionada", command=on_remove).pack(side="right")
    refresh_list()
    return panel
