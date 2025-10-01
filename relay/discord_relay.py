#!/usr/bin/env python3
import argparse
import os
import queue
import re
import sys
import threading
import time
from typing import Optional

import requests

GUILD_PATTERNS = [
	re.compile(r"^.*\[(?:G|Guild)\]\s*\[(?P<name>[^\]]+)\]:\s*(?P<message>.+)$"),
	re.compile(r"^.*\[(?:G|Guild)\].*?\[(?P<name>[^\]]+)\]:\s*(?P<message>.+)$"),
]

SYSTEM_LIKE = [
	re.compile(r"^\[(?:Guild|Guild Message of the Day|Achievement)\]", re.IGNORECASE),
]

LINE_TIMESTAMP = re.compile(r"^(?P<ts>\d{2}/\d{2}/\d{2}.*?\d{2}:\d{2}:\d{2}(?:\.\d+)?)")


def extract_guild_message(line: str) -> Optional[dict]:
	for pattern in GUILD_PATTERNS:
		m = pattern.search(line)
		if m:
			name = m.group("name").strip()
			message = m.group("message").strip()
			if not name or not message:
				return None
			for s in SYSTEM_LIKE:
				if s.search(line):
					return None
			return {"name": name, "message": message}
	return None


def extract_timestamp(line: str) -> str:
	m = LINE_TIMESTAMP.match(line)
	if m:
		return m.group("ts")
	return time.strftime("%Y-%m-%d %H:%M:%S")


def find_savedvariables_webhook(saved_variables_path: str) -> Optional[str]:
	try:
		with open(saved_variables_path, "r", encoding="utf-8", errors="ignore") as f:
			data = f.read()
			m = re.search(r"GuildToDiscordDB\s*=\s*\{[\s\S]*?webhookUrl\s*=\s*\"(.*?)\"", data)
			if m:
				return m.group(1)
	except FileNotFoundError:
		return None
	return None


def post_to_discord(webhook: str, content: str) -> None:
	resp = requests.post(webhook, json={"content": content}, timeout=10)
	if resp.status_code >= 300:
		raise RuntimeError(f"Discord webhook failed {resp.status_code}: {resp.text[:200]}")


def tail_file(path: str, stop_event: threading.Event):
	with open(path, "r", encoding="utf-8", errors="ignore") as f:
		f.seek(0, os.SEEK_END)
		inode = os.fstat(f.fileno()).st_ino if hasattr(os, "stat") else None
		while not stop_event.is_set():
			line = f.readline()
			if line:
				yield line.rstrip("\n")
				continue
			try:
				if inode is not None and os.stat(path).st_ino != inode:
					f.close()
					f = open(path, "r", encoding="utf-8", errors="ignore")
					inode = os.fstat(f.fileno()).st_ino
					f.seek(0, os.SEEK_END)
			except Exception:
				pass
			time.sleep(0.25)


def worker(line_queue: "queue.Queue[str]", webhook: str, stop_event: threading.Event):
	while not stop_event.is_set():
		try:
			line = line_queue.get(timeout=0.5)
		except queue.Empty:
			continue
		msg = extract_guild_message(line)
		if not msg:
			continue
		ts = extract_timestamp(line)
		content = f"[{msg['name']}][{ts}][{msg['message']}]"
		try:
			post_to_discord(webhook, content)
		except Exception as e:
			print(f"Failed to post: {e}", file=sys.stderr)


def main():
	parser = argparse.ArgumentParser(description="Relay WoW Guild chat to Discord via webhook")
	parser.add_argument("--log-path", help="Path to WoWChatLog.txt", required=True)
	parser.add_argument("--webhook", help="Discord webhook URL")
	parser.add_argument("--savedvariables", help="Path to GuildToDiscord.lua SavedVariables (to read webhook)")
	args = parser.parse_args()

	webhook = args.webhook
	if not webhook and args.savedvariables:
		webhook = find_savedvariables_webhook(args.savedvariables)
	if not webhook:
		print("Error: webhook not provided and not found in SavedVariables", file=sys.stderr)
		return 2

	if not os.path.isfile(args.log_path):
		print(f"Error: log file not found: {args.log_path}", file=sys.stderr)
		return 2

	stop_event = threading.Event()
	line_queue: "queue.Queue[str]" = queue.Queue(maxsize=1000)

	def producer():
		for line in tail_file(args.log_path, stop_event):
			try:
				line_queue.put_nowait(line)
			except queue.Full:
				pass

	prod_thread = threading.Thread(target=producer, daemon=True)
	prod_thread.start()

	try:
		worker(line_queue, webhook, stop_event)
	except KeyboardInterrupt:
		pass
	finally:
		stop_event.set()
		prod_thread.join(timeout=1.0)

	return 0


if __name__ == "__main__":
	sys.exit(main())