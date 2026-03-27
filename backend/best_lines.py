import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def better_price(new_price, current_price):
    if current_price is None:
        return True
    return new_price > current_price


games_res = supabase.table("games").select("*").execute()
games = games_res.data

bookmakers_res = supabase.table("bookmakers").select("*").execute()
bookmakers = bookmakers_res.data
bookmaker_map = {b["id"]: b["name"] for b in bookmakers}

odds_res = supabase.table("odds_moneyline").select("*").execute()
odds_rows = odds_res.data

for game in games:
    game_id = game["id"]
    home_team = game["home_team"]
    away_team = game["away_team"]

    game_odds = [row for row in odds_rows if row["game_id"] == game_id]

    best_home_price = None
    best_home_book = None
    best_away_price = None
    best_away_book = None

    for row in game_odds:
        home_price = row["home_price_american"]
        away_price = row["away_price_american"]
        book_name = bookmaker_map.get(row["bookmaker_id"], "Unknown")

        if home_price is not None and better_price(home_price, best_home_price):
            best_home_price = home_price
            best_home_book = book_name

        if away_price is not None and better_price(away_price, best_away_price):
            best_away_price = away_price
            best_away_book = book_name

    print("=" * 50)
    print(f"{away_team} @ {home_team}")
    print(f"Best {home_team}: {best_home_price} at {best_home_book}")
    print(f"Best {away_team}: {best_away_price} at {best_away_book}")
