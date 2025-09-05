"""Unit tests for hangman_game (logic + timer)."""

import hangman_game as game


def test_mask_text_masks_letters_only() -> None:
    """Letters masked as '_', spaces/punctuation preserved."""
    assert game.mask_text("Hello World!") == "_ _ _ _ _  _ _ _ _ _ !"


class FakeClock:
    """Tiny controllable clock for deterministic timer tests."""

    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        """Move time forward by *seconds*."""
        self.t += seconds


def test_initial_state() -> None:
    """New game starts masked, with given lives, not won/lost."""
    g = game.Game(secret="apple", lives=3)
    assert g.masked == "_ _ _ _ _"
    assert g.lives == 3
    assert (not g.won) and (not g.lost)


def test_correct_guess_reveals_all_positions() -> None:
    """A correct guess reveals all matching letters."""
    g = game.Game("banana", lives=3)
    assert g.guess("a") == "hit"
    assert g.masked == "_ a _ a _ a"


def test_wrong_guess_costs_one_life() -> None:
    """A wrong guess decrements lives by one."""
    g = game.Game("hi", lives=2)
    assert g.guess("z") == "miss"
    assert g.lives == 1


def test_win_when_all_letters_revealed() -> None:
    """Game is won when every letter has been guessed."""
    g = game.Game("go", lives=3)
    g.guess("g")
    g.guess("o")
    assert g.won and (not g.lost)


def test_loss_when_lives_zero() -> None:
    """Game is lost when lives reach zero and it is not won."""
    g = game.Game("x", lives=1)
    g.guess("z")
    assert g.lost and (not g.won)


def test_timeout_costs_life_and_ignores_input() -> None:
    """Timeout before a guess consumes a life and ignores that guess."""
    clk = FakeClock()
    g = game.GameWithTimer(
        "abc", lives=2, seconds_per_turn=15, clock=clk
    )
    clk.advance(16)  # exceed deadline before guessing
    assert g.guess("a") == "timeout"
    assert g.lives == 1
    assert g.masked == "_ _ _"  # 'a' not applied


def test_deadline_resets_after_timeout() -> None:
    """After timeout, the deadline resets for the next turn."""
    clk = FakeClock()
    g = game.GameWithTimer(
        "abc", lives=2, seconds_per_turn=15, clock=clk
    )
    clk.advance(16)
    g.guess("a")  # timeout -> deadline reset
    clk.advance(10)
    assert g.guess("a") == "hit"  # within the new window
    assert g.masked == "a _ _"
