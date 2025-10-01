## GuildToDiscord (Retail Demo)

Relay WoW Guild chat to Discord via webhook in near real-time using WoW's chat log and a small Python relay.

### 1) Install the WoW Addon

- Copy the `GuildToDiscord` folder into your Retail AddOns directory:
  - Windows: `C:\Program Files (x86)\World of Warcraft\_retail_\Interface\AddOns\GuildToDiscord`
  - Linux (Wine/Proton): `<wow_root>/_retail_/Interface/AddOns/GuildToDiscord`

Files included:
- `GuildToDiscord.toc`
- `GuildToDiscord.lua`

What it does:
- Adds a settings panel to store your Discord Webhook URL in `SavedVariables`.
- Enables chat logging automatically (calls `LoggingChat(true)`) so WoW writes `Logs/WoWChatLog.txt`.

### 2) Configure the Webhook In-Game

- Launch WoW Retail.
- Open the settings panel: Esc -> Options -> AddOns -> GuildToDiscord.
- Paste your Discord Webhook URL.
- Type `/reload` to flush `SavedVariables` to disk.
- Alternatively use the slash command: `/g2d https://discord.com/api/webhooks/...`

SavedVariables path (Retail):
- Windows: `C:\Program Files (x86)\World of Warcraft\_retail_\WTF\Account\<ACCOUNT>\SavedVariables\GuildToDiscord.lua`
- Linux (Proton): `<wow_root>/_retail_/WTF/Account/<ACCOUNT>/SavedVariables/GuildToDiscord.lua`

### 3) Enable Chat Logging

The addon calls `LoggingChat(true)` on load and login. You can also manually run `/chatlog`.
The log file appears at:
- Windows: `C:\Program Files (x86)\World of Warcraft\_retail_\Logs\WoWChatLog.txt`
- Linux (Proton): `<wow_root>/_retail_/Logs/WoWChatLog.txt`

### 4) Run the Python Relay

Prereqs:
- Python 3.9+
- Install deps: `pip install -r requirements.txt`

Run:
```bash
python relay/discord_relay.py --log-path \
  "C:/Program Files (x86)/World of Warcraft/_retail_/Logs/WoWChatLog.txt" \
  --savedvariables \
  "C:/Program Files (x86)/World of Warcraft/_retail_/WTF/Account/<ACCOUNT>/SavedVariables/GuildToDiscord.lua"
```

Or pass the webhook directly (skips SavedVariables):
```bash
python relay/discord_relay.py --log-path \
  "/path/to/_retail_/Logs/WoWChatLog.txt" \
  --webhook "https://discord.com/api/webhooks/..."
```

### Behavior
- Filters only Guild chat lines and only when a player name is present.
- Posts formatted as `[name][timestamp][message]`.
- Near real-time tailing with basic rotation handling.

### Notes & Limitations
- WoW log formats vary by locale. The relay uses several regexes for `[G]` or `[Guild]` patterns. You can add more patterns if needed.
- SavedVariables only write on `/reload` or logout; do that after changing the webhook.
- This demo avoids dependencies on external addon libraries.