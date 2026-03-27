import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def american_to_implied_prob(odds: int) -> float:
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)


def better_price(new_price, current_price):
    if current_price is None:
        return True
    return new_price > current_price

def get_plays():
    games = supabase.table("games").select("*").execute().data
    bookmakers = supabase.table("bookmakers").select("*").execute().data
    odds_rows = supabase.table("odds_moneyline").select("*").execute().data

    bookmaker_map = {b["id"]: b["name"] for b in bookmakers}

    raw_plays = []

    for game in games:
        game_id = game["id"]
        home_team = game["home_team"]
        away_team = game["away_team"]

        game_odds = [row for row in odds_rows if row["game_id"] == game_id]

        if not game_odds:
            continue

        best_home_price = None
        best_home_book = None
        best_away_price = None
        best_away_book = None

        home_probs = []
        away_probs = []

        for row in game_odds:
            home_price = row["home_price_american"]
            away_price = row["away_price_american"]

            if home_price is not None:
                home_probs.append(american_to_implied_prob(home_price))
            if away_price is not None:
                away_probs.append(american_to_implied_prob(away_price))

            book_name = bookmaker_map.get(row["bookmaker_id"], "Unknown")

            if home_price is not None and better_price(home_price, best_home_price):
                best_home_price = home_price
                best_home_book = book_name

            if away_price is not None and better_price(away_price, best_away_price):
                best_away_price = away_price
                best_away_book = book_name

        if not home_probs or not away_probs:
            continue

        fair_home_prob = sum(home_probs) / len(home_probs)
        fair_away_prob = sum(away_probs) / len(away_probs)

        best_home_prob = american_to_implied_prob(best_home_price)
        best_away_prob = american_to_implied_prob(best_away_price)

        home_edge = fair_home_prob - best_home_prob
        away_edge = fair_away_prob - best_away_prob

        if home_edge >= 0.01:
            raw_plays.append({
                "tier": "ELITE",
                "game": f"{away_team} @ {home_team}",
                "team": home_team,
                "book": best_home_book,
                "price": best_home_price,
                "edge": home_edge
            })
        elif home_edge >= 0.005:
            raw_plays.append({
                "tier": "SOLID",
                "game": f"{away_team} @ {home_team}",
                "team": home_team,
                "book": best_home_book,
                "price": best_home_price,
                "edge": home_edge
            })

        if away_edge >= 0.01:
            raw_plays.append({
                "tier": "ELITE",
                "game": f"{away_team} @ {home_team}",
                "team": away_team,
                "book": best_away_book,
                "price": best_away_price,
                "edge": away_edge
            })
        elif away_edge >= 0.005:
            raw_plays.append({
                "tier": "SOLID",
                "game": f"{away_team} @ {home_team}",
                "team": away_team,
                "book": best_away_book,
                "price": best_away_price,
                "edge": away_edge
            })

    deduped = {}
    for play in raw_plays:
        key = (play["game"], play["team"])
        if key not in deduped or play["edge"] > deduped[key]["edge"]:
            deduped[key] = play

    plays = list(deduped.values())
    plays.sort(key=lambda x: x["edge"], reverse=True)
    return plays



if __name__ == "__main__":
    plays = get_plays()

    print("\n🔥 TOP VALUE PLAYS 🔥\n")

    if not plays:
        print("No elite or solid plays right now.")
    else:
        for play in plays:
            label = "🔥 ELITE PLAY" if play["tier"] == "ELITE" else "⚡ SOLID PLAY"
            print(label)
            print(play["game"])
            print(f"BET: {play['team']} at {play['book']} ({play['price']})")
            print(f"EDGE: {play['edge']:.4f}")
            print("-" * 40)
