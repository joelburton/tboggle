from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Label


class PauseModal(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss"), Binding("ctrl+q", "dismiss")]

    def compose(self):
        with Container():
            yield Label("Game Paused\n\nPress [orange]Esc[/] when ready")