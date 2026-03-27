import os
import requests
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BOOKS = [
    "draftkings",
    "fanduel",
    "betmgm",
    "bovada"
]
# MONEYLINE ODDS
url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

params = {
    "apiKey": ODDS_API_KEY,
    "regions": "us",
    "markets": "h2h",
    "oddsFormat": "american"
}

response = requests.get(url, params=params)
data = response.json()

for game in data:
    home_team = game["home_team"]
    away_team = game["away_team"]

    game_insert = supabase.table("games").insert({
        "home_team": home_team,
        "away_team": away_team,
        "game_date": game["commence_time"][:10]
    }).execute()

    game_id = game_insert.data[0]["id"]

    for bookmaker in game["bookmakers"]:
        print(bookmaker["key"])
        if bookmaker["key"] not in BOOKS:
            continue

        supabase.table("bookmakers").upsert(
            {
                "key": bookmaker["key"],
                "name": bookmaker["title"]
            },
            on_conflict="key"
        ).execute()

        bm = supabase.table("bookmakers").select("*").eq("key", bookmaker["key"]).execute()
        bookmaker_id = bm.data[0]["id"]

        market = bookmaker["markets"][0]

        home_price = None
        away_price = None

        for outcome in market["outcomes"]:
            if outcome["name"] == home_team:
                home_price = outcome["price"]
            elif outcome["name"] == away_team:
                away_price = outcome["price"]

        supabase.table("odds_moneyline").insert({
            "game_id": game_id,
            "bookmaker_id": bookmaker_id,
            "home_price_american": home_price,
            "away_price_american": away_price
        }).execute()

print("DONE LOADING ODDS")

# PLAYER PROPS
props_url = "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"

props_params = {
    "apiKey": ODDS_API_KEY,
    "regions": "us",
    "markets": "player_hits",
    "oddsFormat": "american"
}

props_response = requests.get(props_url, params=props_params)
props_data = props_response.json()

print(type(props_data))
print(props_data)

if isinstance(props_data, dict):
    print("PROPS API ERROR:", props_data)
else:
    for game in props_data:
        home_team = game["home_team"]
        away_team = game["away_team"]

        db_game = supabase.table("games").select("*").eq("home_team", home_team).eq("away_team", away_team).execute()
        if not db_game.data:
            continue

        game_id = db_game.data[0]["id"]

        for bookmaker in game["bookmakers"]:
            if bookmaker["key"] not in BOOKS:
                continue

            bm = supabase.table("bookmakers").select("*").eq("key", bookmaker["key"]).execute()
            if not bm.data:
                continue

            bookmaker_id = bm.data[0]["id"]

            for market in bookmaker["markets"]:
                grouped_props = {}

                for outcome in market["outcomes"]:
                    if "point" not in outcome:
                        continue

                    player_name = outcome.get("description")
                    side = outcome.get("name")
                    line = outcome.get("point")
                    price = outcome.get("price")

                    if not player_name or side not in ["Over", "Under"]:
                        continue

                    key = (player_name, market["key"], line)

                    if key not in grouped_props:
                        grouped_props[key] = {
                            "game_id": game_id,
                            "bookmaker_id": bookmaker_id,
                            "player_name": player_name,
                            "market": market["key"],
                            "line": line,
                            "over_price": None,
                            "under_price": None
                        }

                    if side == "Over":
                        grouped_props[key]["over_price"] = price
                    elif side == "Under":
                        grouped_props[key]["under_price"] = price

                for prop in grouped_props.values():
                    supabase.table("odds_player_props").insert(prop).execute()

    print("DONE LOADING PLAYER PROPS")
