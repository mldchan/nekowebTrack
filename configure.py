# Run this file to configure the project
import asyncio
import json

import aiohttp


async def main():
    username = input("Your Nekoweb username: ")
    username_valid = False
    while not username_valid:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://nekoweb.org/api/site/info/%s' % username) as req:
                if req.status == 200:
                    print("Your username seems to exist, setting up the project...")
                    with open('config.json', 'w') as f:
                        json.dump({'username': username}, f)

                    print("Project setup complete, you can now run main.py.")
                    username_valid = True
                else:
                    print("An account with this username was not found, try again")

if __name__ == '__main__':
    asyncio.run(main())
