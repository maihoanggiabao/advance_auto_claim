import requests
import datetime
import time
import pytz
from .base import basetap

DEFAULT_HEADERS = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9,vi;q=0.8",
    "authorization": "Bearer 17135328889144GZkVJpJhxCCkBjffo6FNgBr2gM4pQTg8TU4ADhWjpJSTHI127AqcYfiDXS3VtgA5624258194",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://hamsterkombat.io",
    "priority": "u=1, i",
    "referer": "https://hamsterkombat.io/",
    "sec-ch-ua": "\"Chromium\";v=\"124\", \"Microsoft Edge\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
}

DEFAULT_AUTH = "Bearer 17135328889144GZkVJpJhxCCkBjffo6FNgBr2gM4pQTg8TU4ADhWjpJSTHI127AqcYfiDXS3VtgA5624258194"

class hamster(basetap):
    def __init__(self, auth=DEFAULT_AUTH, proxy=None, headers=DEFAULT_HEADERS):
        super().__init__()
        self.auth = auth
        self.proxy = proxy
        self.headers = headers
        self.stopped = False
        self.wait_time = 5
        self.name = self.__class__.__name__
        self.last_remain = 1
        self.availableTaps = 201
        self.next_time_buy_boost = 0

    def parse_config(self, cline):
        self.update_header("authorization", cline["authorization"])

    def check_boost(self):
        url = "https://api.hamsterkombat.io/clicker/boosts-for-buy"
        
        try:
            response = requests.post(url, headers=self.headers, proxies=self.proxy)

            if response.status_code == 200:
                data = response.json()
                boost_for_buy = data["boostsForBuy"]
                
                for boost in boost_for_buy:
                    if boost["id"] == "BoostFullAvailableTaps":
                        count_down_time = boost["cooldownSeconds"]
                        # print(f"Countdown time for BoostFullAvailableTaps: {count_down_time} seconds")
                        return count_down_time
                print("BoostFullAvailableTaps not found.")
            else:
                print(f"Request failed with status code {response.status_code}.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def update_time_buy_boost(self, duration):
        current_time = datetime.datetime.now(pytz.UTC)
        self.next_time_buy_boost = int(current_time.timestamp()) + duration + 20

    def buy_boost(self):
        url = "https://api.hamsterkombat.io/clicker/buy-boost"
        max_retries = 3  # Number of retries
        retries = 0
        
        while retries < max_retries:
            current_time = datetime.datetime.now()
            time_buy_boost = int(current_time.timestamp())
            data = {
                "boostId": "BoostFullAvailableTaps",
                "timestamp": time_buy_boost
            }

            try:
                response = requests.post(url, headers=self.headers, json=data, proxies=self.proxy)
                
                if response.status_code == 200:
                    data = response.json()
                    available_taps = data["clickerUser"]["availableTaps"]
                    max_taps = data["clickerUser"]["maxTaps"]
                    if available_taps == max_taps:
                        self.bprint("Buy boost thành công!!")
                        return
                    else:
                        retries += 1
                        if retries < max_retries:
                            self.bprint(f"Attempt {retries} failed. Retrying...")
                        else:
                            self.bprint("Cannot buy boost!!")
                else:
                    retries += 1
                    if retries < max_retries:
                        self.bprint(f"Attempt {retries} failed with status code {response.status_code}. Retrying...")
                    else:
                        self.bprint(f"Failed to buy boost after {max_retries} attempts. Status code: {response.status_code}.")
            except Exception as e:
                retries += 1
                if retries < max_retries:
                    self.bprint(f"Attempt {retries} encountered an error: {e}. Retrying...")
                else:
                    self.bprint(f"Failed to buy boost after {max_retries} attempts due to error: {e}.")


    def is_boost_ready(self):
        current_epoch_seconds = int(time.time())
        return current_epoch_seconds >= self.next_time_buy_boost

    def tap(self):
        url = "https://api.hamsterkombat.io/clicker/tap"
        current_time = datetime.datetime.now()
        current_timestamp = int(current_time.timestamp())
        data = {
            "count": self.availableTaps,
            "availableTaps": self.availableTaps,
            "timestamp": current_timestamp
        }
        try:
            response = requests.post(url, headers=self.headers, json=data, proxies=self.proxy)
            data = response.json()
            self.print_balance(data['clickerUser']['balanceCoins'])
            self.availableTaps = data["clickerUser"]["availableTaps"]
            return data["clickerUser"]["availableTaps"]
        except Exception as e:
            self.bprint(e)
            return 1

    def claim(self):
        if self.next_time_buy_boost == 0:
            count_down_time = self.check_boost()
        if count_down_time:
            self.update_time_buy_boost(count_down_time)
        
        if self.is_boost_ready():
                if self.availableTaps < 400:
                    self.buy_boost()
                else:
                    self.bprint("Boost is ready but available taps are sufficient. Continuing tapping...")
        self.tap()

