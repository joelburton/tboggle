from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ExitModal(ModalScreen):
    """A modal exit screen."""

    BINDINGS = [
        Binding("escape", "dismiss"),
        Binding("b", "board"),
        Binding("ctrl+b", "board"),
        Binding("g", "game"),
        Binding("ctrl+g", "game"),
        Binding("q", "quit"),
        Binding("ctrl+q", "quit"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label("Play again or quit? ([orange]Esc[/] to cancel)\n")
            with Horizontal():
                yield Button("New Board", id="board", variant="primary")
                yield Button("New Game", id="game", variant="warning")
                yield Button("Quit", id="quit", variant="error")

    @on(Button.Pressed, "#board")
    def action_board(self) -> None:
        self.app.exit("board")

    @on(Button.Pressed, "#game")
    def action_game(self) -> None:
        self.app.exit("game")

    @on(Button.Pressed, "#quit")
    def action_quit(self) -> None:
        self.app.exit("quit")

    @on(Button.Pressed, "#continue")
    def action_continue(self) -> None:
        self.dismiss()