import asyncio
import datetime
import json
import logging
import os.path
import sqlite3

import aiohttp

db = sqlite3.connect('nekoweb.db')

logger = logging.Logger(__name__)
logger.setLevel(logging.DEBUG)
logger_console = logging.StreamHandler()
logger_console.setLevel(logging.DEBUG)
logger_console.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
logger.addHandler(logger_console)

logger_file = logging.FileHandler('nekoweb.log')
logger_file.setLevel(logging.DEBUG)
logger_file.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
logger.addHandler(logger_file)

async def send_to_discord(webhook, views, last_visits):
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook, json={
            "embeds": [
                {
                    "title": "Nekoweb Tracker",
                    "description": f"The visitor counter has been updated!",
                    "color": "#00ff00",
                    "fields": [
                        {
                            "name": "Views",
                            "value": f"From {last_visits} to {views}!",
                            "inline": True
                        },
                        {
                            "name": "Difference",
                            "value": f"{views - last_visits}",
                            "inline": True
                        }
                    ],
                    "footer": {
                        "text": "Nekoweb Tracker",
                        "icon_url": "https://nekoweb.org/favicon.ico"
                    }
                }
            ]
        }):
            pass


async def main():
    # Let's get the information
    async with aiohttp.ClientSession() as session:
        async with session.get("https://nekoweb.org/api/site/info/%s" % config["username"]) as req:
            logger.debug('API responded with status %s' % str(req.status))
            if req.status == 200:
                out = await req.json()
                logger.debug('Got json formatted body')

                cur = db.cursor()
                cur.execute("create table if not exists viewshistory(date text, views int);")
                
                # Get last visits
                cur.execute("select * from viewshistory order by date desc limit 1")
                last_entry = cur.fetchone()
                if last_entry is not None:
                    last_visits = last_entry[1]
                else:
                    last_visits = 0

                logger.debug('Writing to the database')
                cur.execute('insert into viewshistory(date, views) values (?, ?)',
                            (str(datetime.datetime.now()), out["views"]))

                logger.debug('Commiting to the database')
                db.commit()
                
                # Send to Discord webhook
                if config["webhook"] is not None:
                    await send_to_discord(config["webhook"], out["views"], last_visits)
                
                logger.debug('Finished.')


if __name__ == '__main__':
    logger.debug('Checking everything is in order...')
    if not os.path.exists('config.json'):
        logger.critical('config.json not found!')
        raise Exception('config.json not found')

    with open('config.json', 'r') as f:
        logger.debug('Loading config.json')
        config = json.load(f)

    if 'username' not in config:
        logger.critical('No username provided in config.json!')
        raise Exception('username not found')
    logger.debug('Starting Nekoweb tracker')
    asyncio.run(main())
