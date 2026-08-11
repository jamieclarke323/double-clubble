from app.data_loader import Player
from app.matching import MatchResult, match_guess, normalise


def make_player(name):
    return Player(
        name=name,
        position="CB",
        years_charlton="2014",
        apps_charlton=38,
        goals_charlton=0,
        years_opponent="2010",
        apps_opponent=8,
        goals_opponent=0,
    )


def test_normalise_strips_accents_and_punctuation():
    assert normalise("Guðmundsson") == "gudmundsson"
    assert normalise("N'Guessan") == "nguessan"
    assert normalise("  Ben-Haim ") == "ben haim"


def test_exact_surname_is_correct():
    players = [make_player("Tal Ben Haim")]
    outcome = match_guess("Haim", players, set())
    assert outcome.result == MatchResult.CORRECT
    assert outcome.player_index == 0


def test_multi_word_surname_accepted_in_full():
    players = [make_player("Tal Ben Haim")]
    outcome = match_guess("Ben Haim", players, set())
    assert outcome.result == MatchResult.CORRECT


def test_full_name_also_accepted():
    players = [make_player("Jóhann Berg Guðmundsson")]
    outcome = match_guess("Johann Berg Gudmundsson", players, set())
    assert outcome.result == MatchResult.CORRECT


def test_minor_misspelling_is_close():
    players = [make_player("Jóhann Berg Guðmundsson")]
    outcome = match_guess("Gudmunson", players, set())
    assert outcome.result == MatchResult.CLOSE
    assert outcome.player_index == 0


def test_unrelated_guess_is_wrong():
    players = [make_player("Tal Ben Haim"), make_player("Darren Bent")]
    outcome = match_guess("Zzzxxqq", players, set())
    assert outcome.result == MatchResult.WRONG


def test_already_solved_players_are_skipped():
    players = [make_player("Darren Bent")]
    outcome = match_guess("Bent", players, solved_indices={0})
    assert outcome.result == MatchResult.WRONG


def test_short_guesses_never_match():
    players = [make_player("Bent")]
    outcome = match_guess("be", players, set())
    assert outcome.result == MatchResult.WRONG
