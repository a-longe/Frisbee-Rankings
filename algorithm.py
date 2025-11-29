from math import sin, pi
import pandas as pd
import datetime

GAME_DATE = 1
GAME_SCORE = 3
GAME_TEAM = 4
GAME_OPP = 5

INITIAL_RATING = 1000

def get_date_weight(game: list) -> float:
    """
    The date weight is calculated by the fact that during the first week of the
    season, the date weight is 0.5 and 1 by the end of the season.

    The algorithm details tell us that every week some constant is multiplied
    into the date weight.

    The college season is 13 weeks.

    The formula must be
    d(w) = 1/2 * c^w
    c^13 = 2
    c = 2^(1/13)
    """
    jan_1 = datetime.date(2000, 1, 1) # jan 1st 2000
    game_date = datetime.strptime(game[GAME_DATE], "%B %d").date()
    c = 2^(1/13)
    return 0.5 * c**((game_date - jan_1).days // 7)


def get_game_weight(game: list) -> float:
    score = game[GAME_SCORE]
    if int(score[0]) >= 13 or int(score[1]) >= 13 or \
        int(score[0]) + int(score[1]) >= 19:
        return 1
    winning_score = max(int(score[0]), int(score[1]))
    loosing_score = min(int(score[0]), int(score[1]))
    return ((winning_score + max(loosing_score, (winning_score-1)//2))
            /19)**0.5


def get_rating_diff(game: list) -> float:
    winning_score = max(int(score[0]), int(score[1]))
    loosing_score = min(int(score[0]), int(score[1]))
    r = loosing_score/(winning_score-1)
    return 125 + 475*(sin(min(1, ((1-r)/5))*0.4*pi) / sin(0.4*pi))


def compute_iteration(games: pd.DataFrame, cur_ratings: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """
    compute iteration
    """
    pass


def get_initial_ratings(games: pd.DataFrame) -> pd.DataFrame:
    """
    takes in game, finds all teams, give each time initial rating of 1000
    """
    teams = set(games.get("Team Name").to_list())
    init_rating_list = [[team, (0, 0), INITIAL_RATING], for team in teams]

    return pd.DataFrame(init_rating_list,\
                        columns=["Name", "Record", "Rating"])


def compute_ratings(games: pd.DataFrame) -> pd.DataFrame:
    """
    update ratings until they converge
    """
    initial = get_initial_ratings(games)
    cur_iter, complete = compute_iteration(games, initial)
    while not complete:
        cur_iter, complete = compute_iteration(games, cur_iter)

    return cur_iter


def get_2025_ratings() -> pd.DataFrame:
    games = pd.read_csv("2025season.csv")
    ratings = compute_ratings(games)
    return ratings

