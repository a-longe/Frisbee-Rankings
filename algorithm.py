from math import sin, pi
import pandas as pd
import datetime

INITIAL_RATING = 1000.0

CONVERGANCE_THRESHOLD = 0.1


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
    jan_1 = datetime.date(year=1900, month=1, day=1) # 1900 is default year
    game_date = datetime.datetime.strptime(game["Date String"], "%B %d").date()
    if (game_date - datetime.date(year=1900, month=6, day=1)).days > 0:
        # pre-pre season games
        return 0.5
    c = 2**(1/13)
    return 0.5 * c**((game_date - jan_1).days // 7)


def get_score_weight(game: list) -> float:
    score: tuple[str, str] = game["Score(F,A)"].strip('()').replace("'", '').split(',')
    try:
        score_for = int(score[0])
    except ValueError:
        # int casting failed
        score_for = 0
    try:
        score_against = int(score[1])
    except ValueError:
        score_against = 0
    if score_for >= 13 or score_against >= 13 or \
        score_for + score_against >= 19:
        return 1
    winning_score = max(score_for, score_against)
    loosing_score = min(score_for, score_against)

    return ((winning_score + max(loosing_score, (winning_score-1)//2))
            /19)**0.5


def get_rating_diff(game: list) -> float:
    score: tuple[str, str] = game["Score(F,A)"].strip('()').replace("'", '').split(',')
    try:
        winning_score = max(int(score[0]), int(score[1]))
    except ValueError:
        # int conversion failed
        winning_score = 0

    try:
        loosing_score = min(int(score[0]), int(score[1]))
    except ValueError:
        # int conversion failed
        loosing_score = 0

    if winning_score-1 != 0:
        r = loosing_score/(winning_score-1)
    else:
        r = 0
    return 125 + 475*(sin(min(1, ((1-r)/5))*0.4*pi) / sin(0.4*pi))


def compute_iteration(ratings: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """
    compute iteration
    First, update the rating diff of each game, then average out and update the
    team rating.
    """
    teams = set(ratings.get("Team Name").to_list())

    for team in teams:
        # filter to only games with this team, update rating diff
        ratings.loc[ratings["Team Name"] == team, "game_rating"] = \
            ratings.apply(lambda row : row["team_rating"] + get_rating_diff(row), axis=1)

    # update team ratings
    max_change = 0.0
    for team in teams:
        # filter to only games with this team, sum ratings
        sum_rating = 0
        for game in ratings.query(f'`Team Name` == "{team}"').itertuples():
            sum_rating += float(game.date_weight) \
                * float(game.score_weight) \
                * float(game.game_rating)

        avg_rating = sum_rating / len(ratings.query(f'`Team Name` == "{team}"'))
        for game in ratings.query(f'`Team Name` == "{team}"').itertuples():
            max_change = max(max_change, abs(float(game.team_rating) - avg_rating))
            ratings.loc[game[0], "team_rating"] = avg_rating

    return (ratings, max_change)


def get_initial_ratings(games: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """
    takes in game, finds all teams, give each time initial rating of 1000
    """
    games["team_rating"] = INITIAL_RATING
    games["game_rating"] = games.apply(lambda row : INITIAL_RATING + get_rating_diff(row), axis=1)
    games["date_weight"] = games.apply(lambda row : get_date_weight(row), axis=1)
    games["score_weight"] = games.apply(lambda row : get_score_weight(row), axis=1)
    games["game_effect"] = 0
    return games, 1000 # arbirarly large number, has not converged


def has_converged(max_change: float) -> bool:
    return max_change < CONVERGANCE_THRESHOLD


def compute_ratings(games: pd.DataFrame) -> pd.DataFrame:
    """
    update ratings until they converge
    """
    iter_count = 0
    initial, _ = get_initial_ratings(games)
    print("Computed Initial Ratings")
    cur_iter, max_change = compute_iteration(initial)
    while not has_converged(max_change):
        print(f"Computed Iteration {iter_count}, Max Change was {max_change}")
        cur_iter, max_change = compute_iteration(cur_iter)
        iter_count+=1

    print(f"Completed Convergence Iterations after {iter_count} iterations")
    print(f"Final Maximum change was {max_change}")

    return cur_iter


def get_2025_ratings() -> pd.DataFrame:
    games = pd.read_csv("2025season.csv")
    games = games.drop(columns=["Unnamed: 0"]) # get rid of extra index col
    print("Loaded 2025 Season")
    ratings = compute_ratings(games)
    return ratings

