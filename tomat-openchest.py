import requests
import json
import urllib.parse
from urllib.parse import parse_qs, unquote
import time
import asyncio
import aiohttp
from colorama import Fore, Style, init

REFF_CODE = "00000loQ"
MAX_THREAD = 2

class BoxClaim:
    def __init__(self):
        self.base_url = "https://api-web.tomarket.ai/tomarket-game/v1"
        self.headers = {
            'Content-Type': 'application/json'
        }
        self.session = None

    def print_message(self, message):
        print(f"{Fore.CYAN}[ TOMARKET ]{Style.RESET_ALL} {message}")

    def load_data(self):
        try:
            with open('data.txt', 'r') as f:
                queries = [line.strip() for line in f.readlines()]
            return queries
        except FileNotFoundError:
            print("data.txt file not found.")
            return []
        except Exception as e:
            print("Error loading data:", str(e))
            return []

    def parse_query(self, query: str):
        parsed_query = parse_qs(query)
        parsed_query = {k: v[0] for k, v in parsed_query.items()}
        user_data = json.loads(unquote(parsed_query['user']))
        parsed_query['user'] = user_data
        return parsed_query

    async def login(self, query):
        url = f'{self.base_url}/user/login'
        try:
            payload = {
                'init_data': query,
                'invite_code': REFF_CODE,
                'is_bot': False
            }
            async with self.session.post(url, headers=self.headers, json=payload) as response:
                data = await response.json()
                if data and 'data' in data and 'access_token' in data['data']:
                    return data['data']['access_token']
            return None
        except Exception as e:
            self.print_message(f"{Fore.RED}[ {e} ]{Style.RESET_ALL}")
            return None

    async def input_reff_code(self, token):
        url = f"{self.base_url}/user/inviteCode"
        headers = {**self.headers, 'Authorization': token}
        payload = {"invite_code": REFF_CODE}
        async with self.session.post(url, headers=headers, json=payload) as response:
            return await response.json()

    async def claim_treasure_box(self, token):
        url = f"{self.base_url}/invite/openTreasureBox"
        headers = {**self.headers, 'Authorization': token}
        async with self.session.post(url, headers=headers) as response:
            return await response.json()

    async def process_account(self, query, index, total):
        try:
            parsed_data = self.parse_query(query)
            user = parsed_data['user']
            username = user.get('username', 'Unknown')
            
            self.print_message(f"[{index}/{total}] Welcome, {Fore.YELLOW}{username}{Style.RESET_ALL}")

            token = await self.login(query)
            if not token:
                self.print_message(f"{Fore.RED}Login failed for {Fore.YELLOW}{username}{Style.RESET_ALL}")
                return

            self.print_message(f"Trying to input referral code for {Fore.YELLOW}{username}{Style.RESET_ALL}")
            reff_result = await self.input_reff_code(token)
            if reff_result['status'] == 0:
                self.print_message(f"{Fore.GREEN}Success input reff code{Style.RESET_ALL}")
            else:
                self.print_message(f"{Fore.RED}Referral code info: {reff_result.get('message', 'Unknown error')}{Style.RESET_ALL}")

            await asyncio.sleep(2)

            self.print_message(f"Trying to claim treasure box for {Fore.YELLOW}{username}{Style.RESET_ALL}")
            result = await self.claim_treasure_box(token)
            if result['status'] == 0:
                self.print_message(f"{Fore.GREEN}Success claim treasure box! Reward: {result['data']['toma_reward']} TOMA{Style.RESET_ALL}")
            else:
                self.print_message(f"{Fore.RED}Failed to claim treasure box: {result.get('message', 'Unknown error')}{Style.RESET_ALL}")

            await asyncio.sleep(2)

        except Exception as e:
            self.print_message(f"{Fore.RED}Error occurred for account {Fore.YELLOW}{username}{Style.RESET_ALL}: {str(e)}")

    async def process_all_accounts(self):
        queries = self.load_data()
        print(f"Total accounts found: {len(queries)}")
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            tasks = []
            for index, query in enumerate(queries, 1):
                tasks.append(self.process_account(query, index, len(queries)))
                if len(tasks) >= MAX_THREAD:
                    await asyncio.gather(*tasks)
                    tasks = []
            if tasks:
                await asyncio.gather(*tasks)

def main():
    init(autoreset=True)
    print(r"""
    
                [ TOMARKET TREASURE BOX CLAIMER ]
          
    """)
    claimer = BoxClaim()
    asyncio.run(claimer.process_all_accounts())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    except Exception as e:
        print(f"An error occurred: {str(e)}")