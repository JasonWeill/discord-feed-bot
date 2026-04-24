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
        self.polling_started = False

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        print(f"Connected to {len(self.guilds)} guild(s):")
        for guild in self.guilds:
            print(f"  - {guild.name} (id={guild.id})")
        print(f"Configured feeds:")
        for feed in FEEDS:
            print(f"  - {feed['url']} -> channel {feed['channel_id']}")

        # Only start polling tasks once, even if bot reconnects
        if not self.polling_started:
            print("Starting polling tasks...")
            for feed in FEEDS:
                self.loop.create_task(self.poll_feed(feed["url"], int(feed["channel_id"])))
            self.polling_started = True
        else:
            print("Reconnected - polling tasks already running")

    async def poll_feed(self, url, channel_id):
        await self.wait_until_ready()
        print(f"[{url}] Polling task started")

        while not self.is_closed():
            try:
                print(f"[{url}] Looking up channel/thread {channel_id}")
                try:
                    channel = await self.fetch_channel(channel_id)
                except discord.NotFound:
                    print(f"[{url}] ERROR: Channel/thread {channel_id} not found, will retry in {CHECK_INTERVAL}s")
                    await asyncio.sleep(CHECK_INTERVAL)
                    continue
                except discord.Forbidden:
                    print(f"[{url}] ERROR: No access to channel/thread {channel_id}, will retry in {CHECK_INTERVAL}s")
                    await asyncio.sleep(CHECK_INTERVAL)
                    continue
                print(f"[{url}] Found: #{channel.name}")

                print(f"[{url}] Fetching feed")
                new_articles, feed_title = fetch_new_articles(url, self.seen[url])
                print(f"[{url}] Feed title: {feed_title!r}, new articles: {len(new_articles)}")

                for entry in new_articles:
                    print(f"[{url}] Posting: {entry.title!r}")
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
                    print(f"[{url}] Posted: {entry.title!r}")

                if new_articles:
                    save_seen(url, self.seen[url])

            except Exception as e:
                print(f"[{url}] Error: {e}")

            print(f"[{url}] Sleeping {CHECK_INTERVAL}s")
            await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    client = FeedBot()
    client.run(DISCORD_TOKEN)
