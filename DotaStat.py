import json
import requests
import os
import time


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


import matplotlib.pyplot as plt


class PlotBuilder:
    def __init__(self, hero_names_dict):
        self.hero_names_dict = hero_names_dict

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

    def create_kda_plot(self, match_data):
        def calculate_kda(kills, deaths, assists):
            return (kills + assists) / max(deaths, 1)

        fig, axes = plt.subplots(5, 2, figsize=(20, 30))
        fig.suptitle('KDA for First 10 Players', fontsize=16)
        axes = axes.ravel()

        for i, player in enumerate(match_data.get('players', [])[:10]):
            hero_id = player.get('hero_id')
            hero_name = self.hero_names_dict.get(hero_id, f"Unknown Hero ID {hero_id}")

            kills = player.get('kills', 0)
            deaths = player.get('deaths', 0)
            assists = player.get('assists', 0)

            kda = calculate_kda(kills, deaths, assists)

            x = ['Kills', 'Deaths', 'Assists']
            y = [kills, deaths, assists]
            axes[i].bar(x, y, color=['#ff9999', '#66b3ff', '#99ff99'])
            axes[i].set_title(f'KDA for {hero_name}: {kda:.2f}')
            axes[i].set_ylabel('Count')
            axes[i].text(0.5, max(y) * 1.1, f'KDA: {kda:.2f}', horizontalalignment='center')

        plt.tight_layout()
        plt.subplots_adjust(top=0.95)
        plt.show()


from tkinter import Tk, Entry, Button, Label


class DotaStatsGUI:
    def __init__(self, fetcher, plot_builder, cacher):
        self.fetcher = fetcher
        self.plot_builder = plot_builder
        self.cacher = cacher

        # GUI
        self.root = Tk()
        self.root.title("Match Statistics Viewer")

        self.entry = Entry(self.root, width=50)
        self.entry.pack()

        self.entry.bind("<Button-3>", self.paste)

        Button(self.root, text="Get Match Stats", command=self.fetch_match_data).pack()
        Button(self.root, text="Get Player Win/Lose", command=self.fetch_player_win_lose_data).pack()

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
        self.plot_builder.create_kda_plot(match_data)
        self.status_label.config(text="Match statistics displayed.")

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
plot_builder = PlotBuilder(hero_names_dict)
gui = DotaStatsGUI(fetcher, plot_builder, cacher)

gui.run()
