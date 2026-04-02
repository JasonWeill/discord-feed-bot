import discord
import feedparser
import json
import os
import asyncio
import hashlib

# FEEDS must be a JSON array of {"url": "...", "channel_id": 123} objects
FEEDS = json.loads(os.environ["FEEDS"])
CHECK_INTERVAL = 600  # seconds (10 minutes)

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]


def seen_file(url):
    h = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"seen_articles_{h}.json"


def load_seen(url):
    path = seen_file(url)
    if os.path.exists(path):
        with open(path) as f:
            return set(json.load(f))
    return set()


def save_seen(url, seen):
    with open(seen_file(url), "w") as f:
        json.dump(list(seen), f)


def fetch_new_articles(url, seen):
    feed = feedparser.parse(url)
    feed_title = feed.feed.get("title", url)
    new = []
    for entry in reversed(feed.entries):  # oldest first
        if entry.id not in seen:
            new.append(entry)
    return new, feed_title


class FeedBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.seen = {f["url"]: load_seen(f["url"]) for f in FEEDS}

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        for feed in FEEDS:
            self.loop.create_task(self.poll_feed(feed["url"], int(feed["channel_id"])))

    async def poll_feed(self, url, channel_id):
        await self.wait_until_ready()
        channel = self.get_channel(channel_id)
        if channel is None:
            print(f"ERROR: Could not find channel {channel_id}")
            return

        while not self.is_closed():
            try:
                new_articles, feed_title = fetch_new_articles(url, self.seen[url])
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
                    self.seen[url].add(entry.id)

                if new_articles:
                    save_seen(url, self.seen[url])

            except Exception as e:
                print(f"Error polling {url}: {e}")

            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    client = FeedBot()
    client.run(DISCORD_TOKEN)
