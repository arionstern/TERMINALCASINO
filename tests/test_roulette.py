from casino.accounts import Account
from casino.config import Config
from casino.games.roulette import roulette as roulette_module
from casino.games.roulette.roulette import AmericanRoulette, play_roulette
from casino.types import GameContext


def make_roulette(balance=100):
    account = Account.generate('test', balance)
    return AmericanRoulette([account]), account


def place_bet(roulette, account, bet_type, bet_value, amount):
    """Places a bet the same way submit_bets() does, without user input"""
    account.withdraw(amount)
    roulette.bets[str(account.aid)] = {
        "type": bet_type,
        "value": bet_value,
        "amount": amount
    }


def test_stats_start_empty():
    """
    Tests that a new game starts with empty stats and the player's balance
    """
    roulette, _ = make_roulette(250)
    assert roulette.stats.game_name == "Roulette (U.S.)"
    assert roulette.stats.starting_balance == 250
    assert roulette.stats.rounds_played == 0
    assert roulette.stats.wins == 0
    assert roulette.stats.losses == 0


def test_stats_win():
    """
    Tests that a winning bet is counted as a win
    """
    roulette, account = make_roulette()
    place_bet(roulette, account, "number", "7", 10)
    roulette.winning_value = ("7", "red", 4, 29)
    roulette.payout()
    assert roulette.stats.rounds_played == 1
    assert roulette.stats.wins == 1
    assert roulette.stats.losses == 0


def test_stats_loss():
    """
    Tests that a losing bet is counted as a loss
    """
    roulette, account = make_roulette()
    place_bet(roulette, account, "color", "black", 10)
    roulette.winning_value = ("7", "red", 4, 29)
    roulette.payout()
    assert roulette.stats.rounds_played == 1
    assert roulette.stats.wins == 0
    assert roulette.stats.losses == 1


def test_stats_multiple_rounds():
    """
    Tests that stats carry over between rounds and that a round with no bet
    is not counted
    """
    roulette, account = make_roulette()
    place_bet(roulette, account, "color", "red", 10)
    roulette.winning_value = ("7", "red", 4, 29)
    roulette.payout()

    roulette.reset_round()
    place_bet(roulette, account, "number", "00", 10)
    roulette.winning_value = ("7", "red", 4, 29)
    roulette.payout()

    #Player skipped betting this round
    roulette.reset_round()
    roulette.winning_value = ("7", "red", 4, 29)
    roulette.payout()

    assert roulette.stats.rounds_played == 2
    assert roulette.stats.wins == 1
    assert roulette.stats.losses == 1
    assert roulette.stats.win_rate == "50.0%"


def test_stats_displayed_on_quit(monkeypatch):
    """
    Tests that the postgame stats are shown when the player quits
    """
    shown = []
    monkeypatch.setattr(roulette_module, "cinput", lambda *args, **kwargs: "q")
    monkeypatch.setattr(roulette_module, "display_stats", shown.append)

    ctx = GameContext(account=Account.generate('test', 100), config=Config.default())
    play_roulette(ctx)

    assert len(shown) == 1
    assert shown[0].starting_balance == 100
    assert shown[0].ending_balance == 100
    assert shown[0].net == 0
