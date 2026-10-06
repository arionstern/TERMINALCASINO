from casino.accounts import Account
from casino.config import Config
from casino.games.roulette import european_roulette as roulette_module
from casino.games.roulette.european_roulette import EuropeanRoulette, play_european_roulette
from casino.types import GameContext


def make_roulette(balance=100):
    account = Account.generate('test', balance)
    return EuropeanRoulette([account]), account


def place_bet(roulette, account, bet_type, bet_value, amount):
    """Places a bet the same way submit_bets() does, without user input"""
    account.withdraw(amount)
    roulette._save_bet(0, bet_type, bet_value, amount)


def test_stats_start_empty():
    """
    Tests that a new game starts with empty stats and the player's balance
    """
    roulette, _ = make_roulette(250)
    assert roulette.stats.game_name == "Roulette (E.U.)"
    assert roulette.stats.starting_balance == 250
    assert roulette.stats.rounds_played == 0
    assert roulette.stats.wins == 0
    assert roulette.stats.losses == 0


def test_stats_win():
    """
    Tests that winning inside and outside bets are counted as wins
    """
    roulette, account = make_roulette()
    place_bet(roulette, account, "inside_number", "32", 10)
    roulette.winning_value = ("32", "red", 0, 17)
    roulette.payout()

    roulette.reset_round()
    place_bet(roulette, account, "outside_parity", "even", 10)
    roulette.winning_value = ("32", "red", 0, 17)
    roulette.payout()

    assert roulette.stats.rounds_played == 2
    assert roulette.stats.wins == 2
    assert roulette.stats.losses == 0


def test_stats_loss():
    """
    Tests that a losing bet is counted as a loss, including outside bets on zero
    """
    roulette, account = make_roulette()
    place_bet(roulette, account, "outside_color", "black", 10)
    roulette.winning_value = ("32", "red", 0, 17)
    roulette.payout()

    roulette.reset_round()
    place_bet(roulette, account, "outside_color", "red", 10)
    roulette.winning_value = ("0", "green", 0, 14)
    roulette.payout()

    assert roulette.stats.rounds_played == 2
    assert roulette.stats.wins == 0
    assert roulette.stats.losses == 2


def test_stats_round_without_bet():
    """
    Tests that a round where the player skipped betting is not counted
    """
    roulette, _ = make_roulette()
    roulette.winning_value = ("32", "red", 0, 17)
    roulette.payout()
    assert roulette.stats.rounds_played == 0
    assert roulette.stats.win_rate == "N/A"


def test_stats_displayed_on_quit(monkeypatch):
    """
    Tests that the postgame stats are shown when the player quits
    """
    shown = []
    monkeypatch.setattr(roulette_module, "cinput", lambda *args, **kwargs: "q")
    monkeypatch.setattr(roulette_module, "display_stats", shown.append)

    ctx = GameContext(account=Account.generate('test', 100), config=Config.default())
    play_european_roulette(ctx)

    assert len(shown) == 1
    assert shown[0].starting_balance == 100
    assert shown[0].ending_balance == 100
    assert shown[0].net == 0
