from __future__ import annotations

import dataclasses
from pathlib import Path
import pickle

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Container, VerticalScroll
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
    scores: tuple[int]

PREF_FILE = Path.home() / "tboggle-prefs.pickle"
if not (PREF_FILE).exists():
    defaults = Choices(
            set="4",
            legal_min=3,
            timeout=180,
            min_words=0,
            max_words=9999,
            min_score=0,
            max_score=9999,
            min_longest=0,
            max_longest=16,
            scores=(0, 0, 0, 1, 1, 2, 3, 5, 11, 11, 11, 11, 11, 11, 11, 11, 11),
    )
else:
    with open(PREF_FILE, "rb") as f:
        defaults = pickle.load(f)

class Chooser(App):
    TITLE = "Boggle"
    CSS = ("""
    #main {
        max-width: 60;
        layout: grid;
        grid-size: 2;
        grid-columns: 2fr 3fr;
        height: 12;
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
        height: 4;
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

        with VerticalScroll(id="full"):

            with Collapsible(title="Game options", collapsed=False):
                with Container(id="main"):

                    yield Label("Cube set:")
                    yield Select(
                        ((s.desc, s.name) for s in sets),
                        id="set",
                        prompt="Choose cube set",
                        value=defaults.set,
                    )

                    yield Label("Legal words:")
                    yield Select(
                        [
                            ("3 letters or more", 3),
                            ("4 letters or more", 4),
                            ("5 letters or more", 5),
                        ],
                        id="legal-min",
                        value=defaults.legal_min,
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
                        value=defaults.timeout,
                    )

                    yield Label("Scores:")
                    yield Select(
                            [
                                ("Flat: 1", 
                                 (0, 0, 0, 1, 1, 1, 1, 1, 1,  1,  1,  1,  1,  1,   1,   1,   1)),
                                ("Flat: 1-16", 
                                 (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)),
                                ("Squares: 1-256", 
                                 (0, 1, 4, 9, 16, 25, 36, 49, 64, 81, 100, 121, 144, 169, 196, 225, 256)),
                                ("Fibonnaci: 1-377", 
                                 (0, 0, 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377)),
                                ("Basic: 1-11", 
                                 (0, 0, 0, 1, 1, 2, 3, 5, 11, 11, 11, 11, 11, 11, 11, 11, 11)),
                                ("Basic+: 1-11 +2ea for 9+", 
                                 (0, 0, 0, 1, 1, 2, 3, 5, 11, 18, 20, 22, 24, 26, 28, 30, 32)),
                                ("Prefer big: 1-50",
                                 (0, 0, 0, 1, 1, 2, 4, 6, 9, 12, 16, 20, 25, 30, 36, 42, 50)),
                                ],
                            prompt="Choose scores",
                            id="scores",
                            value=defaults.scores,
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
                            value=str(getattr(defaults, f"min_{id}")),
                            max_length=4,
                        )
                        yield Input(
                            type="integer",
                            id=f"max-{id}",
                            value=str(getattr(defaults, f"max_{id}")),
                            max_length=4,
                        )

            with Horizontal(id="start-buttons"):
                yield Button("Play", variant="success", id="play")
                yield Button("Save as Default", id="save")
                yield Button("Restore Game", id="restore")
                yield Button("Quit", variant="error", id="quit")

        yield Footer()

    def set_to_defaults(self):
        defaults.set=self.query_one("#set").value
        defaults.legal_min=int(self.query_one("#legal-min").value)
        defaults.timeout=int(self.query_one("#timeout").value)
        defaults.min_words=int(self.query_one("#min-words").value)
        defaults.max_words=int(self.query_one("#max-words").value)
        defaults.min_score=int(self.query_one("#min-score").value)
        defaults.max_score=int(self.query_one("#max-score").value)
        defaults.min_longest=int(self.query_one("#min-longest").value)
        defaults.max_longest=int(self.query_one("#max-longest").value)
        defaults.scores=self.query_one("#scores").value

    @on(Button.Pressed, "#play")
    def action_play(self):
        self.set_to_defaults()
        self.app.exit((defaults, "play"))

    @on(Button.Pressed, "#quit")
    def action_quit(self):
        self.app.exit(False)

    @on(Button.Pressed, "#save")
    def action_save(self):
        self.set_to_defaults()
        with open(PREF_FILE, "wb") as prefs:
            pickle.dump(defaults, prefs)
        self.notify(f"Saved to {PREF_FILE}", title="Saved")

    @on(Button.Pressed, "#restore")
    def action_restore(self):
        self.set_to_defaults()
        self.app.exit((defaults, "restore"))


if __name__ == "__main__":
    app = Chooser()
    app.run()
