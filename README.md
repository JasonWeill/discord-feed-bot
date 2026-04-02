# Discord Feed Bot

A Discord bot that polls one or more RSS feeds and automatically posts new articles as embeds to associated Discord channels.

## Prerequisites

- Python 3.8+
- A Discord account with permission to manage a server

## 1. Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**.
2. Give it a name (e.g. "Feed Bot") and click **Create**.
3. In the left sidebar, click **Bot**.
4. Click **Add Bot**, then confirm.
5. Under the **Token** section, click **Reset Token** and copy the token — you'll need this for your `.env` file.
6. Scroll down to **Privileged Gateway Intents** and make sure they are all **disabled** (this bot doesn't need them).

## 2. Invite the Bot to Your Server

1. In the left sidebar, click **OAuth2 > URL Generator**.
2. Under **Scopes**, check `bot`.
3. Under **Bot Permissions**, check:
   - `Send Messages`
   - `Embed Links`
4. Copy the generated URL at the bottom of the page, open it in your browser, and select the server you want to add the bot to.

> You must have the **Manage Server** permission on the target server to add a bot.

## 3. Get Your Channel IDs

For each feed you want to monitor, you'll need the ID of the Discord channel it should post to.

1. In Discord, open **User Settings > Advanced** and enable **Developer Mode**.
2. Right-click each channel you want the bot to post in and click **Copy Channel ID**.

## 4. Configure the Bot

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```
DISCORD_TOKEN=your-bot-token-here
FEEDS=[{"url":"https://theurbanist.org/feed/","channel_id":111222333444555666},{"url":"https://www.myballard.com/feed/","channel_id":777888999000111222}]
```

`FEEDS` is a JSON array where each object maps one RSS feed URL to one Discord channel ID. Each feed posts only to its associated channel.

## 5. Install Dependencies

```bash
pip3 install discord.py feedparser
```

## 6. Run the Bot

### Manually

```bash
python3 bot.py
```

### As a systemd Service (runs on boot, restarts on failure)

```bash
# Copy the service file
sudo cp feed-bot.service /etc/systemd/system/

# Reload systemd and enable the service
sudo systemctl daemon-reload
sudo systemctl enable feed-bot
sudo systemctl start feed-bot
```

Check the status or logs:

```bash
sudo systemctl status feed-bot
journalctl -u feed-bot -f
```

## How It Works

The bot polls each RSS feed every 10 minutes in parallel. New articles are posted to their associated channel as Discord embeds showing the title, link, and a short summary. The footer of each embed shows the feed's own name. Seen article IDs are saved to a per-feed JSON file so duplicates are never posted, even after a restart.

## Author

This script was made with the assistance of Claude Code, and is published by Jason Weill (dev@weill.org).
