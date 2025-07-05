from __future__ import annotations

import dataclasses
import sys
from random import randint

from rich.markup import escape
from textual import on
from textual.timer import Timer
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, Container
from textual.reactive import reactive, var
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Static, Footer, Input, DataTable, Label, Button

from tboggle import fill
from tboggle.dice import DiceSet
from tboggle.game import Game, GuessResult, get_def
from tboggle.chooser import Chooser, Choices
from tboggle.pause_modal import PauseModal
from tboggle.exit_modal import ExitModal
from tboggle.lookup_modal import LookupModal


class Board(Widget):
    """Show non-interactive board.

    Is always shown, both during game play and after.
    """

    app: BoggleApp

    def on_mount(self):
        self.styles.height = 2 * len(self.app.game.board) + 3

    def render(self):
        lines = []
        for row in self.app.game.board:
            line = "  ".join(cell for cell in row)
            lines.append(line)
        return "\n\n".join(lines)


class LeftPane(Vertical):
    app: BoggleApp

    def on_mount(self):
        self.styles.width = len(self.app.game.board[0]) * 4 + 4


class WordInput(Input):
    app: BoggleApp
    history: list[str]
    history_at: int

    BINDINGS = [
            Binding("up", "up"),
            Binding("down", "down"),
            ]

    def on_mount(self):
        self.history = []
        self.history_at = 0

    def action_up(self):
        if self.history_at > 0:
            self.history_at -= 1
            self.value = self.history[self.history_at]
            self.cursor_position = len(self.value)

    def action_down(self):
        if self.history_at < len(self.history) - 1:
            self.history_at += 1
            self.value = self.history[self.history_at]
            self.cursor_position = len(self.value)
        else:
            self.value = ""
            self.cursor_position = 0
            self.history_at = len(self.history) 

    @on(Input.Submitted)
    def submitted(self, event):
        word = event.value
        result = self.app.game.handle_guess(word)
        if result == GuessResult.GOOD:
            self.app.add_word(word)
            self.classes = "good"
        elif result == GuessResult.BAD:
            self.classes = "bad"
        elif result == GuessResult.DUP:
            self.classes = "dup"
        elif result == GuessResult.NOT_ON_BOARD:
            self.classes = "not-on-board"
        self.value = ""
        self.history.append(event.value)
        self.history_at = len(self.history)
        self.placeholder = word

    @on(Input.Changed)
    def reset_color_on_entry(self, event):
        if event.value:
            self.classes = ""


class StatusArea(Container):
    app: BoggleApp

    def compose(self):
        game = self.app.game
        max_words = str(len(game.legal.words))
        max_score = str(game.legal.score)
        max_long = str(game.legal.longest)
        dur = str(self.app.game.duration)
        time_left = str(self.app.time_left)
        num_words = str(len(game.found.words))
        longest = str(game.found.longest)
        score = str(game.found.score)

        if self.app.game.duration:
            yield Label("Time:", classes="status-label")
            yield Label(dur, classes="status-r status-base")
            yield Label(time_left, classes="status-r", id="num_time")

        yield Label("Words:", classes="status-label")
        yield Label(max_words, classes="status-r status-base")
        yield Label(num_words, classes="status-r", id="num-words")

        yield Label("Long:", classes="status-label")
        yield Label(max_long, classes="status-r status-base")
        yield Label(longest, classes="status-r", id="num-long")

        yield Label("Score:", classes="status-label")
        yield Label(max_score, classes="status-r status-base")
        yield Label(score, classes="status-r", id="num-score")


@dataclasses.dataclass
class Page:
    rows: list[list[str]]
    label: str
    col_width: int
    total_words: int

class Results(DataTable):
    def on_mount(self):
        self.cur_page_num = 1
        self.pages = []
        if not self.app.playing:
            self.make_stats()

    def on_key(self, event):
        if event.key == "space" and self.cur_page_num < len(self.pages):
            self.show_page(self.cur_page_num + 1)
        if event.key == "backspace" and self.cur_page_num > 1:
            self.show_page(self.cur_page_num - 1)

    def on_data_table_cell_highlighted(self, event):
        if not self.disabled and event.value and not self.app.playing:
            word = event.value
            defn = escape(get_def(word) or "(nothing found)")
            score = self.app.game.scores[len(word)]
            self.app.query_one("#def-area").update(f"[u]{word} ({score})[/]: [i]{defn}[/]")

    def make_list(self, title, words_set):
        self.header_height = 0

        words = list(sorted(words_set))
        if not words:
            self.pages = [Page([], title, 0, 0)]
        else:
            width = max(len(w) for w in words)
            num_cols = (self.size.width - 4) // (width + 3)
            num_rows = self.size.height
            self.pages = [
                Page(rows, title, width, len(words))
                for rows
                in fill.fill(words, num_cols, num_rows)
            ]

        self.show_page(1)

    def show_page(self, num: int):
        self.disabled = False
        self.cur_page_num = num
        p = self.pages[num - 1]
        has_next = num < len(self.pages)
        has_prev = num > 1
        if has_next and has_prev:
            nav = f" ([orange]BS[/] ↑, [orange]Spc[/]: ↓)"
        elif has_next:
            nav = f" ([orange]Spc[/] ↓)"
        elif has_prev:
            nav = f" ([orange]BS[/] ↑)"
        else:
            nav = ""
        self.border_title = f"{p.label}: {p.total_words}"
        self.border_subtitle = f"{num}/{len(self.pages)}{nav}"
        self.clear(columns=True)
        if p.rows:
            self.add_columns(*(f"c{x:{p.col_width}}" for x in p.rows[0]))
            self.add_rows(p.rows)
        if not self.app.playing:
            self.focus()

    def make_stats(self):
        self.border_title = "Stats"
        self.border_subtitle = ""
        self.clear(columns=True)
        self.add_columns("Metric", "Value", "More")
        self.header_height = 0
        g = self.app.game
        self.add_rows([
            ("Dice Set", "Name Here"),
            ("Scoring", "Name Here"),
            ("", "/".join(str(s) for s in g.scores)),
            ("Words", f"{(len(g.found.words) / len(g.legal.words)):.2%}"),
            ("Score", f"{(g.found.score / g.legal.score):.2%}"),
        ])
        self.add_rows([
            ("",""),
            ("[orange]Freq Legal[/]", "[orange]Found[/]"),
            *((f"{c[0]:2}: {c[1]:3}", f"{c[2]:3}") for c in g.freqs()),
        ])
        self.disabled = True
        

class BoggleApp(App):
    CSS_PATH = "styles.css"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding("escape", "pause", "Pause"),
        Binding("ctrl+e", "end", "End game", priority=True),
        # Binding("q",       "quit",    "Quit"),

        Binding("s", "stats", "Stats"),
        Binding("m", "missed", "Missed"),
        Binding("f", "found", "Found"),
        Binding("b", "bad", "Bad"),
        Binding("?", "lookup", "Lookup"),
        # Binding("ctrl+a", "again", "Again"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    timer = var(True)
    playing = reactive(True, recompose=True, init=False)

    def __init__(self, game):
        self.game = game
        self.time_left = game.duration
        self.time_max = game.duration
        self.my_timer: Timer | None = None
        self.time_widget = None  # Cache for timer widget
        super().__init__()

    def on_mount(self):
        if self.game.duration:
            self.my_timer = self.set_interval(1, self.update_timer)
            # Cache the timer widget reference for performance
            try:
                self.time_widget = self.query_one("#num_time")
            except:
                self.time_widget = None

    def update_timer(self):
        if self.timer and self.time_widget:
            self.time_left -= 1
            self.time_widget.update(str(self.time_left))
            if self.time_left == 0:
                self.action_end()
            elif self.time_left < 20:
                self.time_widget.styles.color = "red"
            elif self.time_left < 40:
                self.time_widget.styles.color = "orange"

    def action_end(self):
        self.timer = False
        if self.game.duration:
            self.my_timer.stop()
        self.playing = False
        self.action_stats()

    def compose(self):
        with Horizontal():
            with LeftPane():
                yield Board()
                if self.playing:
                    yield WordInput(
                        max_length=16 if self.game.width > 4 else 15,
                        restrict=r"[A-Za-z]*",
                        placeholder="Enter word",
                    )
                yield StatusArea()
            with Vertical(classes="right-pane"):
                if self.playing:
                    # yield Log()
                    yield Results()
                else:
                    yield Results()
        if not self.playing:
            yield Label(id="def-area")
        yield Footer()

    # -----------------------------

    def check_action(self, event, parameters):
        if not self.app.game.duration and event == "pause":
            return False
        if self.playing:
            if event in ("stats", "missed", "found", "bad", "again", "lookup"):
                return False
        if not self.playing:
            if event in ("end", "pause"):
                return False
        return True

    def action_quit(self) -> None:
        """Called when the user hits Ctrl+Q."""
        self.push_screen(ExitModal())

    def action_lookup(self):
        self.push_screen(LookupModal())

    def action_pause(self):
        def restart_timer(_):
            self.query_one("Input").disabled = False
            self.timer = True

        self.query_one("Input").disabled = True
        self.timer = False
        self.push_screen(PauseModal(), restart_timer)

    def action_found(self):
        self.query_one(Results).make_list("Found", self.game.found.words)

    def action_missed(self):
        self.query_one(Results).make_list("Missed", self.game.get_missed())

    def action_bad(self):
        self.query_one(Results).make_list("Bad", self.game.bad.words)

    def action_stats(self):
        self.query_one(Results).make_stats()

    # -------------------------------

    def add_word(self, word):
        found = self.query_one(Results)
        found.make_list("Found", self.game.found.words)
        found.cursor_type = "none"
        f = self.game.found
        self.query_one("#num-score").update(str(f.score))
        self.query_one("#num-words").update(str(len(f.words)))
        self.query_one("#num-long").update(str(f.longest))


def main():
    import os

    os.system('cls' if os.name == 'nt' else 'clear')

    # size = sys.argv[1] if len(sys.argv) > 1 else "4"
    # dur = int(sys.argv[2]) if len(sys.argv) > 2 else 180
    choices: Choices = None
    while True:
        if not choices:
            result = Chooser().run()
            if not result: break
        choices, start_by = result

        set =  DiceSet.get_by_name(choices.set)
        game = Game(set, set.num, set.num, duration=choices.timeout, min_legal=choices.legal_min, scores=choices.scores)
        if start_by == "restore":
            dice = [ 65, 65, 65, 65, 66, 66, 66, 66 ,67, 67, 67, 67, 69,69,69,69]
            #g = Game(DiceSet.get_by_name("4"), 4, 4, scores)
            game.restore_game(dice)
            #game.restore_game()
        else:
            game.fill_board(
                min_words=choices.min_words,
                max_words=choices.max_words,
                min_score=choices.min_score,
                max_score=choices.max_score,
                min_longest=choices.min_longest,
                max_longest=choices.max_longest,
            )
        app = BoggleApp(game)
        rez = app.run()
        if rez == "board":
            pass
        elif rez == "game":
            choices = None
        else:
            break

if __name__ == "__main__":
    main()
