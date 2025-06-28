from __future__ import annotations

import dataclasses

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Container
from textual.widgets import Input, Label, Button, Header, Select, Collapsible, Footer
from textual.binding import Binding

from tboggle.dice import sets

@dataclasses.dataclass
class Choices:
    set: str
    legal_min: int
    timeout: int
    min_words: int
    max_words: int
    min_score: int
    max_score: int
    min_longest: int
    max_longest: int


class Chooser(App):
    TITLE = "Boggle"
    CSS = ("""
    
    #main {
    max-width: 60;
    layout: grid;
    grid-size: 2;
    grid-columns: 2fr 3fr;
    height: 9;
    }
    #adv {
    max-width: 60;
        layout: grid;
        grid-size: 3;
        height: 6;
        grid-columns: 2fr 1fr 2fr;
    }
    #main Label {
        width: 100%;
        text-align: right;
        padding-top: 1;
    }
    #adv Label {
        width: 100%;
        text-align: right;
    }
    #main Input, #adv Input {
        border: none;
        border-bottom: solid $primary;
        margin-left: 3;
        padding-left: 0;
        width: 5;
    }
    #start-buttons {
        margin-top: 1;
    }
    #start-buttons Button {
        margin-right: 1;
    }
           """)

    BINDINGS = [
        Binding("p", "play"),
        Binding("ctrl+p", "play", "Play"),
        Binding("q", "quit"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    ENABLE_COMMAND_PALETTE = False

    def compose(self) -> ComposeResult:
        yield Header()

        with Collapsible(title="Game options", collapsed=False):
            with Container(id="main"):

                yield Label("Cube set:")
                yield Select(
                    ((s.desc, s.name) for s in sets),
                    id="set",
                    prompt="Choose cube set",
                    value="4",
                )

                yield Label("Legal words:")
                yield Select(
                    [
                        ("3 letters or more", 3),
                        ("4 letters or more", 4),
                        ("5 letters or more", 5),
                    ],
                    id="legal-min",
                    value=3,
                )

                yield Label("Game timeout:")
                yield Select(
                    [
                        ("1 minute", 60),
                        ("1.5 minutes", 90),
                        ("2 minutes", 120),
                        ("3 minutes", 180),
                        ("4 minutes", 240),
                        ("5 minutes", 300),
                        ("7 minutes", 420),
                        ("10 minutes", 600),
                        ("No timeout", 0),
                    ],
                    prompt="Choose game timeout",
                    id="timeout",
                    value=180,
                )

        with Collapsible(title="Min/max options for board finding", collapsed=True):
            with Container(id="adv"):
                for (id, label) in [
                    ("words", "Number words:"),
                    ("score", "Score:"),
                    ("longest", "Longest word:"),
                ]:
                    yield Label(label)
                    yield Input(
                        type="integer",
                        id=f"min-{id}",
                        value="0",
                        max_length=4,
                    )
                    yield Input(
                        type="integer",
                        id=f"max-{id}",
                        value="9999",
                        max_length=4,
                    )

        with Horizontal(id="start-buttons"):
            yield Button("Play", variant="success", id="play")
            yield Button("Quit", variant="error", id="quit")

        yield Footer()

    @on(Button.Pressed, "#play")
    def action_play(self):
        choices = Choices(
                set=self.query_one("#set").value,
                legal_min=int(self.query_one("#legal-min").value),
                timeout=int(self.query_one("#timeout").value),
                min_words=int(self.query_one("#min-words").value),
                max_words=int(self.query_one("#max-words").value),
                min_score=int(self.query_one("#min-score").value),
                max_score=int(self.query_one("#max-score").value),
                min_longest=int(self.query_one("#min-longest").value),
                max_longest=int(self.query_one("#max-longest").value),
            )
        self.app.exit(choices)

    @on(Button.Pressed, "#quit")
    def action_quit(self):
        self.app.exit(False)

if __name__ == "__main__":
    app = Chooser()
    app.run()
