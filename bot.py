import discord
import feedparser
import json
import os
import asyncio
from datetime import timezone

FEED_URL = os.environ["FEED_URL"]

import hashlib
_feed_hash = hashlib.md5(FEED_URL.encode()).hexdigest()[:8]
SEEN_FILE = f"seen_articles_{_feed_hash}.json"
CHECK_INTERVAL = 600  # seconds (10 minutes)

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
DISCORD_CHANNEL_ID = int(os.environ["DISCORD_CHANNEL_ID"])


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def fetch_new_articles(seen):
    feed = feedparser.parse(FEED_URL)
    feed_title = feed.feed.get("title", FEED_URL)
    new = []
    for entry in reversed(feed.entries):  # oldest first
        if entry.id not in seen:
            new.append(entry)
    return new, feed_title


class FeedBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.seen = load_seen()

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        self.loop.create_task(self.poll_feed())

    async def poll_feed(self):
        await self.wait_until_ready()
        channel = self.get_channel(DISCORD_CHANNEL_ID)
        if channel is None:
            print(f"ERROR: Could not find channel {DISCORD_CHANNEL_ID}")
            return

        while not self.is_closed():
            try:
                new_articles, feed_title = fetch_new_articles(self.seen)
                for entry in new_articles:
                    embed = discord.Embed(
                        title=entry.title,
                        url=entry.link,
                        description=getattr(entry, "summary", "")[:300] or None,
                        color=0x2B6CB0,
                    )
                    if hasattr(entry, "media_content") and entry.media_content:
                        embed.set_image(url=entry.media_content[0].get("url", ""))
                    embed.set_footer(text=feed_title)
                    await channel.send(embed=embed)
                    self.seen.add(entry.id)

                if new_articles:
                    save_seen(self.seen)

            except Exception as e:
                print(f"Error polling feed: {e}")

            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    client = FeedBot()
    client.run(DISCORD_TOKEN)
