import json
import requests
import os
import time
import matplotlib.pyplot as plt
from tkinter import Tk, Entry, Button, Label


class APICacher:
    def __init__(self, cache_dir="."):
        self.cache_dir = cache_dir

    def fetch_with_cache(self, url, cache_file, max_age=86400):
        cache_path = os.path.join(self.cache_dir, cache_file)
        if os.path.exists(cache_path) and (time.time() - os.path.getmtime(cache_path) < max_age):
            with open(cache_path, 'r') as f:
                return json.load(f)
        response = requests.get(url)
        data = response.json()
        with open(cache_path, 'w') as f:
            json.dump(data, f)
        return data

    def clear_cache(self):
        for file in os.listdir(self.cache_dir):
            if file.startswith("cache_"):
                os.remove(file)
        return "Cache cleared."


class DotaDataFetcher:
    def __init__(self, api_cacher):
        self.api_cacher = api_cacher
        self.base_url = "https://api.opendota.com/api"

    def fetch_match_data(self, match_id):
        if not match_id.isdigit():
            return {"error": "Please enter a valid match ID."}
        url = f"{self.base_url}/matches/{match_id}"
        return self.api_cacher.fetch_with_cache(url, f"cache_match_{match_id}.json")

    def fetch_player_win_lose_data(self, account_id):
        if not account_id.isdigit():
            return {"error": "Please enter a valid player ID"}
        url_wl = f"{self.base_url}/players/{account_id}/wl"
        return self.api_cacher.fetch_with_cache(url_wl, f"cache_wl_{account_id}.json")

    def fetch_player_profile(self, account_id):
        if not account_id.isdigit():
            return {"error": "Please enter a valid player ID"}
        url_player = f"{self.base_url}/players/{account_id}"
        return self.api_cacher.fetch_with_cache(url_player, f"cache_player_{account_id}.json")

    
    def fetch_hero_stats(self):
        url = f"{self.base_url}/heroStats"
        return self.api_cacher.fetch_with_cache(url, "cache_hero_stats.json")

    
    def fetch_recent_matches(self, account_id):
        if not account_id.isdigit():
            return {"error": "Please enter a valid player ID"}
        url = f"{self.base_url}/players/{account_id}/recentMatches"
        return self.api_cacher.fetch_with_cache(url, f"cache_recent_{account_id}.json")


class PlotBuilder:
    def __init__(self, hero_names_dict, hero_winrate_dict):
        self.hero_names_dict = hero_names_dict
        self.hero_winrate_dict = hero_winrate_dict

    def create_win_lose_bar(self, win_lose_data, player_name):
        wins = win_lose_data.get('win', 0)
        losses = win_lose_data.get('lose', 0)
        categories = ['Wins', 'Losses']
        values = [wins, losses]
        colors = ['green', 'red']
        plt.figure(figsize=(6, 4))
        plt.bar(categories, values, color=colors)
        plt.title(f"Player Win/Loss Record: {player_name}")
        plt.ylabel("Count")
        for i, value in enumerate(values):
            plt.text(i, value + 0.5, str(value), ha='center')
        plt.show()

    def create_match_summary(self, match_data):
        duration = match_data.get('duration', 0) // 60
        radiant_win = match_data.get('radiant_win', False)
        winner = "Radiant" if radiant_win else "Dire"
        plt.figure(figsize=(8, 2))
        plt.text(0.5, 0.5, f"Duration: {duration} min\nWinner: {winner}",
                 ha='center', va='center', fontsize=12)
        plt.axis('off')
        plt.show()

    def create_gpm_xpm_plot(self, match_data):
        players = match_data.get('players', [])[:10]
        hero_names = [self.hero_names_dict.get(player.get('hero_id'), "Unknown") for player in players]
        gpm = [player.get('gold_per_min', 0) for player in players]
        xpm = [player.get('xp_per_min', 0) for player in players]
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        ax1.plot(hero_names, gpm, marker='o', color='gold', label='GPM')
        ax1.set_title('Gold Per Minute (GPM)')
        ax1.set_ylabel('GPM')
        ax1.grid(True)
        ax1.tick_params(axis='x', rotation=45)
        ax2.plot(hero_names, xpm, marker='o', color='blue', label='XPM')
        ax2.set_title('Experience Per Minute (XPM)')
        ax2.set_ylabel('XPM')
        ax2.grid(True)
        ax2.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        plt.show()

    def create_kda_plot(self, match_data):
        players = match_data.get('players', [])[:10]
        for player in players:
            hero_id = player.get('hero_id')
            hero_name = self.hero_names_dict.get(hero_id, f"Unknown Hero ID {hero_id}")
            kills = player.get('kills', 0)
            deaths = player.get('deaths', 0)
            assists = player.get('assists', 0)
            labels = ['Kills', 'Deaths', 'Assists']
            sizes = [kills, deaths, assists]
            colors = ['#ff9999', '#66b3ff', '#99ff99']
            explode = (0.1, 0, 0)
            plt.figure(figsize=(6, 6))
            plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            plt.title(f'KDA for {hero_name}: {kills}/{deaths}/{assists}')
            plt.axis('equal')
            plt.show()

    
    def create_hero_winrate_plot(self, match_data):
        players = match_data.get('players', [])[:10]
        hero_ids = [player.get('hero_id') for player in players]
        hero_names = [self.hero_names_dict.get(hero_id, "Unknown") for hero_id in hero_ids]
        winrates = [self.hero_winrate_dict.get(hero_id, 0) * 100 for hero_id in hero_ids]
        plt.figure(figsize=(10, 6))
        plt.bar(hero_names, winrates, color='purple')
        plt.title("Hero Winrates in Professional Games")
        plt.ylabel("Winrate (%)")
        plt.xticks(rotation=45)
        plt.ylim(0, 100)
        for i, winrate in enumerate(winrates):
            plt.text(i, winrate + 1, f"{winrate:.1f}%", ha='center')
        plt.show()

    
    def create_recent_matches_plot(self, recent_matches):
        results = []
        kda_values = []
        for match in recent_matches:
            is_radiant = match.get('player_slot') < 128
            radiant_win = match.get('radiant_win')
            result = 1 if (is_radiant and radiant_win) or (not is_radiant and not radiant_win) else 0
            results.append(result)
            kills = match.get('kills', 0)
            deaths = match.get('deaths', 0)
            assists = match.get('assists', 0)
            kda = (kills + assists) / max(deaths, 1)  
            kda_values.append(kda)
        match_numbers = list(range(1, len(results) + 1))
        avg_kda = sum(kda_values) / len(kda_values) if kda_values else 0

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        ax1.plot(match_numbers, results, marker='o', color='green')
        ax1.set_title("Recent Matches Results (1 = Win, 0 = Loss)")
        ax1.set_xlabel("Match Number (most recent first)")
        ax1.set_ylabel("Result")
        ax1.set_ylim(-0.5, 1.5)
        ax1.grid(True)
        for i, result in enumerate(results):
            ax1.text(i + 1, result + 0.1, str(result), ha='center')

        ax2.plot(match_numbers, kda_values, marker='o', color='blue')
        ax2.set_title(f"KDA Over Recent Matches (Average KDA: {avg_kda:.2f})")
        ax2.set_xlabel("Match Number (most recent first)")
        ax2.set_ylabel("KDA")
        ax2.grid(True)
        plt.tight_layout()
        plt.show()


class DotaStatsGUI:
    def __init__(self, fetcher, plot_builder, cacher):
        self.fetcher = fetcher
        self.plot_builder = plot_builder
        self.cacher = cacher
        self.root = Tk()
        self.root.title("Match Statistics Viewer")
        self.entry = Entry(self.root, width=50)
        self.entry.pack()
        self.entry.bind("<Button-3>", self.paste)
        Button(self.root, text="Get Match Stats", command=self.fetch_match_data).pack()
        Button(self.root, text="Get Player Win/Lose", command=self.fetch_player_win_lose_data).pack()
        Button(self.root, text="Get Player Recent Matches", command=self.fetch_player_recent_matches).pack()
        self.status_label = Label(self.root, text="")
        self.status_label.pack()
        Button(self.root, text="Clear Cache", command=self.clear_cache).pack()
        instructions = Label(self.root, text="Right-click to paste match or player ID")
        instructions.pack()

    def paste(self, event):
        try:
            self.entry.event_generate('<<Paste>>')
        except:
            pass

    def fetch_match_data(self):
        match_data = self.fetcher.fetch_match_data(self.entry.get())
        if 'error' in match_data:
            self.status_label.config(text=f"Error: {match_data['error']}")
            return
        self.plot_builder.create_match_summary(match_data)
        self.plot_builder.create_gpm_xpm_plot(match_data)
        self.plot_builder.create_kda_plot(match_data)
        self.plot_builder.create_hero_winrate_plot(match_data)
        self.status_label.config(text="Match summary, stats, and hero winrates displayed.")

    def fetch_player_win_lose_data(self):
        account_id = self.entry.get()
        win_lose_data = self.fetcher.fetch_player_win_lose_data(account_id)
        if 'error' in win_lose_data:
            self.status_label.config(text=f"Error: {win_lose_data['error']}")
            return
        player_data = self.fetcher.fetch_player_profile(account_id)
        if 'error' in player_data:
            self.status_label.config(text=f"Error: {player_data['error']}")
            return
        player_name = player_data.get('profile', {}).get('personaname', 'Unknown')
        self.plot_builder.create_win_lose_bar(win_lose_data, player_name)
        self.status_label.config(text="Win/Lose stats displayed.")

    def fetch_player_recent_matches(self):
        account_id = self.entry.get()
        recent_matches = self.fetcher.fetch_recent_matches(account_id)
        if 'error' in recent_matches:
            self.status_label.config(text=f"Error: {recent_matches['error']}")
            return
        self.plot_builder.create_recent_matches_plot(recent_matches)
        self.status_label.config(text="Recent matches plot displayed.")

    def clear_cache(self):
        status = self.cacher.clear_cache()
        self.status_label.config(text=status)

    def run(self):
        self.root.mainloop()


with open('hero_ids.json', 'r') as file:
    hero_names_data = json.load(file)
hero_names_dict = {hero['id']: hero['name'] for hero in hero_names_data['result']['heroes']}

cacher = APICacher()
fetcher = DotaDataFetcher(cacher)
hero_stats = fetcher.fetch_hero_stats()
hero_winrate_dict = {hero['id']: (hero['pro_win'] / hero['pro_pick'] if hero['pro_pick'] > 0 else 0) for hero in hero_stats}
plot_builder = PlotBuilder(hero_names_dict, hero_winrate_dict)
gui = DotaStatsGUI(fetcher, plot_builder, cacher)
gui.run()