from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_PATH = "C:/Users/adity/OneDrive/Desktop/CrickStatX/datasets"

datasets = {}

def calculate_career_length(span_str):
    try:
        years = span_str.split("-")
        if len(years) == 2:
            return int(years[1]) - int(years[0])
    except:
        return None
    return None

TEAM_MAP = {
    "INDIA": "India", "AUS": "Australia", "PAK": "Pakistan", "ENG": "England",
    "RSA": "South Africa", "SA": "South Africa", "NZ": "New Zealand",
    "SL": "Sri Lanka", "BDESH": "Bangladesh", "WI": "West Indies", "WIND": "West Indies",
    "AFG": "Afghanistan", "IRE": "Ireland", "NL": "Netherlands","SCOT": "Scotland" ,"KENYA": "Kenya",
    "CAN": "Canada", "NAM": "Namibia", "UAE": "United Arab Emirates",
    "HKG": "Hong Kong", "NEPAL": "Nepal",
    "ASIA": "Asia XI", "AFR": "Africa XI", "ICC": "ICC World XI", "EAF": "East Africa XI",
    "WORLD": "World XI", "AMERICAS": "Americas XI"
}

def extract_teams_played(player_name: str):
    match = re.search(r"\((.*?)\)", player_name or "")
    if not match:
        return None
    
    raw_teams = match.group(1).split("/")
    teams = []
    for team in raw_teams:
        team = team.strip()
        up = team.upper()
        # Map to full country name if available
        if up in TEAM_MAP:
            teams.insert(0,TEAM_MAP[up])
        else:
            teams.append(team.title())  # fallback
    
    return ", ".join(teams)


def clean_player_name(player_name):
    return re.sub(r"\s*\(.*?\)", "", player_name).strip()

def load_all_datasets():
    for category in ["Batting", "Bowling", "Fielding"]:
        category_path = os.path.join(BASE_PATH, category)
        datasets[category] = {}
        for file in os.listdir(category_path):
            if file.endswith(".csv"):
                file_path = os.path.join(category_path, file)
                try:
                    df = pd.read_csv(file_path)

                    # Drop all 'Unnamed' columns
                    df = df.loc[:, ~df.columns.str.startswith('Unnamed')]

                    # Drop exact duplicate rows
                    df.drop_duplicates(inplace=True)

                    # Add CareerLength
                    if "Span" in df.columns:
                        df["CareerLength"] = df["Span"].apply(calculate_career_length)

                    # Extract Teams and Clean Player Name
                    if "Player" in df.columns:
                        df["Teams"] = df["Player"].apply(extract_teams_played)
                        df["Player"] = df["Player"].apply(clean_player_name)

                    datasets[category][file] = df
                except Exception as e:
                    print(f"Error loading {file}: {e}")

load_all_datasets()

def to_json(df):
    return json.loads(df.to_json(orient="records"))

@app.get("/")
def home():
    return {"message": "CrickStatX API is live!"}

@app.get("/available-files")
def list_files():
    all_files = []
    for category in ["Batting", "Bowling", "Fielding"]:
        folder = os.path.join(BASE_PATH, category)
        if os.path.exists(folder):
            for file in os.listdir(folder):
                if file.endswith(".csv"):
                    all_files.append(f"{category}/{file}")
    return {"available_files": all_files}

@app.get("/players")
def get_all_players():
    player_set = set()
    for category_files in datasets.values():
        for df in category_files.values():
            if "Player" in df.columns:
                player_set.update(df["Player"].dropna().str.strip().str.title().unique())
    return sorted([p for p in player_set if p])

@app.get("/player-profile")
def get_player_profile(player_name: str = Query(..., description="Full name, initials and surname, or just a letter")):
    player_name = player_name.strip().lower()
    result = {}

    for category, files in datasets.items():
        result[category] = {}
        for filename, df in files.items():
            if "Player" in df.columns:
                df["lower_name"] = df["Player"].str.lower()
                df["surname"] = df["Player"].apply(lambda x: x.lower().split()[-1] if isinstance(x, str) else "")
                df["short_code"] = df["Player"].apply(
                    lambda x: f"{x.strip().split()[0][0].lower()} {x.lower().split()[-1]}"
                    if isinstance(x, str) and len(x.strip().split()) >= 2 else "")
                df["initial"] = df["Player"].apply(lambda x: x.strip()[0].lower() if isinstance(x, str) else "")

                if " " in player_name:
                    matched_df = df[(df["short_code"] == player_name) | (df["lower_name"] == player_name)]
                elif len(player_name) == 1:
                    matched_df = df[df["initial"] == player_name]
                else:
                    matched_df = df[df["surname"] == player_name]

                if not matched_df.empty:
                    cleaned = matched_df.drop(columns=["lower_name", "surname", "short_code", "initial"])
                    # Remove any columns with all 0 values
                    cleaned = cleaned.applymap(lambda x: None if str(x).isdigit() and int(x) == 0 else x).dropna(axis=1, how="all")
                    result[category][filename] = to_json(cleaned)

    if all(len(files) == 0 for files in result.values()):
        return {"message": f"No data found for player: {player_name.title()}"}

    return {
        "player": player_name.title(),
        "profile": result
    }


@app.get("/analyze")
def analyze_player(player_name: str = Query(..., description="Search by full name, short form like 's tendulkar', or just 's'")):
    player_name = player_name.strip().lower()
    summary_by_player = {}

    for category, files in datasets.items():
        for filename, df in files.items():
            if "Player" not in df.columns:
                continue

            df["lower_name"] = df["Player"].str.lower()
            df["surname"] = df["Player"].apply(lambda x: x.lower().split()[-1] if isinstance(x, str) else "")
            df["short_code"] = df["Player"].apply(
                lambda x: f"{x.strip().split()[0][0].lower()} {x.lower().split()[-1]}"
                if isinstance(x, str) and len(x.strip().split()) >= 2 else ""
            )
            df["initial"] = df["Player"].apply(lambda x: x.strip()[0].lower() if isinstance(x, str) else "")

            if " " in player_name:
                matched_df = df[(df["short_code"] == player_name) | (df["lower_name"] == player_name)]
            elif len(player_name) == 1:
                matched_df = df[df["initial"] == player_name]
            else:
                matched_df = df[df["surname"] == player_name]

            for _, row in matched_df.iterrows():
                player = row["Player"]
                if player not in summary_by_player:
                    summary_by_player[player] = {
                        "Batting": [],
                        "Bowling": [],
                        "Fielding": [],
                        "CareerLength": row.get("CareerLength"),
                        "Teams": row.get("Teams"),
                    }
                summary_by_player[player][category].append(dict(row))

    if not summary_by_player:
        return {"message": f"No player found for '{player_name}'"}

    final_output = []

    for player, sections in summary_by_player.items():
        batting, bowling, fielding = sections.get("Batting", []), sections.get("Bowling", []), sections.get("Fielding", [])
        teams = sections.get("Teams", "N/A")
        career = sections.get("CareerLength", "N/A")

        def valid(val): return str(val).isdigit() and int(val) > 0

        total_runs = sum(int(r["Runs"]) for r in batting if valid(r.get("Runs")))
        total_4s = sum(int(r["4s"]) for r in batting if valid(r.get("4s")))
        total_6s = sum(int(r["6s"]) for r in batting if valid(r.get("6s")))
        innings = sum(int(r["Inns"]) for r in batting if valid(r.get("Inns")))

        total_wickets = sum(int(r["Wkts"]) for r in bowling if valid(r.get("Wkts")))
        four_wkts = sum(int(r["4"]) for r in bowling if valid(r.get("4")))
        five_wkts = sum(int(r["5"]) for r in bowling if valid(r.get("5")))
        ten_wkts = sum(int(r["10"]) for r in bowling if valid(r.get("10")))

        total_dismissals = sum(int(r["Dis"]) for r in fielding if valid(r.get("Dis")))
        total_catches = sum(int(r["Ct"]) for r in fielding if valid(r.get("Ct")))
        total_stumpings = sum(int(r["St"]) for r in fielding if valid(r.get("St")))

        is_batsman = total_runs > 1000 and total_wickets < 50
        is_bowler = total_wickets > 100 and total_runs < 1000
        is_allrounder = total_runs > 1000 and total_wickets > 50

        lines = [f"{player} represented {teams} for {career} years in international cricket across various formats."]

        if is_batsman:
            line = f"🏏 A remarkable batsman, he"
            if total_runs: line += f" scored over {total_runs} runs"
            if innings: line += f" in {innings} innings"
            line += "."
            if total_4s: line += f" He struck {total_4s} boundaries"
            if total_6s: line += f" and {total_6s} sixes"
            line += ". His consistency made him a pillar in his batting lineup."
            lines.append(line)

        elif is_bowler:
            line = f"🔥 A lethal bowler, he"
            if total_wickets: line += f" claimed over {total_wickets} wickets"
            if four_wkts: line += f" with {four_wkts} four-wicket hauls"
            if five_wkts: line += f", {five_wkts} five-wicket hauls"
            if ten_wkts: line += f", and {ten_wkts} ten-wicket hauls"
            line += ". His economy and average made him a threat for batters."
            lines.append(line)

        elif is_allrounder:
            line = f"⭐ An excellent all-rounder, he"
            if total_runs: line += f" accumulated {total_runs} runs"
            if total_wickets: line += f" and took {total_wickets} wickets"
            haul_parts = []
            if four_wkts: haul_parts.append(f"{four_wkts} four-wicket hauls")
            if five_wkts: haul_parts.append(f"{five_wkts} five-wicket hauls")
            if ten_wkts: haul_parts.append(f"{ten_wkts} ten-wicket match hauls")
            if haul_parts:
                line += ". His bowling included " + ", ".join(haul_parts) + "."
            line += " His performance in both departments contributed equally to his team's success."
            lines.append(line)

        else:
            lines.append("While his numbers aren't exceptional in batting or bowling alone, his utility as a team player was valuable.")

        if fielding:
            if total_stumpings > 0:
                lines.append(f"🧤 His fielding record includes {total_dismissals} dismissals, {total_catches} catches and {total_stumpings} stumpings.")
            elif total_catches > 0:
                lines.append(f"⚡ In the field, he contributed {total_catches} catches, showcasing his alertness.")

        final_output.append({
            "player": player,
            "summary": " ".join(lines)
        })

    return final_output

@app.get("/tags")
def generate_tags(player_name: str = Query(..., description="Search by full name, initials + surname, surname, or just a letter")):
    player_name = player_name.strip().lower()
    tags_by_player = {}

    for category, files in datasets.items():
        for filename, df in files.items():
            if "Player" not in df.columns:
                continue

            # Create helper columns
            df["lower_name"] = df["Player"].str.lower()
            df["surname"] = df["Player"].apply(lambda x: x.lower().split()[-1] if isinstance(x, str) else "")
            df["short_code"] = df["Player"].apply(
                lambda x: f"{x.strip().split()[0][0].lower()} {x.lower().split()[-1]}"
                if isinstance(x, str) and len(x.strip().split()) >= 2 else "")
            df["initial"] = df["Player"].apply(lambda x: x.strip()[0].lower() if isinstance(x, str) else "")

            # Matching logic
            if " " in player_name:
                matched_df = df[(df["short_code"] == player_name) | (df["lower_name"] == player_name)]
            elif len(player_name) == 1:
                matched_df = df[df["initial"] == player_name]
            else:
                matched_df = df[df["surname"] == player_name]

            # Collect data by player
            for _, row in matched_df.iterrows():
                player = row["Player"]
                if player not in tags_by_player:
                    tags_by_player[player] = {
                        "Batting": [],
                        "Bowling": [],
                        "Fielding": [],
                        "FormatScores": {"Test": 0, "ODI": 0, "T20": 0}
                    }

                # Organize data by category
                if category == "Batting":
                    tags_by_player[player]["Batting"].append(row)
                elif category == "Bowling":
                    tags_by_player[player]["Bowling"].append(row)
                elif category == "Fielding":
                    tags_by_player[player]["Fielding"].append(row)

                # Format name for performance comparison
                format_key = ""
                if "test" in filename.lower():
                    format_key = "Test"
                elif "odi" in filename.lower():
                    format_key = "ODI"
                elif "t20" in filename.lower():
                    format_key = "T20"
                else:
                    continue

                # Add performance score to format
                def valid(val): return str(val).replace(".", "", 1).isdigit() and float(val) > 0
                score = 0
                if category == "Batting" and valid(row.get("Runs")):
                    score += int(row["Runs"])
                if category == "Bowling" and valid(row.get("Wkts")):
                    score += int(row["Wkts"]) * 20
                if category == "Fielding" and valid(row.get("Dis")):
                    score += int(row["Dis"]) * 10

                tags_by_player[player]["FormatScores"][format_key] += score

    if not tags_by_player:
        return {"message": f"No player found for '{player_name}'"}

    # Generate tags per player
    final_tags = []

    for player, data in tags_by_player.items():
        batting = data["Batting"]
        bowling = data["Bowling"]
        fielding = data["Fielding"]
        format_scores = data["FormatScores"]

        # Totals
        def valid(val): return str(val).replace(".", "", 1).isdigit() and float(val) > 0
        total_runs = sum(int(r["Runs"]) for r in batting if valid(r.get("Runs")))
        total_wkts = sum(int(r["Wkts"]) for r in bowling if valid(r.get("Wkts")))
        total_stumps = sum(int(r["St"]) for r in fielding if valid(r.get("St")))

        # Role Tag
        if total_stumps > 1:
            role_tag = " Wicketkeeper Batter 🧤"
        elif total_runs > 1000 and total_wkts >= 50:
            role_tag = " Spirited All-Rounder ⚔️"
        elif total_runs > 1000:
            role_tag = " Dependable Batsman 🏏"
        elif total_wkts >= 100:
            role_tag = " Ferocious Bowler 🎯"
        else:
            role_tag = "Versatile Team Player 🔁"

        # Format Tag (best performing format)
        best_format = max(format_scores.items(), key=lambda x: x[1])[0]
        format_tag = (
            "Test Veteran 🛡️" if best_format == "Test" else
            "ODI Performer 🔥" if best_format == "ODI" else
            "T20 Specialist 💪"
        )


        tags = []
        if role_tag:
            tags.append(role_tag)
        tags.append(format_tag)

        final_tags.append({
            "player": player,
            "tags": tags
        })

    return final_tags

@app.get("/compare")
def compare_players(players: str = Query(..., description="Comma-separated list of TWO player names or short codes")):
    player_names = [p.strip().lower() for p in players.split(",") if p.strip()]
    if len(player_names) != 2:
        return {"error": "Please provide exactly TWO players for comparison."}

    comparison_data = {}

    def valid(val):
        return str(val).replace(".", "", 1).isdigit() and float(val) > 0

    # Process datasets
    for category, files in datasets.items():
        for filename, df in files.items():
            if "Player" not in df.columns:
                continue

            # Prepare search helpers
            df["lower_name"] = df["Player"].str.lower()
            df["surname"] = df["Player"].apply(lambda x: x.lower().split()[-1] if isinstance(x, str) else "")
            df["short_code"] = df["Player"].apply(
                lambda x: f"{x.strip().split()[0][0].lower()} {x.lower().split()[-1]}"
                if isinstance(x, str) and len(x.strip().split()) >= 2 else ""
            )
            df["initial"] = df["Player"].apply(lambda x: x.strip()[0].lower() if isinstance(x, str) else "")

            # Detect format
            if "test" in filename.lower():
                fmt = "Test"
            elif "odi" in filename.lower():
                fmt = "ODI"
            elif "t20" in filename.lower():
                fmt = "T20"
            else:
                continue

            for pname in player_names:
                if " " in pname:
                    matched_df = df[(df["short_code"] == pname) | (df["lower_name"] == pname)]
                elif len(pname) == 1:
                    matched_df = df[df["initial"] == pname]
                else:
                    matched_df = df[df["surname"] == pname]

                for _, row in matched_df.iterrows():
                    player = row["Player"]
                    if player not in comparison_data:
                        comparison_data[player] = {
                            "Batting": {}, "Bowling": {}, "Fielding": {}
                        }

                    if category == "Batting":
                        if fmt not in comparison_data[player]["Batting"]:
                            comparison_data[player]["Batting"][fmt] = {}
                        for col in ["Mat", "Inns", "Runs", "Ave", "SR", "100", "50", "4s", "6s"]:
                            if col in row and valid(row[col]):
                                comparison_data[player]["Batting"][fmt][col] = row[col]

                    elif category == "Bowling":
                        if fmt not in comparison_data[player]["Bowling"]:
                            comparison_data[player]["Bowling"][fmt] = {}
                        for col in ["Mat", "Inns", "Wkts", "Econ", "Ave", "SR", "4", "5", "10"]:
                            if col in row and valid(row[col]):
                                comparison_data[player]["Bowling"][fmt][col] = row[col]

                    elif category == "Fielding":
                        if fmt not in comparison_data[player]["Fielding"]:
                            comparison_data[player]["Fielding"][fmt] = {}
                        for col in ["Mat", "Inns", "Dis", "Ct", "St"]:
                            if col in row and valid(row[col]):
                                comparison_data[player]["Fielding"][fmt][col] = row[col]

    if not comparison_data:
        return {"message": "No matching players found."}

    final_comparison = {
        "players": list(comparison_data.keys()),
        "comparison": {"Batting": {}, "Bowling": {}, "Fielding": {}},
        "winner_summary": {}
    }

    # Detect WK logic
    both_wk = True
    for p in comparison_data:
        st_sum = sum(int(v) for fmt in comparison_data[p]["Fielding"].values() for k, v in fmt.items() if k == "St" and valid(v))
        if st_sum == 0:
            both_wk = False
            break

    # Ct & Dis display control
    show_ct = True
    show_dis = True
    if not both_wk:
        p1_ct = sum(int(v) for fmt in comparison_data[list(comparison_data.keys())[0]]["Fielding"].values() for k, v in fmt.items() if k == "Ct" and valid(v))
        p1_dis = sum(int(v) for fmt in comparison_data[list(comparison_data.keys())[0]]["Fielding"].values() for k, v in fmt.items() if k == "Dis" and valid(v))
        p2_ct = sum(int(v) for fmt in comparison_data[list(comparison_data.keys())[1]]["Fielding"].values() for k, v in fmt.items() if k == "Ct" and valid(v))
        p2_dis = sum(int(v) for fmt in comparison_data[list(comparison_data.keys())[1]]["Fielding"].values() for k, v in fmt.items() if k == "Dis" and valid(v))

        if p1_ct == p1_dis and p2_ct == p2_dis:
            # Only show Dis if Ct & Dis are equal for both players
            show_ct = False
            show_dis = True

    # Build comparison table
    for role in ["Batting", "Bowling", "Fielding"]:
        for fmt in ["Test", "ODI", "T20"]:
            stats_set = set()
            for player in comparison_data:
                if fmt in comparison_data[player][role]:
                    stats_set.update(comparison_data[player][role][fmt].keys())

            for stat in stats_set:
                if stat == "St" and not both_wk:
                    continue
                if stat == "Ct" and not show_ct:
                    continue
                if stat == "Dis" and not show_dis:
                    continue
                if all(fmt in comparison_data[p][role] and stat in comparison_data[p][role][fmt] for p in comparison_data):
                    if fmt not in final_comparison["comparison"][role]:
                        final_comparison["comparison"][role][fmt] = {}
                    final_comparison["comparison"][role][fmt][stat] = {
                        p: comparison_data[p][role][fmt][stat] for p in comparison_data
                    }

    # Winner calculation
    player_scores = {p: 0 for p in comparison_data}
    player_roles = {}
    for player, pdata in comparison_data.items():
        runs = sum(int(v) for fmt in pdata["Batting"].values() for k, v in fmt.items() if k == "Runs" and valid(v))
        wkts = sum(int(v) for fmt in pdata["Bowling"].values() for k, v in fmt.items() if k == "Wkts" and valid(v))
        dismissals = sum(int(v) for fmt in pdata["Fielding"].values() for k, v in fmt.items() if k in ["Dis", "Ct", "St"] and valid(v))

        # Assign role
        if sum(int(v) for fmt in pdata["Fielding"].values() for k, v in fmt.items() if k == "St" and valid(v)) > 0:
            player_roles[player] = "wk"
        elif runs > 1000 and wkts >= 50:
            player_roles[player] = "allrounder"
        elif wkts >= 100:
            player_roles[player] = "bowler"
        else:
            player_roles[player] = "batsman"

        player_scores[player] = runs + (wkts * 20) + (dismissals * 10)

    winner = max(player_scores.items(), key=lambda x: x[1])[0]
    loser = [p for p in player_scores if p != winner][0]

    # Winner stats
    winner_runs = sum(int(v) for fmt in comparison_data[winner]["Batting"].values() for k, v in fmt.items() if k == "Runs" and valid(v))
    winner_wkts = sum(int(v) for fmt in comparison_data[winner]["Bowling"].values() for k, v in fmt.items() if k == "Wkts" and valid(v))
    winner_stumps = sum(int(v) for fmt in comparison_data[winner]["Fielding"].values() for k, v in fmt.items() if k == "St" and valid(v))
    winner_catches = sum(int(v) for fmt in comparison_data[winner]["Fielding"].values() for k, v in fmt.items() if k == "Ct" and valid(v))

    # Winner summary (unchanged from your given one, with emojis)
    if player_roles[winner] == "wk":
        summary_text = (f"🧤 {winner} emerged as the stronger player in this comparison, excelling as a wicketkeeper-batter. "
                        f"Across all formats, he recorded {winner_runs} runs and {winner_catches + winner_stumps} total dismissals, "
                        f"including {winner_stumps} stumpings and {winner_catches} catches. His performance behind the stumps "
                        f"was equally matched by consistent contributions with the bat, making him invaluable in multiple match situations. "
                        f"In comparison, {loser} a talented player but could not match his balanced excellence. The combination of batting stability and "
                        f"sharp wicketkeeping gives {winner} a decisive edge across formats, proving his adaptability and dominance.")
    elif player_roles[winner] == "allrounder":
        summary_text = (f"⚔️ {winner} proved to be the superior all-rounder in this matchup. He scored {winner_runs} runs "
                        f"and claimed {winner_wkts} wickets across formats, showing dominance with both bat and ball. "
                        f"His ability to shift momentum in matches with either bat or bowl made a huge difference. "
                        f"{loser}, while talented, could not match the same all-round impact. {winner}’s dual skills "
                        f"set him apart, delivering consistent match-winning performances in a variety of conditions.")
    elif player_roles[winner] == "bowler":
        summary_text = (f"🎯 {winner} stood out as the more effective bowler, claiming {winner_wkts} wickets across formats. "
                        f"His ability to break partnerships and maintain control over run flow tilted the balance in his favor. "
                        f"While {loser} had his moments, {winner}’s dominance with the ball ensured he had the upper hand "
                        f"throughout this comparison, proving his value as a strike bowler.")
    else:
        summary_text = (f"🏏 {winner} outshined {loser} in batting performance, amassing {winner_runs} runs across all formats. "
                        f"His ability to consistently score and anchor innings proved decisive. "
                        f"{loser} fell short in maintaining the same level of batting impact, "
                        f"making {winner} the more reliable and productive batter overall.")

    final_comparison["winner_summary"] = {
        "winner": winner,
        "summary": summary_text
    }

    return final_comparison

@app.get("/top-performers")
def top_performers(format: str = Query(..., description="Format: test, odi, t20"),
                   role: str = Query(..., description="Role: batsman, bowler, allrounder, wk"),
                   limit: int = Query(10, description="Number of players to return")):
    format = format.lower()
    role = role.lower()
    
    # Map role to dataset
    if role == "batsman":
        file_map = {"test": "Batting/test.csv", "odi": "Batting/ODI data.csv", "t20": "Batting/t20.csv"}
    elif role == "bowler":
        file_map = {"test": "Bowling/Bowling_test.csv", "odi": "Bowling/Bowling_ODI.csv", "t20": "Bowling/Bowling_t20.csv"}
    elif role == "wk":
        file_map = {"test": "Fielding/Fielding_test.csv", "odi": "Fielding/Fielding_ODI.csv", "t20": "Fielding/Fielding_t20.csv"}
    elif role == "allrounder":
        file_map = {
            "test": ("Batting/test.csv", "Bowling/Bowling_test.csv"),
            "odi": ("Batting/ODI data.csv", "Bowling/Bowling_ODI.csv"),
            "t20": ("Batting/t20.csv", "Bowling/Bowling_t20.csv")
        }
    else:
        return {"error": "Invalid role. Choose from batsman, bowler, allrounder, wk"}

    result = []

    # BATSMAN 
    if role == "batsman":
        file = file_map[format]
        df = datasets["Batting"][file.split("/")[-1]].copy()

        df = df[df["Runs"].apply(lambda x: str(x).isdigit())]
        df["Runs"] = df["Runs"].astype(int)

        sorted_df = df.sort_values(by="Runs", ascending=False).head(limit)

        cols = [c for c in ["Player","Teams","Mat", "Inns", "Runs", "Ave", "SR", "50", "100", "HS"] if c in df.columns]
        result = sorted_df[cols].to_dict(orient="records")

    # BOWLER
    elif role == "bowler":
        file = file_map[format]
        df = datasets["Bowling"][file.split("/")[-1]].copy()

        df = df[df["Wkts"].apply(lambda x: str(x).isdigit())]
        df["Wkts"] = df["Wkts"].astype(int)

        sorted_df = df.sort_values(by="Wkts", ascending=False).head(limit)

        cols = [c for c in ["Player","Teams","Mat", "Inns", "Wkts", "Econ", "Ave", "SR", "5", "10" ,"BBI"] if c in df.columns]
        result = sorted_df[cols].to_dict(orient="records")

    # WK 
    elif role == "wk":
        file = file_map[format]
        fld = datasets["Fielding"][file.split("/")[-1]].copy()
        fld = fld[fld["St"].apply(lambda x: str(x).isdigit())].copy()
        fld["St"] = fld["St"].astype(int)
        if "Dis" in fld.columns:
            fld["Dis"] = fld["Dis"].astype(int)
        sorted_fld = fld.sort_values(by=["St", "Dis"], ascending=False).head(limit)

        bat_file = {"test": "Batting/test.csv", "odi": "Batting/ODI data.csv", "t20": "Batting/t20.csv"}[format]
        bat = datasets["Batting"][bat_file.split("/")[-1]].copy()
        if "Runs" in bat.columns:
            bat = bat[bat["Runs"].apply(lambda x: str(x).isdigit())].copy()
            bat["Runs"] = bat["Runs"].astype(int)

        bat_cols = ["Player", "Teams"]
        for c in ["Runs", "SR", "100", "50", "Ave", "HS", "D/I"]:
            if c in bat.columns:
                bat_cols.append(c)
        bat = bat[bat_cols]

        merged = pd.merge(sorted_fld, bat, on="Player", how="left")

        if "Teams_x" in merged.columns or "Teams_y" in merged.columns:
            merged["Teams"] = merged.get("Teams_x", "").fillna("")
            merged.loc[(merged["Teams"] == "") & merged.get("Teams_y").notna(), "Teams"] = merged["Teams_y"]
            merged.drop(columns=[c for c in ["Teams_x", "Teams_y"] if c in merged.columns], inplace=True)

        cols = [c for c in ["Player", "Teams", "Mat", "Runs", "St", "Ct", "D/I", "Ave", "SR", "50", "100", "HS"] if c in merged.columns]
        result = merged[cols].to_dict(orient="records")

    # ALLROUNDER 
    elif role == "allrounder":
        bat_file, bowl_file = file_map[format]
        batting_df = datasets["Batting"][bat_file.split("/")[-1]].copy()
        bowling_df = datasets["Bowling"][bowl_file.split("/")[-1]].copy()

        bat_cols = ["Teams","Player", "Runs", "Ave","50","100","HS"]
        if "SR" in batting_df.columns:
            bat_cols.append("SR")
        bat_df = batting_df[bat_cols]

        bowl_cols = ["Player", "Wkts"]
        if "Econ" in bowling_df.columns:
            bowl_cols.append("Econ")
        if "5" in bowling_df.columns:
            bowl_cols.append("5")
        if "10" in bowling_df.columns:
            bowl_cols.append("10")
        bowl_df = bowling_df[bowl_cols]

        bat_df = bat_df[bat_df["Runs"].apply(lambda x: str(x).isdigit())].copy()
        bowl_df = bowl_df[bowl_df["Wkts"].apply(lambda x: str(x).isdigit())].copy()

        bat_df["Runs"] = bat_df["Runs"].astype(int)
        bowl_df["Wkts"] = bowl_df["Wkts"].astype(int)

        merged = pd.merge(bat_df, bowl_df, on="Player", how="inner").fillna(0)
        merged = merged[(merged["Runs"] >= 1000) & (merged["Wkts"] >= 50)]
        merged["Impact"] = merged["Runs"] + merged["Wkts"]

        sorted_df = merged.sort_values(by="Impact", ascending=False).head(limit)

        cols = [c for c in ["Player","Teams","Runs","Ave","SR","50","100","Wkts","Econ","5","10","HS"] if c in sorted_df.columns]
        result = sorted_df[cols].to_dict(orient="records")

    # Fix Teams → Country and place it right after Player
    final_result = []
    for r in result:
        new_r = {}
        if "Player" in r:
            new_r["Player"] = r["Player"]

        # Extract main country (ignore special XI)
        country = None
        if "Teams" in r and r["Teams"]:
            teams_list = [t.strip() for t in r["Teams"].split(",")]
            for t in teams_list:
                if "XI" not in t.upper():
                    country = t
                    break
            if not country and teams_list:
                country = teams_list[0]

        # Add country only if found
        if country:
            new_r["Country"] = country

        # Add the rest (skipping Teams)
        for k, v in r.items():
            if k not in ["Player", "Teams"]:
                new_r[k] = v

        # Remove zero values
        new_r = {k: v for k, v in new_r.items() if str(v) not in ["0", "0.0"]}
        if len(new_r) > 1:
            final_result.append(new_r)

    return {"role": role, "format": format, "top_performers": final_result}

@app.get("/player-filter")
def player_filter(
    team: str = Query(..., description="Country name (e.g., India, Australia, Pakistan)"),
    sort_by: str = Query(None, description="Optional: 'runs', 'wkts', 'st'"),
    era: str = Query(None, description="Optional: decade like 1990s, 2000s, 2010s"),
    format: str = Query(None, description="Optional: 'test', 'odi', 't20'")
):
    team = team.strip().lower()
    players = {}

    # 🔹 Helper: check if player played in given era
    def in_era(span, era):
        if not era or not isinstance(span, str) or "-" not in span:
            return True
        try:
            start, end = map(int, span.split("-"))
            decade = int(era[:4])  # e.g. "2000s" -> 2000
            return (start <= decade + 9 and end >= decade)
        except:
            return True

    # Loop through datasets
    for category in datasets:
        for file, df in datasets[category].items():
            if "Teams" not in df.columns:
                continue

            # Apply format filter
            if format and format.lower() not in file.lower():
                continue

            # Filter by team
            mask = df["Teams"].apply(lambda x: isinstance(x, str) and team in x.lower())
            filtered = df[mask].copy()

            # Apply era filter
            if "Span" in filtered.columns and era:
                filtered = filtered[filtered["Span"].apply(lambda s: in_era(s, era))]

            for _, row in filtered.iterrows():
                name = row["Player"]
                if name not in players:
                    players[name] = {"Player": name}

                # Assign stats only if sort_by is requested
                if sort_by == "runs" and category == "Batting" and "Runs" in row and str(row["Runs"]).isdigit():
                    players[name]["Runs"] = max(players[name].get("Runs", 0), int(row["Runs"]))
                elif sort_by == "wkts" and category == "Bowling" and "Wkts" in row and str(row["Wkts"]).isdigit():
                    players[name]["Wickets"] = max(players[name].get("Wickets", 0), int(row["Wkts"]))
                elif sort_by == "st" and category == "Fielding" and "St" in row and str(row["St"]).isdigit():
                    players[name]["Stumpings"] = max(players[name].get("Stumpings", 0), int(row["St"]))

    result = list(players.values())

    # Sorting by stat if requested
    if sort_by:
        stat_key = {"runs": "Runs", "wkts": "Wickets", "st": "Stumpings"}[sort_by]
        result = sorted(result, key=lambda x: x.get(stat_key, 0), reverse=True)

        # Keep only Player and that stat + remove 0 values
        cleaned = []
        for r in result:
            if r.get(stat_key, 0) > 0:  # remove irrelevant 0 stat players
                new_r = {"Player": r["Player"]}
                new_r[stat_key] = r[stat_key]
                cleaned.append(new_r)
        result = cleaned
    else:
        # Alphabetical player names only
        result = sorted([{"Player": r["Player"]} for r in result], key=lambda x: x["Player"])

    # Build response with proper order (team → era → format → players)
    response = {"team": team.capitalize()}
    if era:
        response["era"] = era
    if format:
        response["format"] = format.lower()
    response["players"] = result  # always added last

    return response