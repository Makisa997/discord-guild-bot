local addonName = ...

GuildToDiscordDB = GuildToDiscordDB or {}

local function ensureDefaults()
	if type(GuildToDiscordDB) ~= "table" then GuildToDiscordDB = {} end
	if type(GuildToDiscordDB.webhookUrl) ~= "string" then GuildToDiscordDB.webhookUrl = "" end
end

local function onEvent(self, event, ...)
	if event == "ADDON_LOADED" then
		local loadedName = ...
		if loadedName == addonName then
			ensureDefaults()
			-- Enable chat logging so WoW writes Logs/WoWChatLog.txt (required for near real-time relay)
			if LoggingChat then
				LoggingChat(true)
			end
			-- Register settings UI in Dragonflight retail
			if Settings and Settings.RegisterCanvasLayoutCategory and CreateFrame then
				local panel = CreateFrame("Frame")
				panel.name = "GuildToDiscord"
				panel:Hide()

				local title = panel:CreateFontString(nil, "ARTWORK", "GameFontNormalLarge")
				title:SetPoint("TOPLEFT", 16, -16)
				title:SetText("GuildToDiscord")

				local desc = panel:CreateFontString(nil, "ARTWORK", "GameFontHighlight")
				desc:SetPoint("TOPLEFT", title, "BOTTOMLEFT", 0, -8)
				desc:SetJustifyH("LEFT")
				desc:SetText("Enter your Discord Webhook URL below. A companion script will read this and tail WoWChatLog.txt to relay guild chat.")

				local editBox = CreateFrame("EditBox", nil, panel, "InputBoxTemplate")
				editBox:SetSize(560, 30)
				editBox:SetPoint("TOPLEFT", desc, "BOTTOMLEFT", 0, -12)
				editBox:SetAutoFocus(false)
				editBox:SetText(GuildToDiscordDB.webhookUrl or "")
				editBox:HighlightText(0, 0)
				editBox:SetCursorPosition(0)

				local label = panel:CreateFontString(nil, "ARTWORK", "GameFontNormal")
				label:SetPoint("BOTTOMLEFT", editBox, "TOPLEFT", 4, 6)
				label:SetText("Discord Webhook URL")

				editBox:SetScript("OnEditFocusLost", function(self)
					GuildToDiscordDB.webhookUrl = self:GetText() or ""
				end)

				local hint = panel:CreateFontString(nil, "ARTWORK", "GameFontDisable")
				hint:SetPoint("TOPLEFT", editBox, "BOTTOMLEFT", 4, -8)
				hint:SetJustifyH("LEFT")
				hint:SetText("Changes are saved immediately. Use /reload to flush SavedVariables to disk.")

				local category, layout = Settings.RegisterCanvasLayoutCategory(panel, "GuildToDiscord")
				Settings.RegisterAddOnCategory(category)
			end

			-- Slash command for quick set/view
			SLASH_GUILDTODISCORD1 = "/g2d"
			SlashCmdList.GUILDTODISCORD = function(msg)
				msg = tostring(msg or ""):gsub("^%s+", ""):gsub("%s+$", "")
				if msg == "" then
					DEFAULT_CHAT_FRAME:AddMessage("GuildToDiscord: current webhook=" .. (GuildToDiscordDB.webhookUrl ~= "" and GuildToDiscordDB.webhookUrl or "<not set>"))
					DEFAULT_CHAT_FRAME:AddMessage("Usage: /g2d https://discord.com/api/webhooks/...")
					return
				end
				GuildToDiscordDB.webhookUrl = msg
				DEFAULT_CHAT_FRAME:AddMessage("GuildToDiscord: webhook saved. /reload to flush to disk.")
			end
		end
	elseif event == "PLAYER_LOGIN" then
		-- Ensure chat logging remains enabled across sessions
		if LoggingChat then LoggingChat(true) end
	end
end

local f = CreateFrame("Frame")
f:RegisterEvent("ADDON_LOADED")
f:RegisterEvent("PLAYER_LOGIN")
f:SetScript("OnEvent", onEvent)