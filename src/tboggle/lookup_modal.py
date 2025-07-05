from textual import on
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Input, Label

from rich.markup import escape
from tboggle.game import get_def


class LookupModal(ModalScreen):
    """Look up other words while reviewing end-of-game lists."""

    BINDINGS = [Binding("escape", "dismiss"), Binding("ctrl+q", "dismiss")]

    def compose(self):
        with Container():
            yield Label("Lookup word ([orange]Esc[/] to exit)")
            yield Input(placeholder="Enter word")
            yield Label(id="lookup-def")

    @on(Input.Submitted)
    def submitted(self, event):
        word = event.value
        defn = escape(get_def(word) or "(nothing found)")
        self.query_one(Input).value = ""
        self.query_one(Label).update(f"[u]{word}[/]: [i]{defn}[/]")