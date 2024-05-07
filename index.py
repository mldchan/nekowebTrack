import asyncio
import datetime
import json
import logging
import aiohttp
import sqlite3

db = sqlite3.connect('nekoweb.db')

logger = logging.Logger(__name__)
logger.setLevel(logging.DEBUG)
logger_console = logging.StreamHandler()
logger_console.setLevel(logging.DEBUG)
logger.addHandler(logger_console)

logger_file = logging.FileHandler('nekoweb.log')
logger_file.setLevel(logging.DEBUG)
logger.addHandler(logger_file)


async def main():
    # Let's get the information
    async with aiohttp.ClientSession() as session:
        async with session.get("https://nekoweb.org/api/site/info/akatsuki") as req:
            logger.debug('API responded with status %s' % str(req.status))
            if req.status == 200:
                out = await req.json()
                logger.debug('Got json formatted body')

                cur = db.cursor()
                cur.execute("create table if not exists viewshistory(date text, views int);")

                logger.debug('Writing to the database')
                cur.execute('insert into viewshistory(date, views) values (?, ?)',
                            (str(datetime.datetime.now()), out["views"]))

                logger.debug('Commiting to the database')
                db.commit()
                logger.debug('Finished.')


if __name__ == '__main__':
    logger.debug('Starting Nekoweb tracker')
    asyncio.run(main())
