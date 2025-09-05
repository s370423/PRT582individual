"""Hangman game (logic + Tkinter UI) in one file.

Provides the game logic (masking, guessing, timed turns) and a small
Tkinter app to play it. Written to satisfy flake8 and pylint defaults.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional, Set
import random
import time
import tkinter as tk


# =============================== logic ===============================


def mask_text(secret: str, guessed: Optional[Set[str]] = None) -> str:
    """
    Return a masked view of *secret*, revealing only letters in *guessed*.

    Letters not in *guessed* become "_". Spaces are preserved by returning
    "" for them so the final join inserts spaces around them. Punctuation
    remains visible.

    Example:
        "Hello World!" -> "_ _ _ _ _  _ _ _ _ _ !"
    """
    guessed = {c.lower() for c in (guessed or set())}

    def token(ch: str) -> str:
        if ch == " ":
            # keep word breaks; returning "" makes join add spaces around it
            return ""
        if not ch.isalpha():
            return ch
        return ch if ch.lower() in guessed else "_"

    return " ".join(token(ch) for ch in secret)


@dataclass
class Game:
    """Basic Hangman game (no timer)."""

    secret: str
    lives: int = 6
    guessed: Set[str] = field(default_factory=set)

    @property
    def masked(self) -> str:
        """Masked version of the secret using current guesses."""
        return mask_text(self.secret, self.guessed)

    @property
    def won(self) -> bool:
        """True if all letters in the secret have been guessed."""
        letters = {c.lower() for c in self.secret if c.isalpha()}
        return letters.issubset({c.lower() for c in self.guessed})

    @property
    def lost(self) -> bool:
        """True if no lives remain and the game has not been won."""
        return self.lives <= 0 and not self.won

    def guess(self, raw: str) -> str:
        """Apply one letter guess; returns: 'hit'|'miss'|'repeat'|'invalid'."""
        if not raw or len(raw) != 1 or not raw.isalpha():
            return "invalid"

        ch = raw.lower()

        if ch in {c.lower() for c in self.guessed}:
            return "repeat"

        if ch in {c.lower() for c in self.secret if c.isalpha()}:
            self.guessed.add(ch)
            return "hit"

        self.lives -= 1
        return "miss"


class GameWithTimer(Game):
    """Hangman that deducts a life when the per-turn deadline is exceeded."""

    def __init__(
        self,
        secret: str,
        lives: int = 6,
        seconds_per_turn: int = 15,
        clock: Optional[Callable[[], float]] = None,
    ):
        """Create a timed game; the clock can be injected for testing."""
        super().__init__(secret=secret, lives=lives)
        self.seconds_per_turn = seconds_per_turn
        self._clock = clock or time.monotonic
        self._deadline = self._clock() + self.seconds_per_turn

    def _apply_timeout_if_needed(self, now: float) -> bool:
        """If the deadline passed, consume a life and extend the deadline."""
        if now > self._deadline:
            self.lives -= 1
            self._deadline = now + self.seconds_per_turn
            return True
        return False

    def guess(self, raw: str) -> str:
        """Apply a guess, accounting for timeouts before the guess."""
        now = self._clock()
        if self._apply_timeout_if_needed(now):
            return "timeout"
        return super().guess(raw)

    def now(self) -> float:
        """Public wrapper for the injected clock (avoids protected access)."""
        return self._clock()


# ================================ UI =================================


BASIC_WORDS = [
    "python",
    "testing",
    "variable",
    "function",
    "quality",
    "packet",
]

PHRASES = [
    "unit testing",
    "software quality",
    "clean code",
    "open source",
]

SECONDS_PER_TURN = 15
START_LIVES = 6


def choose_secret(level: str) -> str:
    """Pick a secret word/phrase according to the selected *level*."""
    words = PHRASES if level == "intermediate" else BASIC_WORDS
    return random.choice(words)


# pylint: disable=too-many-instance-attributes
class HangmanApp(tk.Tk):
    """Tiny Tkinter app that uses the game logic above."""

    def __init__(self) -> None:
        """Build the UI: level, masked word, lives/timer, input, buttons."""
        super().__init__()
        self.title("Hangman (TDD)")
        self.resizable(False, False)
        self.configure(bg="#FFF8E7")

        title = tk.Label(
            self,
            text="Hangman Game",
            font=("Segoe UI", 18, "bold"),
            bg="#FFF8E7",
        )
        title.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        body = tk.Frame(self, bg="#FFF8E7")
        body.grid(row=1, column=0, padx=16, pady=8, sticky="n")

        lvl = tk.Frame(body, bg="#FFF8E7")
        lvl.pack(anchor="w")
        tk.Label(lvl, text="Level:", bg="#FFF8E7").pack(side=tk.LEFT)
        self.level = tk.StringVar(value="basic")
        tk.Radiobutton(
            lvl,
            text="Basic",
            variable=self.level,
            value="basic",
            bg="#FFF8E7",
        ).pack(side=tk.LEFT, padx=6)
        tk.Radiobutton(
            lvl,
            text="Intermediate",
            variable=self.level,
            value="intermediate",
            bg="#FFF8E7",
        ).pack(side=tk.LEFT, padx=6)

        self.lbl_word = tk.Label(
            body,
            text="_ _ _ _ _",
            font=("Consolas", 26, "bold"),
            bg="#FFF8E7",
        )
        self.lbl_word.pack(pady=(10, 8), anchor="w")

        info = tk.Frame(body, bg="#FFF8E7")
        info.pack(fill="x")
        self.var_lives = tk.StringVar(value=f"Lives: {START_LIVES}")
        self.var_time = tk.StringVar(
            value=f"Time left: {SECONDS_PER_TURN}s"
        )
        lbl_lives = tk.Label(
            info,
            textvariable=self.var_lives,
            font=("Segoe UI", 11, "bold"),
            bg="#FFF8E7",
        )
        lbl_lives.pack(side=tk.LEFT)
        lbl_time = tk.Label(
            info,
            textvariable=self.var_time,
            font=("Segoe UI", 11, "bold"),
            bg="#FFF8E7",
        )
        lbl_time.pack(side=tk.RIGHT)

        row = tk.Frame(body, bg="#FFF8E7")
        row.pack(pady=(12, 6), fill="x")
        tk.Label(row, text="Your guess:", bg="#FFF8E7").pack(side=tk.LEFT)
        self.entry = tk.Entry(row, width=6, font=("Segoe UI", 12))
        self.entry.pack(side=tk.LEFT, padx=6)
        self.entry.bind("<Return>", self.on_submit)

        btns = tk.Frame(body, bg="#FFF8E7")
        btns.pack(pady=4, fill="x")
        self.btn_submit = tk.Button(
            btns,
            text="Submit",
            width=10,
            command=self.on_submit,
        )
        self.btn_submit.pack(side=tk.LEFT, padx=4)
        self.btn_new = tk.Button(
            btns,
            text="New",
            width=8,
            command=self.start_game,
        )
        self.btn_new.pack(side=tk.LEFT, padx=4)
        btn_quit = tk.Button(btns, text="Quit", width=8, command=self.destroy)
        btn_quit.pack(side=tk.LEFT, padx=4)

        self.var_msg = tk.StringVar(
            value="Choose level and press New to start."
        )
        lbl_info = tk.Label(
            body,
            textvariable=self.var_msg,
            fg="#444",
            bg="#FFF8E7",
        )
        lbl_info.pack(pady=(6, 4), anchor="w")

        self.result_banner = tk.Label(
            body,
            text="",
            font=("Segoe UI", 16, "bold"),
            bg="#FFF8E7",
        )
        self.result_banner.pack(pady=(2, 0), anchor="w")

        self.g: Optional[GameWithTimer] = None
        self._tick_job: Optional[str] = None

    # ------------------------- game control -------------------------

    def start_game(self) -> None:
        """Start a new game using the selected level."""
        secret = choose_secret(self.level.get())
        self.g = GameWithTimer(
            secret,
            lives=START_LIVES,
            seconds_per_turn=SECONDS_PER_TURN,
        )
        self.var_msg.set("Game started. Guess one letter.")
        self.result_banner.config(text="", fg="#000000")
        self._refresh_board()
        self._start_ticker()
        self.entry.config(state="normal")
        self.btn_submit.config(state="normal")
        self.entry.focus()

    def _start_ticker(self) -> None:
        """Start or restart the periodic timer update."""
        if self._tick_job:
            self.after_cancel(self._tick_job)
            self._tick_job = None
        self._tick()

    def _remaining(self) -> int:
        """Seconds remaining on the current turn."""
        if not self.g:
            return 0
        deadline = getattr(self.g, "_deadline", 0)
        return int(max(0, deadline - self.g.now()))

    def _tick(self) -> None:
        """Update the time label and process timeouts."""
        if self.g:
            remain = self._remaining()
            self.var_time.set(f"Time left: {remain}s")
            if remain <= 0:
                res = self.g.guess("")  # timeout path
                if res == "timeout":
                    msg_timeout = "Time's up! A life was lost."
                    self.var_msg.set(msg_timeout)
                    self._refresh_board()
        self._tick_job = self.after(250, self._tick)

    def _refresh_board(self) -> None:
        """Refresh masked word, lives, and win/lose banners."""
        self.lbl_word.config(text=self.g.masked)
        self.var_lives.set(f"Lives: {self.g.lives}")

        if self.g.won:
            self._end_with_banner(
                f"You won! Answer: {self.g.secret}",
                color="#107C10",
            )
        elif self.g.lost:
            self._end_with_banner(
                f"You lost! Answer: {self.g.secret}",
                color="#C50F1F",
            )

    def _end_with_banner(self, text: str, color: str) -> None:
        """Show result banner and disable input until 'New' is pressed."""
        self.result_banner.config(text=text, fg=color)
        self.var_msg.set("Press New to start another round.")
        self.entry.config(state="disabled")
        self.btn_submit.config(state="disabled")

    # --------------------------- events ----------------------------

    def on_submit(self, _evt: Optional[tk.Event] = None) -> None:
        """Handle Return/Submit: read input, apply guess, update message."""
        if not self.g:
            self.start_game()
            return

        raw = self.entry.get().strip()
        self.entry.delete(0, tk.END)

        res = self.g.guess(raw)
        mapping = {
            "timeout": "Time's up! A life was lost.",
            "hit": "Correct guess.",
            "miss": "Wrong guess.",
            "repeat": "Already guessed.",
            "invalid": "Enter one A–Z letter.",
        }
        self.var_msg.set(mapping.get(res, res))
        self._refresh_board()


# ============================== launcher ==============================


if __name__ == "__main__":
    HangmanApp().mainloop()
