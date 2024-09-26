import asyncio
import datetime
import json
import logging
import os.path
import sqlite3

import aiohttp

if not os.path.exists('data'):
    os.makedirs('data')
db = sqlite3.connect('data/nekoweb.db')

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


async def send_views_to_discord(webhook, views, last_visits):
    if views == last_visits:
        logger.debug('Views are the same, skipping Discord webhook')
        return
    logger.debug('Sending to Discord webhook')
    async with aiohttp.ClientSession() as session:
        logger.debug('Posting to Discord webhook')
        async with session.post(webhook, json={"embeds": [
            {"title": "Nekoweb Tracker", "description": f"The visitor counter has been updated!", "color": 0x7FD5EA,
                "fields": [{"name": "Views", "value": f"From {last_visits} to {views}!"},
                    {"name": "Difference", "value": f"{views - last_visits}"}],
                "footer": {"text": "Nekoweb Tracker"}}]}) as req:
            if req.status == 204:
                logger.debug('Discord webhook sent')
            else:
                logger.error('Failed to send Discord webhook')

                reason = await req.text()
                logger.error('Discord webhook failed with status %s: %s' % (req.status, reason))


async def send_update_to_discord(webhook, updated_at, last_update_at):
    updated_at = datetime.datetime.fromtimestamp(int(updated_at) / 1000)
    last_update_at = datetime.datetime.fromtimestamp(int(last_update_at) / 1000)

    if updated_at == last_update_at:
        logger.debug('No updates found, skipping Discord webhook')
        return
    logger.debug('Sending to Discord webhook')
    async with aiohttp.ClientSession() as session:
        logger.debug('Posting to Discord webhook')

        from_formatted = last_update_at.strftime('%Y年%m月%d日 %H:%M')
        to_formatted = updated_at.strftime('%Y年%m月%d日 %H:%M')
        diff = updated_at - last_update_at
        diff_formatted = f"{diff.days}日 {diff.seconds // 3600}時間 {(diff.seconds // 60) % 60}分"

        async with session.post(webhook, json={"embeds": [
            {"title": "Nekoweb Tracker", "description": f"The website has been updated!", "color": 0x7FD5EA,
                "fields": [{"name": "Latest Update", "value": f"{to_formatted}!"},
                    {"name": "Previous Update", "value": f"{from_formatted}!"},
                    {"name": "Difference", "value": f"{diff_formatted}"}],
                "footer": {"text": "Nekoweb Tracker"}}]}) as req:
            if req.status == 204:
                logger.debug('Discord webhook sent')
            else:
                logger.error('Failed to send Discord webhook')
                reason = await req.text()
                logger.error('Discord webhook failed with status %s: %s' % (req.status, reason))


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
                cur.execute('create table if not exists updatehistory(date text, last_update_date text);')

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
                    logger.debug('Sending to Discord webhook')
                    await send_views_to_discord(config["webhook"], out["views"], last_visits)
                else:
                    logger.debug('No webhook provided in config.json, skipping...')

                # Check if there was an update using updated_at (int milliseconds unix timestamp)
                if out["updated_at"] is not None:
                    logger.debug('Checking for updates')
                    cur.execute('select * from updatehistory order by date desc limit 1')
                    last_update = cur.fetchone()
                    if last_update is not None:
                        if last_update[1] == out["updated_at"]:
                            logger.debug('No updates found')
                        else:
                            logger.debug('Updates found')
                            await send_update_to_discord(config["webhook"], out["updated_at"], last_update[1])
                    else:
                        logger.debug('No updates found')
                    cur.execute('insert into updatehistory(date, last_update_date) values (?, ?)',
                                (str(datetime.datetime.now()), out["updated_at"]))
                    db.commit()

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
