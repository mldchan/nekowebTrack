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

    webhook = input("Do you want to configure a Discord webhook? (y/n): ")
    if webhook.lower() == 'y':
        webhook_url = input("Enter the Discord webhook URL: ")
        webhook_valid = False
        async with aiohttp.ClientSession() as session:
            while not webhook_valid:
                print("Sending a test message to the Discord webhook...")
                test_message = {
                    "content": "This is a test message from Nekoweb configuration. Please confirm if you received it."
                }
                async with session.post(webhook_url, json=test_message) as req:
                    if req.status == 204:
                        confirmation = input("Test message sent! Did you receive it? (yes/no): ")
                        if confirmation.lower() == 'yes':
                            webhook_valid = True
                        else:
                            print("Please re-enter the Discord webhook URL.")
                            webhook_url = input("Enter the Discord webhook URL: ")
                    else:
                        print("Failed to send test message. Please check the webhook URL.")
                        webhook_url = input("Enter the Discord webhook URL: ")
        with open('config.json', 'w') as f:
            json.dump({'username': username, 'webhook': webhook_url}, f)
        print("Discord webhook configured successfully.")
    else:
        with open('config.json', 'w') as f:
            json.dump({'username': username}, f)

if __name__ == '__main__':
    asyncio.run(main())
