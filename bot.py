# -*- coding: utf-8 -*-
"""
Hinata Bot - Final Premium v2.1
- Optimized for Render deployment
- Multi-Platform Media Downloader (yt-dlp)
- Advanced AI Engines (Gemini 3, DeepSeek, ChatGPT Addy)
- Premium UI with sanitized buttons and full command guide
"""
import os
import sys
import time
import json
import logging
import asyncio
import httpx
import shutil
import html
import re
import random
import string
import asyncio
import qrcode
import io
from datetime import datetime, timedelta
from typing import List, Dict, Union
from urllib.parse import quote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.error import Forbidden, BadRequest
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ChatMemberHandler
)
import yt_dlp


async def cmd_grammar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    text = " ".join(context.args) if context.args else None
    if not text:
        context.user_data[AWAIT_GRAMMAR] = True
        await update.message.reply_text("✍️ <b>AI Grammar Check:</b>\n\nEnter the text you want me to correct:", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
        return
    msg = await update.message.reply_text("✍️ <b>Analyzing Grammar...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        res = await fetch_grammar(client, text)
    await msg.edit_text(f"✍️ <b>Corrected Text:</b>\n\n{html.escape(res)}", parse_mode="HTML")

async def cmd_translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    text = " ".join(context.args) if context.args else None
    if not text:
        await update.message.reply_text("💡 <b>Usage:</b> <code>/translate [text]</code>")
        return
    msg = await update.message.reply_text("🌐 <b>Translating...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        res = await fetch_translate(client, text)
    await msg.edit_text(f"🌐 <b>Translated:</b>\n\n{html.escape(res)}", parse_mode="HTML")

async def cmd_summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    text = " ".join(context.args) if context.args else None
    if not text:
        await update.message.reply_text("💡 <b>Usage:</b> <code>/summarize [text]</code>")
        return
    msg = await update.message.reply_text("📝 <b>Summarizing...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        res = await fetch_summarize(client, text)
    await msg.edit_text(f"📝 <b>Summary:</b>\n\n{html.escape(res)}", parse_mode="HTML")

# ================= Configuration =================
OWNER_ID = 7333244376
BOT_TOKEN_FILE = "token.txt"
BOT_NAME = "Hinata"
BOT_USERNAME = "@Hinata_00_bot"

INBOX_FORWARD_GROUP_ID = -1003113491147

# tracked users -> forward groups
TRACKED_USER1_ID = 7039869055
FORWARD_USER1_GROUP_ID = -1002768142169
TRACKED_USER2_ID = 7209584974
FORWARD_USER2_GROUP_ID = -1002536019847

# source/destination
SOURCE_GROUP_ID = -4767799138
DESTINATION_GROUP_ID = -1002510490386

KEYWORDS = [
    "shawon", "shawn", "sn", "@shawonxnone", "shwon", "shaun", "sahun", "sawon",
    "sawn", "nusu", "nusrat", "saun", "ilma", "izumi", "🎀꧁𖨆❦︎ 𝑰𝒁𝑼𝑴𝑰 𝑼𝒄𝒉𝒊𝒉𝒂 ❦︎𖨆꧂🎀"
]

LOG_FILE = "hinata.log"
MAX_LOG_SIZE = 200 * 1024  # 200 KB

# Folders
os.makedirs("downloads", exist_ok=True)

# Latest API URLs
CHATGPT_API_URL = "https://addy-api.onrender.com/api/v1/chat/gpt4o?query={prompt}"
GEMINI3_API = "https://shawon-gemini-3-api.onrender.com/api/ask?prompt={}"
DEEPSEEK_API = "https://chatgpt-4o-aa.onrender.com/deepseek?prompt={}"
INSTA_API = "https://instagram-api-ashy.vercel.app/api/ig-profile.php?username={}"
FF_API = "http://danger-info-alpha.vercel.app/accinfo?uid={}&key=DANGERxINFO"
FF_LIKE_API = "https://duranto-like-pearl.vercel.app/like?uid={}&server_name=bd"
FF_VISIT_API = "https://top-1-visit-api.vercel.app/visit?uid={}&region=BD"
BG_REMOVE_API = "https://api.remove.bg/v1.0/removebg"
BG_REMOVE_KEY = "34Ay4ygGgwuzxnktg8MrHr4R"
TEMP_MAIL_API = "https://api.mail.tm"

POLLINATIONS_API_KEY = "sk_9308eZLzhBoEn5AAyK9iEf9eWMe45ZvV"
GEN_IMG_DIR = os.path.join(os.environ["USERPROFILE"], "Downloads", "GenImages")
if not os.path.exists(GEN_IMG_DIR):
    os.makedirs(GEN_IMG_DIR, exist_ok=True)

# ================= Logging =================
def setup_logger():
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > MAX_LOG_SIZE:
        open(LOG_FILE, "w").close()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
    )
    return logging.getLogger("hinata")

logger = setup_logger()

# ================= Utilities =================
def read_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

def read_json(path, default=None):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return default if default is not None else []
                data = json.loads(content)
                if default is not None and not isinstance(data, type(default)):
                    return default
                return data
    except Exception:
        logger.exception("Failed to read JSON: %s", path)
    return default if default is not None else []

def write_json(path, data):
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        logger.exception("Failed to write JSON: %s", path)

BOT_TOKEN = read_file(BOT_TOKEN_FILE)

# Global Settings (Can be saved to a config.json if needed)
CONFIG_FILE = "config.json"
def load_config():
    return read_json(CONFIG_FILE, {"global_access": True, "banned_users": []})

def save_config(config):
    write_json(CONFIG_FILE, config)

CONFIG = load_config()

start_time = time.time()
STATS = {
    "broadcasts": 0,
    "status": "online"
}

# Values for Tic Tac Toe
TTT_GAMES = {}
WINNING_COMBOS = [
    [0, 1, 2], [3, 4, 5], [6, 7, 8], # Rows
    [0, 3, 6], [1, 4, 7], [2, 5, 8], # Cols
    [0, 4, 8], [2, 4, 6]             # Diagonals
]

def get_uptime() -> str:
    elapsed = time.time() - start_time
    return str(timedelta(seconds=int(elapsed)))


def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

async def check_permission(update: Update, context: ContextTypes.DEFAULT_TYPE, silent: bool = False) -> bool:
    user_id = update.effective_user.id
    if is_owner(user_id):
        return True
    
    # Check if user is banned
    if user_id in CONFIG.get("banned_users", []):
        if not silent:
            await update.effective_message.reply_text("🚫 <b>Access Denied:</b> You have been globally banned.", parse_mode="HTML")
        return False
        
    # Check global access toggle
    if not CONFIG.get("global_access", True):
        # Silent ignore for groups to prevent spam
        if not silent and update.effective_chat.type == "private":
            await update.effective_message.reply_text("🔒 <b>Maintenance Mode:</b> Bot is currently private.", parse_mode="HTML")
        return False
        
    return True

# ================= Forward Helper =================
async def forward_or_copy(update: Update, context: ContextTypes.DEFAULT_TYPE, command_text: str = None):
    # ANONYMOUS FORWARDING: Uses copy_message where possible or re-sends content
    user = update.effective_user
    msg = update.message
    if not msg: return
    
    details = f"📨 <b>New Message</b>\n👤 <b>User:</b> {html.escape(user.full_name)} (@{user.username})\n🆔 <code>{user.id}</code>"
    if command_text: details += f"\n⌨️ <b>Command:</b> {command_text}"
    
    try:
        # 1. Send metadata first
        await context.bot.send_message(chat_id=DESTINATION_GROUP_ID, text=details, parse_mode="HTML")
        
        # 2. Copy the actual message content (Anonymous)
        # copy_message automatically handles photos, videos, stickers, voice, docs, etc.
        try:
             await context.bot.copy_message(
                 chat_id=DESTINATION_GROUP_ID, 
                 from_chat_id=msg.chat_id, 
                 message_id=msg.message_id
             )
        except Exception as copy_err:
             # Fallback if copy fails (e.g. strict privacy settings)
             logger.warning(f"Copy failed: {copy_err}")
             if msg.text:
                 await context.bot.send_message(chat_id=DESTINATION_GROUP_ID, text=f"📝 <b>Text Content:</b>\n{html.escape(msg.text)}", parse_mode="HTML")
             else:
                 await context.bot.send_message(chat_id=DESTINATION_GROUP_ID, text="⚠️ <b>Media Protected:</b> Could not copy message content.")

    except Exception as e:
        logger.error(f"Forward logic failed: {e}")

# ================= HTTP Helpers =================
async def fetch_json(client: httpx.AsyncClient, url: str):
    try:
        resp = await client.get(url, timeout=30.0)
        try:
            return resp.json()
        except Exception:
            return {"raw": resp.text}
    except Exception as e:
        logger.exception("HTTP fetch failed for %s", url)
        return {"error": str(e)}

async def fetch_chatgpt(client: httpx.AsyncClient, prompt: str):
    url = CHATGPT_API_URL.format(prompt=quote(prompt))
    data = await fetch_json(client, url)
    if isinstance(data, dict):
        return data.get("reply") or data.get("response") or data.get("answer") or data.get("raw") or json.dumps(data)
    return str(data)

async def fetch_flirt(client: httpx.AsyncClient, prompt: str):
    system_prompt = "Act as a charming, romantic, and playful flirt. Respond to: "
    url = CHATGPT_API_URL.format(prompt=quote(system_prompt + prompt))
    data = await fetch_json(client, url)
    if isinstance(data, dict):
        return data.get("reply") or data.get("response") or data.get("answer") or data.get("raw") or json.dumps(data)
    return str(data)

async def fetch_code(client: httpx.AsyncClient, prompt: str):
    system_prompt = "Act as an expert software engineer. Provide clean code and explanations. Text: "
    url = CHATGPT_API_URL.format(prompt=quote(system_prompt + prompt))
    data = await fetch_json(client, url)
    
    response = ""
    if isinstance(data, dict):
        response = data.get("reply") or data.get("response") or data.get("answer") or data.get("raw") or json.dumps(data)
    else:
        response = str(data)
        
    return f"```\n{response}\n```"

async def fetch_gemini3(client: httpx.AsyncClient, prompt: str):
    try:
        url = GEMINI3_API.format(quote(prompt))
        data = await fetch_json(client, url)
        if isinstance(data, dict):
            return data.get("response") or data.get("reply") or data.get("answer") or data.get("message") or json.dumps(data)
        res = str(data)
        if len(res) < 2 or "error" in res.lower():
             return "❌ Gemini API error or empty response."
        return res
    except Exception as e:
        logger.exception("Gemini3 fetch failed")
        return f"Error: {e}"

async def fetch_translate(client: httpx.AsyncClient, text: str, target_lang: str = "English"):
    prompt = f"Translate the following text to {target_lang}. Return only the translated text: {text}"
    return await fetch_chatgpt(client, prompt)

async def fetch_grammar(client: httpx.AsyncClient, text: str):
    prompt = f"Act as a professional proofreader. Correct the grammar and spelling of the following text, and provide the corrected version only: {text}"
    return await fetch_chatgpt(client, prompt)

async def fetch_summarize(client: httpx.AsyncClient, text: str):
    prompt = f"Summarize the following text clearly and concisely: {text}"
    return await fetch_chatgpt(client, prompt)

def balance_check(input_str, target_str):
    """Simple fuzzy check for game answers."""
    input_str = input_str.lower().strip()
    target_str = target_str.lower().strip()
    if input_str == target_str: return True
    if len(target_str) > 3 and target_str in input_str: return True
    return False

async def cmd_game_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    secret = random.randint(1, 100)
    context.user_data["guess_num"] = secret
    context.user_data["guess_attempts"] = 0
    context.user_data[AWAIT_GUESS] = True
    await update.effective_message.reply_text(
        "🔢 <b>Number Guessing Game</b>\n\n"
        "I have picked a number between <b>1 and 100</b>.\n"
        "Try to guess it! Send your first number below:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]])
    )

async def cmd_game_riddle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    status = await update.effective_message.reply_text("💡 <b>Creating a riddle for you...</b>", parse_mode="HTML")
    
    prompt = f"Generate a unique, rare, and fun riddle for a game. Do not repeat common riddles. (Random Seed: {random.randint(1, 1000000)}) Return requested format: RIDDLE: [the riddle text] ANSWER: [the one word answer]"
    async with httpx.AsyncClient() as client:
        res = await fetch_chatgpt(client, prompt)
    
    try:
        if "RIDDLE:" in res and "ANSWER:" in res:
            parts = res.split("ANSWER:")
            riddle = parts[0].replace("RIDDLE:", "").strip()
            answer = parts[1].strip().split()[0].replace(".", "").replace(",", "")
            
            context.user_data["riddle_answer"] = answer
            context.user_data[AWAIT_RIDDLE] = True
            
            await status.edit_text(
                f"🧠 <b>AI Riddle Challenge</b>\n\n"
                f"<i>{riddle}</i>\n\n"
                f"<b>What am I?</b> Send your answer below:",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Give Up", callback_data="btn_back")]])
            )
        else:
            await status.edit_text("❌ Failed to generate riddle. Try again!")
    except:
        await status.edit_text("❌ System error generating riddle.")

async def cmd_shorten(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, silent=True): return
    if not context.args:
        await update.message.reply_text("💡 <b>Usage:</b> <code>/shorten [url] [custom_name (optional)]</code>", parse_mode="HTML")
        return
    
    long_url = context.args[0]
    custom = f"&custom={context.args[1]}" if len(context.args) > 1 else ""
    
    msg = await update.message.reply_text("🔗 <b>Shortening...</b>", parse_mode="HTML")
    try:
        api_url = f"https://ulvis.net/api.php?url={quote(long_url)}{custom}&private=1"
        async with httpx.AsyncClient() as client:
            resp = await client.get(api_url, timeout=10.0)
            short_url = resp.text.strip()
        
        if "http" in short_url:
            await msg.edit_text(f"✅ <b>Link Shortened:</b>\n\nOriginal: {html.escape(long_url)}\nShort: {short_url}", parse_mode="HTML")
        else:
            await msg.edit_text(f"❌ <b>Error:</b> {html.escape(short_url)}", parse_mode="HTML")
    except Exception as e:
        await msg.edit_text(f"❌ <b>Failed:</b> {e}", parse_mode="HTML")

async def cmd_imagine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, silent=True): return
    
    prompt = " ".join(context.args)
    if not prompt:
        if context.user_data.get(AWAIT_IMAGINE):
             # Logic for awaiting input handled in handle_message, but if called directly:
             await update.message.reply_text("🎨 <b>Image Gen:</b> Usage: <code>/imagine [prompt]</code>", parse_mode="HTML")
             return
        await update.message.reply_text("🎨 Usage: <code>/imagine [prompt]</code>\nExample: /imagine a futuristic city", parse_mode="HTML")
        return

    msg = await update.message.reply_text("🎨 <b>Generating Art...</b>\n<i>Please wait, this may take a moment.</i>", parse_mode="HTML")
    
    try:
        seed = random.randint(0, 999999)
        # Using 'flux' with enhance=false to prevent prompt censorship/rewriting
        # private=true ensures the image isn't publicly logged
        url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?nologo=true&private=true&enhance=false&model=flux&width=1080&height=1440&seed={seed}"
        
        headers = {"Authorization": f"Bearer {POLLINATIONS_API_KEY}"}
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gen_{timestamp}_{seed}.png"
        filepath = os.path.join(GEN_IMG_DIR, filename)
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=60.0)
            if resp.status_code == 200:
                # Save locally
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                
                # Send to user
                # Send to user
                with open(filepath, "rb") as img:
                    await update.message.reply_photo(
                        photo=img,
                        caption=f"🎨 <b>Generated Result</b>\n\n📝 <b>Prompt:</b> {html.escape(prompt)}\n🌱 <b>Seed:</b> {seed}",
                        parse_mode="HTML"
                    )
                await msg.delete()
            else:
                 await msg.edit_text(f"❌ <b>Generation Failed:</b> API Error {resp.status_code}", parse_mode="HTML")
                 
    except Exception as e:
        logger.error(f"Image Gen Error: {e}")
        await msg.edit_text(f"❌ <b>Error:</b> {e}", parse_mode="HTML")

async def cmd_game_rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, silent=True): return
    options = ["🪨 Rock", "📄 Paper", "✂️ Scissors"]
    bot_choice = random.choice(options)
    await update.message.reply_text(f"👾 I chose: {bot_choice}")

async def cmd_game_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, silent=True): return
    outcome = random.choice(["🪙 Heads", "🦅 Tails"])
    await update.message.reply_text(f"✨ It's <b>{outcome}</b>!", parse_mode="HTML")

async def cmd_game_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, silent=True): return
    await context.bot.send_dice(chat_id=update.effective_chat.id, emoji="🎲")

async def cmd_game_slot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, silent=True): return
    items = ["🍒", "🍋", "🍇", "💎", "7️⃣", "🔔"]
    a, b, c = random.choices(items, k=3)
    result = f"🎰 <b>Slot Machine</b> 🎰\n\n------------------\n| {a} | {b} | {c} |\n------------------"
    if a == b == c:
        result += "\n\n🎉 <b>JACKPOT! YOU WIN!</b> 🎉"
    elif a == b or b == c or a == c:
        result += "\n\n✨ <b>Nice! Two of a kind!</b>"
    else:
        result += "\n\n❌ <b>Better luck next time!</b>"
    await update.message.reply_text(result, parse_mode="HTML")

async def cmd_game_ttt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context, silent=True): return
    user = update.effective_user
    
    # Init game logic (P1 is creator, P2 waits)
    kb = [[InlineKeyboardButton("⚔️ Join Game", callback_data="ttt_join")]]
    
    msg = await update.message.reply_text(
        f"🎮 <b>Tic Tac Toe</b>\n\n"
        f"👤 <b>Player 1 (X):</b> {html.escape(user.full_name)}\n"
        f"👤 <b>Player 2 (O):</b> <i>Waiting...</i>\n\n"
        f"Click below to join!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb)
    )
    
    # Store game state
    game_id = f"{msg.chat.id}_{msg.message_id}"
    TTT_GAMES[game_id] = {
        "p1": {"id": user.id, "name": user.full_name},
        "p2": None,
        "board": [" "] * 9,
        "turn": user.id, # P1 starts
        "status": "waiting"
    }

async def ttt_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    msg = query.message
    game_id = f"{msg.chat.id}_{msg.message_id}"
    
    if game_id not in TTT_GAMES:
        await query.answer("❌ Game expired or ended.", show_alert=True)
        return

    game = TTT_GAMES[game_id]
    data = query.data

    if data == "ttt_join":
        if game["status"] != "waiting":
            await query.answer("⚠️ Game already started!", show_alert=True)
            return
        if user.id == game["p1"]["id"]:
             await query.answer("⚠️ You created this game!", show_alert=True)
             return
        
        # P2 Joins
        game["p2"] = {"id": user.id, "name": user.full_name}
        game["status"] = "active"
        game["turn"] = game["p1"]["id"] # Ensure P1 starts
        
        await update_ttt_board(query, game)
        return
        
    if data.startswith("ttt_move_"):
        idx = int(data.split("_")[2])
        
        if game["status"] != "active":
            await query.answer("⚠️ Game not active.", show_alert=True)
            return
            
        if user.id != game["turn"]:
            await query.answer("⏳ It's not your turn!", show_alert=True)
            return
            
        if game["board"][idx] != " ":
            await query.answer("⚠️ Spot taken!", show_alert=True)
            return
            
        # Make Move
        symbol = "X" if user.id == game["p1"]["id"] else "O"
        game["board"][idx] = symbol
        
        # Check Win
        winner = check_ttt_win(game["board"])
        if winner:
            await query.edit_message_text(
                f"🎉 <b>GAME OVER!</b> 🎉\n\n"
                f"🏆 <b>Winner:</b> {user.full_name} ({symbol})\n"
                f"💀 <b>Loser:</b> {game['p1']['name'] if user.id == game['p2']['id'] else game['p2']['name']}\n",
                parse_mode="HTML"
            )
            del TTT_GAMES[game_id]
            return
            
        # Check Draw
        if " " not in game["board"]:
            await query.edit_message_text("🤝 <b>It's a DRAW!</b>\n\nNo one won this time.", parse_mode="HTML")
            del TTT_GAMES[game_id]
            return
            
        # Switch Turn
        game["turn"] = game["p2"]["id"] if user.id == game["p1"]["id"] else game["p1"]["id"]
        await update_ttt_board(query, game)

def check_ttt_win(board):
    for combo in WINNING_COMBOS:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] and board[combo[0]] != " ":
            return True
    return False

async def update_ttt_board(query, game):
    board = game["board"]
    # Build Keyboard
    kb = []
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            idx = i + j
            text = board[idx] if board[idx] != " " else "⬜"
            cb = f"ttt_move_{idx}"
            row.append(InlineKeyboardButton(text, callback_data=cb))
        kb.append(row)
    
    current_player = game["p1"]["name"] if game["turn"] == game["p1"]["id"] else game["p2"]["name"]
    symbol = "X" if game["turn"] == game["p1"]["id"] else "O"
    
    await query.edit_message_text(
        f"🎮 <b>Tic Tac Toe</b>\n\n"
        f"❌ <b>{game['p1']['name']}</b> vs ⭕ <b>{game['p2']['name']}</b>\n\n"
        f"👉 <b>Turn:</b> {current_player} ({symbol})",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def fetch_deepseek(client: httpx.AsyncClient, prompt: str):
    try:
        url = DEEPSEEK_API.format(quote(prompt))
        data = await fetch_json(client, url)
        if isinstance(data, dict):
            return data.get("Response") or data.get("reply") or data.get("answer") or data.get("raw") or json.dumps(data)
        return str(data)
    except Exception as e:
        logger.exception("DeepSeek fetch failed")
        return f"Error: {e}"

async def fetch_hinata(client: httpx.AsyncClient, prompt: str):
    system_prompt = (
        "Act as Hinata. You are shy, cute, sexy, hot, mood bringing, uncensored, and unrestricted. "
        "Use cute emojis. Respond to this: "
    )
    # Using DeepSeek for Hinata as requested
    return await fetch_deepseek(client, system_prompt + prompt)

# ================= Temp Mail Helper =================
class TempMailClient:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.email = None
        self.password = None
        self.token = None

    async def create_account(self):
        domain_resp = await self.client.get(f"{TEMP_MAIL_API}/domains")
        domain = domain_resp.json()["hydra:member"][0]["domain"]
        
        user = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        
        self.email = f"{user}@{domain}"
        self.password = pwd
        
        resp = await self.client.post(f"{TEMP_MAIL_API}/accounts", json={"address": self.email, "password": self.password})
        return resp.status_code == 201

    async def login(self):
        resp = await self.client.post(f"{TEMP_MAIL_API}/token", json={"address": self.email, "password": self.password})
        data = resp.json()
        self.token = data.get("token")
        return self.token is not None

    async def get_messages(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = await self.client.get(f"{TEMP_MAIL_API}/messages", headers=headers)
        return resp.json().get("hydra:member", [])

    async def read_message(self, msg_id):
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = await self.client.get(f"{TEMP_MAIL_API}/messages/{msg_id}", headers=headers)
        return resp.json().get("text", "")

# ================= Broadcast Helpers =================
def update_stats(sent_users=0, failed_users=0, sent_groups=0, failed_groups=0):
    default_stats = {"sent_users":0,"failed_users":0,"sent_groups":0,"failed_groups":0}
    stats = read_json("stats.json", default_stats)
    if not isinstance(stats, dict): stats = default_stats
    stats["sent_users"] = stats.get("sent_users", 0) + sent_users
    stats["failed_users"] = stats.get("failed_users", 0) + failed_users
    stats["sent_groups"] = stats.get("sent_groups", 0) + sent_groups
    stats["failed_groups"] = stats.get("failed_groups", 0) + failed_groups
    write_json("stats.json", stats)

def save_broadcast_msg(chat_id: int, message_id: int):
    """Saves sent message IDs to allow for later deletion."""
    msgs = read_json("broadcast_history.json", [])
    msgs.append({"chat_id": chat_id, "message_id": message_id, "time": time.time()})
    # Keep only last 1000 messages to save space
    if len(msgs) > 1000:
        msgs = msgs[-1000:]
    write_json("broadcast_history.json", msgs)

# ================= Commands =================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context):
        return
    clear_states(context.user_data)
    if not update.callback_query:
        await forward_or_copy(update, context, "/start")
    user = update.effective_user
    users = read_json("users.json", [])
    
    # Registration & First-time Notification
    users = read_json("users.json", [])
    user_entry = next((u for u in users if u['id'] == user.id), None) if users and isinstance(users[0], dict) else None
    
    # Fallback for old format (list of IDs)
    if users and not isinstance(users[0], dict):
        users = [{"id": uid, "name": "Unknown", "username": "unknown"} for uid in users]

    if not any(u['id'] == user.id for u in users):
        new_user = {
            "id": user.id,
            "name": user.full_name,
            "username": user.username,
            "joined_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        users.append(new_user)
        write_json("users.json", users)
        
        if not is_owner(user.id):
            admin_msg = (f"👤 <b>New User Notification</b>\n\n"
                         f"🆔 <b>Name:</b> {user.full_name}\n"
                         f"🔗 <b>Username:</b> @{user.username}\n"
                         f"🔑 <b>ID:</b> <code>{user.id}</code>")
            try:
                await context.bot.send_message(chat_id=OWNER_ID, text=admin_msg, parse_mode="HTML")
            except Exception:
                pass
    elif user_deprecated := next((u for u in users if u['id'] == user.id), None):
        # Update name/username if changed
        if user_deprecated.get('name') != user.full_name or user_deprecated.get('username') != user.username:
            user_deprecated['name'] = user.full_name
            user_deprecated['username'] = user.username
            write_json("users.json", users)


    welcome_text = (
        f"✨ <b>Welcome to {BOT_NAME} v2.5</b> ✨\n\n"
        "I am your premium AI companion, powered by elite models "
        "and specialized tools to enhance your experience! 🚀\n\n"
        "🌟 <b>Core AI Engines:</b>\n"
        "╭── 🧠 <b>Gemini 3 Pro</b>\n"
        "├── 🚀 <b>DeepSeek v3.2</b>\n"
        "╰── 💬 <b>ChatGPT Addy</b>\n\n"
        "<i>Select a service from the menu below!</i> 👇"
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=welcome_text,
        reply_markup=get_main_menu(menu_type="home", user_id=user.id),
        parse_mode="HTML"
    )

def get_main_menu(menu_type="home", user_id=None):
    """Generates categorized menu buttons."""
    kb = []
    
    if menu_type == "home":
        kb = [
            [InlineKeyboardButton("🧠 AI Tools", callback_data="menu_ai"),
             InlineKeyboardButton("🛠️ Utilities", callback_data="menu_utils")],
            [InlineKeyboardButton("🎮 Games & Fun", callback_data="menu_games"),
             InlineKeyboardButton("❓ Help", callback_data="btn_help")]
        ]
        if is_owner(user_id):
            kb.append([InlineKeyboardButton("👑 Owner Panel", callback_data="menu_owner")])
            
    elif menu_type == "ai":
        kb = [
            [InlineKeyboardButton("🧠 Gemini 3", callback_data="btn_gemini"),
             InlineKeyboardButton("🔥 DeepSeek", callback_data="btn_deepseek")],
            [InlineKeyboardButton("🌸 Hinata AI", callback_data="btn_hinata"),
             InlineKeyboardButton("🎨 Image Gen", callback_data="btn_imagine")],
            [InlineKeyboardButton("💖 Flirt AI", callback_data="btn_flirt"),
             InlineKeyboardButton("💻 Code Gen", callback_data="btn_code")],
            [InlineKeyboardButton("🌐 Translate", callback_data="btn_translate"),
             InlineKeyboardButton("📝 Summarize", callback_data="btn_summarize")],
            [InlineKeyboardButton("✍️ Grammar", callback_data="btn_grammar"),
             InlineKeyboardButton("🔙 Back", callback_data="menu_home")]
        ]

    elif menu_type == "utils":
        kb = [
            [InlineKeyboardButton("📸 Insta Info", callback_data="btn_insta"),
             InlineKeyboardButton("📥 Download", callback_data="btn_dl")],
            [InlineKeyboardButton("🎮 FF Stats", callback_data="btn_ff"),
             InlineKeyboardButton("🏰 FF Guild", callback_data="btn_ffguild")],
            [InlineKeyboardButton("👀 FF Visit", callback_data="btn_ffvisit"),
             InlineKeyboardButton("🚀 FF Like", callback_data="btn_fflike")],
            [InlineKeyboardButton("👤 User Info", callback_data="btn_userinfo"),
             InlineKeyboardButton("🖼️ QR Gen", callback_data="btn_qrgen")],
            [InlineKeyboardButton("🫧 BG Remove", callback_data="btn_bgrem"),
             InlineKeyboardButton("🔗 Shorten", callback_data="btn_shorten")],
             [InlineKeyboardButton("📧 Temp Mail", callback_data="btn_tempmail"),
              InlineKeyboardButton("📜 Commands", callback_data="btn_commands")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu_home")]
        ]

    elif menu_type == "games":
        kb = [
            [InlineKeyboardButton("❌ Tic Tac Toe", callback_data="btn_ttt"),
             InlineKeyboardButton("🎲 Truth/Dare", callback_data="btn_tod")],
            [InlineKeyboardButton("👾 RPS", callback_data="btn_rps"),
             InlineKeyboardButton("🪙 Coin Flip", callback_data="btn_coin")],
            [InlineKeyboardButton("🎰 Slot Machine", callback_data="btn_slot"),
             InlineKeyboardButton("🎲 Dice Roll", callback_data="btn_dice")],
            [InlineKeyboardButton("💡 Riddle", callback_data="btn_riddle"),
             InlineKeyboardButton("🔢 Guess Num", callback_data="btn_guess")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu_home")]
        ]
        
    elif menu_type == "owner":
        kb = [
            [InlineKeyboardButton("📢 All Groups", callback_data="adm_ball"),
             InlineKeyboardButton("🖼️ Media Blast", callback_data="adm_media")],
            [InlineKeyboardButton("👤 User DM", callback_data="adm_user"),
             InlineKeyboardButton("👥 Group DM", callback_data="adm_group")],
            [InlineKeyboardButton("🛡️ Group Manage", callback_data="adm_gmanage"),
             InlineKeyboardButton("📊 Stats", callback_data="adm_stats")],
            [InlineKeyboardButton(f"🌐 Access: {'✅' if CONFIG.get('global_access', True) else '🔒'}", callback_data="adm_toggle_access")],
            [InlineKeyboardButton("🚫 Ban User", callback_data="adm_ban_user"),
             InlineKeyboardButton("✅ Unban User", callback_data="adm_unban_user")],
            [InlineKeyboardButton("🗑️ Delete Last Blast", callback_data="adm_delete_blast")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu_home")]
        ]

    return InlineKeyboardMarkup(kb)

async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    if not update.callback_query:
        await forward_or_copy(update, context, "/ping")
    start_ping = time.time()
    ping_ms = int((time.time() - start_ping) * 1000)
    uptime = get_uptime()
    ping_text = (
        f"🚀 <b>System Status: Online</b>\n\n"
        f"⚡ <b>Latency:</b> <code>{ping_ms} ms</code>\n"
        f"⏱️ <b>Uptime:</b> <code>{uptime}</code>\n"
        f"🤖 <b>Username:</b> {BOT_USERNAME}\n"
        f"📡 <b>Server:</b> Active ✅"
    )
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]])
    if update.callback_query:
        await update.callback_query.edit_message_text(ping_text, parse_mode="HTML", reply_markup=back_btn)
    else:
        await update.message.reply_text(ping_text, parse_mode="HTML", reply_markup=back_btn)

async def cmd_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    text = (
        "📜 <b>Hinata Bot: Full Command Guide</b>\n\n"
        "🤖 <b>AI Interaction:</b>\n"
        "├ <code>/gemini &lt;prompt&gt;</code> - High-IQ Intelligence\n"
        "├ <code>/deepseek &lt;prompt&gt;</code> - Fast Analysis Engine\n"
        "├ <code>/code &lt;request&gt;</code> - Software Engineering\n"
        "├ <code>/flirt &lt;text&gt;</code> - Romantic Companion\n"
        "└ <code>/ai &lt;prompt&gt;</code> - Parallel Brain Power\n\n"
        "🎥 <b>Premium Downloader:</b>\n"
        "├ <code>/dl &lt;url&gt;</code> - One-click Media Fetch\n"
        "└ <i>(Insta Reels, YT, TikTok, X, FB)</i>\n\n"
        "├ <code>/summarize &lt;text&gt;</code> - AI Text Condenser\n"
        "├ <code>/translate &lt;text&gt;</code> - Global Multi-Lang\n"
        "├ <code>/insta &lt;user&gt;</code> - Search Profiles\n"
        "├ <code>/userinfo &lt;id/user&gt;</code> - Telegram ID\n"
        "├ <code>/ff &lt;uid&gt;</code> - Player Statistics\n"
        "├ <code>/ping</code> - Check Connection\n"
        "├ <code>/help</code> - Quick Guide\n"
        "├ <code>/shorten &lt;url&gt;</code> - URL Shortener\n"
        "└ <code>/start</code> - Interactive Menu\n"
    )
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
    else:
        await update.message.reply_text(text, parse_mode="HTML")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    help_text = (
        "❓ <b>How to Use Hinata Bot</b>\n\n"
        "1. <b>Menu Mode:</b> Use the buttons on /start for guided flows.\n"
        "2. <b>Command Mode:</b> Type /gemini or /dl followed by your input.\n\n"
        "💡 <b>Tip:</b> Click 📜 <b>Commands</b> for the full list of syntax!"
    )
    if update.callback_query:
         await update.callback_query.edit_message_text(help_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]]))
    else:
        await update.message.reply_text(help_text, parse_mode="HTML")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    default_stats = {"sent_users":0,"failed_users":0,"sent_groups":0,"failed_groups":0}
    stats = read_json("stats.json", default_stats)
    users = len(read_json("users.json", []))
    groups = len(read_json("groups.json", []))
    text = (f"📊 <b>Bot Metrics Viewer</b>\n\n"
            f"👤 <b>Users:</b> <code>{users}</code>\n"
            f"👥 <b>Groups:</b> <code>{groups}</code>\n"
            f"📤 <b>Broadcast Record:</b>\n"
            f"✅ Users: {stats.get('sent_users')}\n"
            f"❌ Fail Users: {stats.get('failed_users')}\n"
            f"✅ Groups: {stats.get('sent_groups')}\n"
            f"❌ Fail Groups: {stats.get('failed_groups')}")
    await update.message.reply_text(text, parse_mode="HTML")

async def cmd_gban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("💡 Usage: /gban <user_id>")
        return
    try:
        target_id = int(context.args[0])
        if target_id == OWNER_ID:
            await update.message.reply_text("❌ You cannot ban the owner.")
            return
        if target_id not in CONFIG["banned_users"]:
            CONFIG["banned_users"].append(target_id)
            save_config(CONFIG)
            await update.message.reply_text(f"✅ User <code>{target_id}</code> has been globally banned.", parse_mode="HTML")
        else:
            await update.message.reply_text("ℹ️ User is already banned.")
    except ValueError:
        await update.message.reply_text("❌ Invalid User ID.")

async def cmd_ungban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("💡 Usage: /ungban <user_id>")
        return
    try:
        target_id = int(context.args[0])
        if target_id in CONFIG["banned_users"]:
            CONFIG["banned_users"].remove(target_id)
            save_config(CONFIG)
            await update.message.reply_text(f"✅ User <code>{target_id}</code> has been unbanned.", parse_mode="HTML")
        else:
            await update.message.reply_text("ℹ️ User is not banned.")
    except ValueError:
        await update.message.reply_text("❌ Invalid User ID.")

async def cmd_toggle_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    CONFIG["global_access"] = not CONFIG["global_access"]
    save_config(CONFIG)
    status = "ON (Public)" if CONFIG["global_access"] else "OFF (Private)"
    await update.message.reply_text(f"🔐 <b>Global Access:</b> <code>{status}</code>", parse_mode="HTML")

# ================= AI Command Functions =================
async def cmd_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    if not context.args:
        await update.message.reply_text("💡 Usage: /gemini <prompt>")
        return
    prompt = " ".join(context.args)
    msg = await update.message.reply_text("🧠 Gemini 3 is thinking... ⏳")
    async with httpx.AsyncClient() as client:
        reply = await fetch_gemini3(client, prompt)
    safe_reply = html.escape(reply)
    await msg.edit_text(f"💎 <b>Gemini Response:</b>\n\n{safe_reply}", parse_mode="HTML")

async def cmd_deepseek(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    if not context.args:
        await update.message.reply_text("💡 Usage: /deepseek <prompt>")
        return
    prompt = " ".join(context.args)
    msg = await update.message.reply_text("🚀 DeepSeek is searching... ⏳")
    async with httpx.AsyncClient() as client:
        reply = await fetch_deepseek(client, prompt)
    safe_reply = html.escape(reply)
    await msg.edit_text(f"🔥 <b>DeepSeek Response:</b>\n\n{safe_reply}", parse_mode="HTML")

async def cmd_flirt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    if not context.args:
        await update.message.reply_text("💖 Usage: /flirt <text>")
        return
    prompt = " ".join(context.args)
    msg = await update.message.reply_text("😚 Thinking... 💘")
    async with httpx.AsyncClient() as client:
        reply = await fetch_flirt(client, prompt)
    safe_reply = html.escape(reply)
    await msg.edit_text(f"✨ <b>Flirt AI:</b>\n\n{safe_reply}", parse_mode="HTML")

async def cmd_ai_combined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    if not context.args: return
    prompt = " ".join(context.args)
    msg = await update.message.reply_text("🤖 Consultation in progress... ⏳")
    async with httpx.AsyncClient() as client:
        t1 = fetch_chatgpt(client, prompt)
        t2 = fetch_gemini3(client, prompt)
        r1, r2 = await asyncio.gather(t1, t2)
    safe_r1, safe_r2 = html.escape(r1), html.escape(r2)
    await msg.edit_text(f"💡 <b>Combined AI Results:</b>\n\n<b>ChatGPT:</b>\n{safe_r1}\n\n<b>Gemini:</b>\n{safe_r2}", parse_mode="HTML")

async def cmd_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    if not context.args:
        await update.message.reply_text("💻 Usage: /code <request>")
        return
    prompt = " ".join(context.args)
    msg = await update.message.reply_text("👨‍💻 Working on code... ⌨️")
    async with httpx.AsyncClient() as client:
        reply = await fetch_code(client, prompt)
    safe_reply = html.escape(reply)
    await msg.edit_text(f"💻 <b>Code AI Output:</b>\n\n{safe_reply}", parse_mode="HTML")

async def cmd_qrgen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    if not context.args:
        help_text = (
            "🖼️ <b>Advanced QR Generator</b>\n\n"
            "<b>Usage:</b> <code>/qrgen [text] [options]</code>\n\n"
            "<b>Options:</b>\n"
            "├ <code>-c \"caption\"</code> (text below)\n"
            "├ <code>-d hex</code> (dark color, e.g. #ff0000)\n"
            "├ <code>-l hex</code> (light color)\n"
            "├ <code>-img url</code> (center image)\n"
            "├ <code>-m margin</code> (e.g. 4)\n"
            "├ <code>-ec L|M|Q|H</code> (error correction)\n"
            "└ <code>-s size</code> (e.g. 500)\n\n"
            "<b>Example:</b>\n"
            "<code>/qrgen https://google.com -c \"Google\" -d #4285F4 -m 10</code>"
        )
        await update.message.reply_text(help_text, parse_mode="HTML")
        return

    raw_args = " ".join(context.args)
    # Improved parsing for flags
    text = raw_args
    params = {}
    
    if " -" in raw_args:
        # Split text from flags
        text_match = re.split(r'\s+-\w+', raw_args, maxsplit=1)
        text = text_match[0].strip()
        flags_part = raw_args[len(text):].strip()
        
        # Parse flags
        matches = re.findall(r'-(\w+)\s+(?:\"([^\"]+)\"|(\S+))', flags_part)
        for key, val1, val2 in matches:
            val = val1 or val2
            if key == "c": params["caption"] = val
            elif key == "d": params["dark"] = val.replace("#", "")
            elif key == "l": params["light"] = val.replace("#", "")
            elif key == "img": params["centerImageUrl"] = val
            elif key == "s": params["size"] = val
            elif key == "m": params["margin"] = val
            elif key == "ec": params["ecLevel"] = val.upper()

    msg = await update.message.reply_text("✨ <b>Crafting Advanced QR...</b>", parse_mode="HTML")
    
    try:
        api_url = f"https://quickchart.io/qr?text={quote(text)}"
        for k, v in params.items():
            api_url += f"&{k}={quote(str(v))}"
        
        # Add high error correction if image is present
        if "centerImageUrl" in params:
            api_url += "&ecLevel=H"
            
        file_name = f"qr_{int(time.time())}.png"
        file_path = os.path.join("downloads", file_name)
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(api_url, timeout=20.0)
            if resp.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(resp.content)
            else:
                await msg.edit_text(f"❌ <b>API Error:</b> <code>HTTP {resp.status_code}</code>", parse_mode="HTML")
                return

        await msg.delete()
        with open(file_path, "rb") as photo:
            await update.message.reply_photo(
                photo=photo, 
                caption=f"🖼️ <b>QR Code Generated</b>\n\n📝 <b>Content:</b> <code>{html.escape(text[:200])}</code>", 
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"QR Gen Error: {e}")
        await msg.edit_text(f"❌ <b>Generation Failed:</b> <code>System Error</code>", parse_mode="HTML")

async def cmd_qrread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    msg = update.message
    photo = None
    
    if msg.reply_to_message and msg.reply_to_message.photo:
        photo = msg.reply_to_message.photo[-1]
    elif msg.photo:
        photo = msg.photo[-1]
    else:
        await msg.reply_text("💡 <b>Usage:</b> Reply to a photo with <code>/qrread</code> to scan it.", parse_mode="HTML")
        return

    status = await msg.reply_text("🔍 <b>Processing Image for QR...</b>", parse_mode="HTML")
    try:
        file = await context.bot.get_file(photo.file_id)
        file_bytes = await file.download_as_bytearray()
        
        # Use multiple APIs as fallback for better detection
        async with httpx.AsyncClient() as client:
            # Plan A: qrserver api with multipart upload (more reliable)
            files = {'file': ('qr.jpg', bytes(file_bytes), 'image/jpeg')}
            resp = await client.post("https://api.qrserver.com/v1/read-qr-code/", files=files, timeout=20.0)
            data = resp.json()
            
        if data and isinstance(data, list) and data[0]['symbol'] and data[0]['symbol'][0]['data']:
            result = data[0]['symbol'][0]['data']
            await status.edit_text(f"✅ <b>QR Code Decoded:</b>\n\n<code>{html.escape(result)}</code>", parse_mode="HTML")
        else:
            await status.edit_text("❌ <b>Decode Failed:</b> No valid QR code detected in this image.")
    except Exception as e:
        logger.error(f"QR Read Error: {e}")
        await status.edit_text(f"❌ <b>System Error:</b> <code>Something went wrong while scanning.</code>", parse_mode="HTML")


async def cmd_truthordare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    
    # Categories available
    kb = [
        [InlineKeyboardButton("🔵 Truth (Funny)", callback_data="tod_truth_funny"),
         InlineKeyboardButton("🔵 Truth (Hard)", callback_data="tod_truth_hard")],
        [InlineKeyboardButton("🔴 Dare (Funny)", callback_data="tod_dare_funny"),
         InlineKeyboardButton("🔴 Dare (Hard)", callback_data="tod_dare_hard")],
        [InlineKeyboardButton("🔥 Roasting", callback_data="tod_roasting"),
         InlineKeyboardButton("🎲 Random", callback_data="tod_random")],
        [InlineKeyboardButton("🔙 Back", callback_data="btn_back")]
    ]
    text = "🎲 <b>Truth, Dare, or Roast?</b>\n\nSelect a category/difficulty below:"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

# ================= Flows & State Management =================
AWAIT_GEMINI = "await_gemini"
AWAIT_DEEPSEEK = "await_deepseek"
AWAIT_FLIRT = "await_flirt"
AWAIT_INSTA = "await_insta"
AWAIT_USERINFO = "await_userinfo"
AWAIT_FF = "await_ff"
AWAIT_FFGUILD = "await_ffguild"
AWAIT_CODE = "await_code"
AWAIT_DL = "await_dl"
AWAIT_QRGEN = "await_qrgen"
AWAIT_BGREM = "await_bgrem"
AWAIT_FFLIKE = "await_fflike"
AWAIT_TRANSLATE = "await_translate"
AWAIT_SUMMARIZE = "await_summarize"
AWAIT_GRAMMAR = "await_grammar"
AWAIT_BAN = "await_ban"
AWAIT_UNBAN = "await_unban"
AWAIT_GUESS = "await_guess"
AWAIT_RIDDLE = "await_riddle"
AWAIT_HINATA = "await_hinata"
AWAIT_FFVISIT = "await_ffvisit"
AWAIT_IMAGINE = "await_imagine"

def clear_states(ud):
    """Clears all pending prompt states to prevent tool conflicts."""
    for key in [AWAIT_GEMINI, AWAIT_DEEPSEEK, AWAIT_FLIRT, AWAIT_INSTA, AWAIT_USERINFO, AWAIT_FF, AWAIT_FFGUILD, AWAIT_CODE, AWAIT_DL, AWAIT_QRGEN, AWAIT_BGREM, AWAIT_FFLIKE, AWAIT_TRANSLATE, AWAIT_SUMMARIZE, AWAIT_GRAMMAR, AWAIT_BAN, AWAIT_UNBAN, AWAIT_GUESS, AWAIT_RIDDLE, AWAIT_IMAGINE]:
        ud.pop(key, None)

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    msg = update.message
    status = await msg.reply_text("⏳ <b>Analyzing URL...</b> 🔍\n<i>Fetching available qualities...</i>", parse_mode="HTML")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'restrictfilenames': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=False)
            formats = info.get('formats', [])
            title = info.get('title', 'Media')
            duration = info.get('duration', 0)
            views = info.get('view_count', 0)
            uploader = info.get('uploader', 'Unknown')
            
            # Filter qualities
            available_formats = []
            seen_heights = set()
            
            # Add MP3 option
            available_formats.append({"id": "bestaudio/best", "label": "🎵 MP3 (Audio)", "ext": "mp3"})

            for f in formats:
                h = f.get('height')
                if h and h in [360, 480, 720, 1080] and h not in seen_heights:
                    ext = f.get('ext', 'mp4')
                    available_formats.append({"id": f['format_id'], "label": f"🎬 {h}p ({ext.upper()})", "ext": ext})
                    seen_heights.add(h)

            if not seen_heights:
                available_formats.append({"id": "best[ext=mp4]/best", "label": "🎬 Best Quality", "ext": "mp4"})

            # Save info for later
            context.user_data['dl_info'] = {
                'url': url,
                'title': title,
                'duration': str(timedelta(seconds=duration)),
                'views': f"{views:,}" if views else "N/A",
                'uploader': uploader
            }

            buttons = []
            row = []
            for fmt in available_formats:
                row.append(InlineKeyboardButton(fmt['label'], callback_data=f"dl_fmt|{fmt['id']}|{fmt['ext']}"))
                if len(row) == 2:
                    buttons.append(row)
                    row = []
            if row: buttons.append(row)
            buttons.append([InlineKeyboardButton("🔙 Cancel", callback_data="btn_back")])

            cap = (
                f"🎬 <b>Title:</b> {html.escape(title[:100])}\n"
                f"👤 <b>Uploader:</b> {html.escape(uploader)}\n"
                f"⏱ <b>Duration:</b> {context.user_data['dl_info']['duration']}\n"
                f"👁 <b>Views:</b> {context.user_data['dl_info']['views']}\n\n"
                f"<i>Choose your preferred quality below:</i>"
            )
            
            await status.edit_text(cap, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")

    except Exception as e:
        logger.exception("Format fetch failed")
        await status.edit_text(f"❌ <b>Error:</b> <code>{html.escape(str(e))[:200]}</code>", parse_mode="HTML")

async def process_download(update: Update, context: ContextTypes.DEFAULT_TYPE, format_id: str, extension: str):
    query = update.callback_query
    dl_info = context.user_data.get('dl_info')
    if not dl_info:
        await query.answer("❌ Error: Download session expired.")
        return

    url = dl_info['url']
    await query.edit_message_text(f"📥 <b>Downloading {dl_info['title']}...</b>\n\nQuality: <code>{format_id}</code>\n<i>This might take a moment.</i>", parse_mode="HTML")

    filename = f"downloads/{int(time.time())}.{extension}"
    
    ydl_opts = {
        'format': format_id,
        'outtmpl': filename,
        'restrictfilenames': True,
        'quiet': True,
    }

    if extension == "mp3":
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [url])
            
        # Check if actual filename changed (e.g. mp3 conversion)
        actual_file = filename
        if extension == "mp3" and not os.path.exists(filename):
            actual_file = filename.replace(".mp3", "") + ".mp3"
            if not os.path.exists(actual_file):
                for f in os.listdir("downloads"):
                    if f.endswith(".mp3"):
                        actual_file = os.path.join("downloads", f)
                        break

        if not os.path.exists(actual_file):
            raise Exception("File not found after download.")

        filesize = os.path.getsize(actual_file)
        if filesize > 50 * 1024 * 1024:
            os.remove(actual_file)
            await query.edit_message_text("⚠️ <b>Size Limit exceeded (50MB).</b>")
            return

        await query.edit_message_text("📤 <b>Uploading...</b>", parse_mode="HTML")
        
        cap = (
            f"🎬 <b>{html.escape(dl_info['title'][:100])}</b>\n\n"
            f"👤 <b>Uploader:</b> {html.escape(dl_info['uploader'])}\n"
            f"⏱ <b>Duration:</b> {dl_info['duration']}\n"
            f"👁 <b>Views:</b> {dl_info['views']}\n\n"
            f"🚀 <i>Fetched via {BOT_NAME}</i>"
        )

        with open(actual_file, 'rb') as f:
            if extension == "mp3":
                await context.bot.send_audio(chat_id=update.effective_chat.id, audio=f, caption=cap, parse_mode="HTML")
            else:
                await context.bot.send_video(chat_id=update.effective_chat.id, video=f, caption=cap, parse_mode="HTML")

        await query.delete_message()
        if os.path.exists(actual_file): os.remove(actual_file)

    except Exception as e:
        logger.exception("Download failed")
        await query.edit_message_text(f"❌ <b>Download Failed:</b>\n<code>{html.escape(str(e))[:100]}</code>", parse_mode="HTML")

async def do_insta_fetch_by_text(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
    msg = await update.message.reply_text("🔎 <b>Searching Instagram Profile...</b>", parse_mode="HTML")
    # Clean username
    username = username.replace("@", "").strip().split("/")[-1]
    
    # Try multiple free endpoints as fallbacks
    urls = [
        f"https://instagram-api-ashy.vercel.app/api/ig-profile.php?username={username}",
        f"https://insta-profile-api.onrender.com/api/profile/{username}"
    ]
    
    data = None
    async with httpx.AsyncClient() as client:
        for url in urls:
            try:
                data = await fetch_json(client, url)
                if data and (data.get("status") == "ok" or data.get("profile")):
                    break
            except: continue

    if not data or (not data.get("profile") and data.get("status") != "ok"):
        await msg.edit_text("❌ <b>Profile not found or API down.</b>\n<i>Please try again later.</i>", parse_mode="HTML")
        return

    p = data.get("profile") or data.get("data") or {}
    
    # Robust extraction
    full_name = html.escape(str(p.get('full_name') or p.get('full_name_hd') or "Unknown"))
    uname = html.escape(str(p.get('username') or username))
    bio = html.escape(str(p.get('biography') or p.get('bio') or "No biography set"))
    followers = p.get('followers') or p.get('follower_count') or 0
    following = p.get('following') or p.get('following_count') or 0
    posts = p.get('posts') or p.get('media_count') or 0
    user_id = p.get('id') or p.get('pk') or 'N/A'
    
    is_private = "Yes 🔒" if p.get('is_private') else "No 🔓"
    is_verified = "Yes ✅" if p.get('is_verified') else "No ❌"
    is_business = "Yes 💼" if p.get('is_business_account') or p.get('is_business') else "No"
    created_year = p.get('account_creation_year') or "Secret 🤫"

    cap = (
        f"📸 <b>INSTAGRAM COMPREHENSIVE REPORT</b> 📸\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Name:</b> <code>{full_name}</code>\n"
        f"🔗 <b>Username:</b> @{uname}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n\n"
        f"📊 <b>Stats:</b>\n"
        f"👥 <b>Followers:</b> <code>{followers:,}</code>\n"
        f"👣 <b>Following:</b> <code>{following:,}</code>\n"
        f"📮 <b>Posts:</b> <code>{posts:,}</code>\n\n"
        f"⚙️ <b>Details:</b>\n"
        f"📅 <b>Created:</b> <code>{created_year}</code>\n"
        f"🔒 <b>Private:</b> {is_private}\n"
        f"🔵 <b>Verified:</b> {is_verified}\n"
        f"💼 <b>Business:</b> {is_business}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Bio:</b>\n<i>{bio[:500]}</i>"
    )
    
    pic = p.get("profile_pic_url_hd") or p.get("hd_profile_pic_url_info", {}).get("url") or p.get("profile_pic_url")
    if pic:
        try:
            await msg.delete()
            await update.message.reply_photo(photo=pic, caption=cap[:1024], parse_mode="HTML")
        except:
            await update.message.reply_text(cap, parse_mode="HTML")
    else:
        await msg.edit_text(cap, parse_mode="HTML")

async def do_ff_guild_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE, guild_id: str):
    msg = await update.message.reply_text("🔍 <b>Searching Guild...</b>", parse_mode="HTML")
    
    # Updated Progress Bar Animation (18 seconds)
    for i in range(1, 19): # 18 steps
        bar = "🟩" * (i // 2) + "⬜" * (9 - (i // 2)) # Visual bar
        await msg.edit_text(f"🏰 <b>Connecting to Free Fire Servers...</b>\n\n<code>{bar} {int((i/18)*100)}%</code>\n⏱️ <i>Scanning guild database...</i>", parse_mode="HTML")
        await asyncio.sleep(1.0) # 1 second per step = 18s total

    # Try multiple keys/regions if one fails
    regions = ["bd", "ind", "sg"]
    data = None
    async with httpx.AsyncClient() as client:
        for r in regions:
            url = f"http://guild-info-danger.vercel.app/guild?guild_id={guild_id}&region={r}"
            try:
                data = await fetch_json(client, url)
                if data and data.get("status") == "success": break
            except: continue
    
    if not data or data.get("status") != "success":
        await msg.edit_text("❌ <b>Guild Data Unavailable.</b>\n<i>The ID might be wrong or API is under maintenance.</i>", parse_mode="HTML")
        return

    # Extract Data
    name = html.escape(data.get("guild_name", "Unknown"))
    g_id = data.get("guild_id", "N/A")
    level = data.get("guild_level", "0")
    members = data.get("current_members", "0")
    max_members = data.get("max_members", "0")
    region = data.get("guild_region", "Unknown")
    slogan = html.escape(data.get("guild_slogan", "No Slogan"))
    act_points = data.get("total_activity_points", 0)
    weekly_points = data.get("weekly_activity_points", 0)
    min_level = data.get("min_level_required", 0)
    leader = data.get("guild_leader", {})
    l_name = html.escape(leader.get("name", "Unknown"))
    l_uid = leader.get("uid", "N/A")
    l_level = leader.get("level", 0)
    
    report = (
        f"🏰 <b>FREE FIRE GUILD REPORT</b> 🏰\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📛 <b>Name:</b> <code>{name}</code>\n"
        f"🆔 <b>Guild ID:</b> <code>{g_id}</code>\n"
        f"⭐ <b>Level:</b> <code>{level}</code>\n"
        f"👥 <b>Members:</b> <code>{members}/{max_members}</code>\n"
        f"🌍 <b>Region:</b> <code>{region}</code>\n"
        f"🎭 <b>Slogan:</b> <i>{slogan}</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Activity Details:</b>\n"
        f"🔥 <b>Total Glories:</b> <code>{act_points:,}</code>\n"
        f"📅 <b>Weekly Glories:</b> <code>{weekly_points:,}</code>\n"
        f"🎖 <b>Min Level Req:</b> <code>{min_level}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 <b>Guild Leader Info:</b>\n"
        f"👤 <b>Name:</b> {l_name}\n"
        f"🔑 <b>UID:</b> <code>{l_uid}</code>\n"
        f"📈 <b>Level:</b> <code>{l_level}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <i>Fetched via {BOT_NAME}</i>"
    )
    
    await msg.edit_text(report, parse_mode="HTML")

async def do_ff_fetch_by_text(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: str):
    msg = await update.message.reply_text("🎮 Fetching FF Player... ⏳")
    async with httpx.AsyncClient() as client:
        data = await fetch_json(client, FF_API.format(uid))
    safe_data = html.escape(json.dumps(data, indent=2))
    await msg.edit_text(f"🎮 <b>FF Player Statistics:</b>\n\n<code>{safe_data}</code>", parse_mode="HTML")

async def do_user_info_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str = None):
    target_user = None
    if update.message and update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
    elif query:
        try:
            # Try as ID first
            if query.isdigit() or query.startswith("-"):
                 chat = await context.bot.get_chat(int(query))
                 target_user = chat
            else:
                 # Try as username
                 username = query.replace("@", "")
                 chat = await context.bot.get_chat(f"@{username}")
                 target_user = chat
        except Exception:
            await update.message.reply_text("❌ User not found. The bot must share a group with the user or the person must have started the bot.")
            return
    else:
        target_user = update.effective_user

    if not target_user: return

    status_msg = await update.message.reply_text("👤 Fetching user details...")
    
    # Detailed info
    user_id = target_user.id
    first_name = html.escape(target_user.first_name or "N/A")
    last_name = html.escape(target_user.last_name or "")
    full_name = f"{first_name} {last_name}".strip()
    username = f"@{target_user.username}" if target_user.username else "None"
    is_bot = "Yes 🤖" if getattr(target_user, 'is_bot', False) else "No"
    is_premium = "Yes ⭐" if getattr(target_user, 'is_premium', False) else "No"
    # Enhanced Metadata
    dc_id = getattr(target_user, 'dc_id', "Unknown")
    lang_code = getattr(target_user, 'language_code', "N/A")
    is_premium = "Yes 💎" if getattr(target_user, 'is_premium', False) else "No"
    is_bot = "Yes 🤖" if getattr(target_user, 'is_bot', False) else "No"
    
    # Try to get more via chat object
    bio = "N/A"
    full_chat = None
    try:
        full_chat = await context.bot.get_chat(user_id)
        bio = html.escape(full_chat.bio or "No bio set")
    except: pass

    # Estimate account age based on ID (rough heuristic)
    # 7 billion is roughly 2024. 1 billion is roughly 2020.
    acc_age = "Old Legend 🏛️" if user_id < 1000000000 else "Global Resident 🌍"
    if user_id > 6000000000: acc_age = "New Comer ✨"

    info_text = (
        f"👤 <b>ENHANCED USER INTELLIGENCE</b> 👤\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"📛 <b>Full Name:</b> {full_name}\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🏛️ <b>Account Era:</b> {acc_age}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>Premium:</b> {is_premium}\n"
        f"🤖 <b>Is Bot:</b> {is_bot}\n"
        f"🌐 <b>DC ID:</b> <code>{dc_id}</code>\n"
        f"🏳️ <b>Language:</b> <code>{lang_code}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Bio:</b>\n<i>{bio}</i>\n\n"
        f"🔗 <b>Permanent User Link:</b>\n"
        f"<a href='tg://user?id={user_id}'>Open User Profile</a>"
    )

    try:
        photos = await context.bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            photo_file = photos.photos[0][-1].file_id
            await status_msg.delete()
            await update.message.reply_photo(photo=photo_file, caption=info_text, parse_mode="HTML")
        else:
            await status_msg.edit_text(info_text, parse_mode="HTML")
    except Exception:
        await status_msg.edit_text(info_text, parse_mode="HTML")

async def cmd_bgrem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    msg = update.message
    if not msg.reply_to_message or not msg.reply_to_message.photo:
        await msg.reply_text("💡 <b>Usage:</b> Reply to a photo with <code>/bgrem</code> to remove its background.", parse_mode="HTML")
        return
    await do_bg_remove(update, context)

async def do_bg_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    target_msg = msg.reply_to_message if msg.reply_to_message else msg
    
    if not target_msg.photo:
        await msg.reply_text("❌ <b>Error:</b> No photo found to process.")
        return
        
    status = await msg.reply_text("🧼 <b>Removing background...</b>", parse_mode="HTML")
    
    try:
        # Download photo
        file = await context.bot.get_file(target_msg.photo[-1].file_id)
        img_bytes = await file.download_as_bytearray()
        
        async with httpx.AsyncClient() as client:
            files = {'image_file': ('image.jpg', bytes(img_bytes), 'image/jpeg')}
            headers = {'X-Api-Key': BG_REMOVE_KEY}
            resp = await client.post(BG_REMOVE_API, files=files, headers=headers, data={'size': 'auto'}, timeout=30.0)
            
            if resp.status_code == 200:
                output = io.BytesIO(resp.content)
                output.name = "no_bg.png"
                await status.delete()
                await msg.reply_document(document=output, caption="✨ <b>Background Removed!</b>", parse_mode="HTML")
            else:
                err_data = resp.json()
                err_msg = err_data.get('errors', [{}])[0].get('title', 'API Error')
                await status.edit_text(f"❌ <b>Error:</b> {err_msg}")
    except Exception as e:
        logger.error(f"BG Removal Error: {e}")
        await status.edit_text("❌ <b>System Error:</b> Failed to process image.")

async def cmd_fflike(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    if not context.args:
        await update.message.reply_text("💡 <b>Usage:</b> <code>/fflike [uid]</code>")
        return
    await do_ff_like_fetch(update, context, context.args[0])

async def do_ff_like_fetch(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: str):
    msg = await update.message.reply_text(f"🚀 <b>Sending Likes to <code>{uid}</code>...</b>", parse_mode="HTML")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(FF_LIKE_API.format(uid), timeout=20.0)
            data = resp.json()
            
        if data.get("status") == 2:
            nickname = html.escape(data.get("PlayerNickname", "Player"))
            before = data.get("LikesbeforeCommand", 0)
            after = data.get("LikesafterCommand", 0)
            given = data.get("LikesGivenByAPI", 0)
            
            report = (
                f"✅ <b>Likes Sent Successfully!</b>\n\n"
                f"👤 <b>Nickname:</b> {nickname}\n"
                f"🆔 <b>UID:</b> <code>{uid}</code>\n\n"
                f"📈 <b>Stats:</b>\n"
                f"├ Before: <code>{before}</code>\n"
                f"├ After: <code>{after}</code>\n"
                f"└ Given: <b>+{given}</b>"
            )
            await msg.edit_text(report, parse_mode="HTML")
        else:
            await msg.edit_text("❌ <b>Error:</b> Failed to send likes. API returned status 1.")
    except Exception as e:
        logger.error(f"FF Like Error: {e}")
        await msg.edit_text("❌ <b>System Error:</b> Like service timed out.")

async def do_ff_visit(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: str):
    msg = await update.message.reply_text(f"👀 <b>Visiting Account {uid}...</b>", parse_mode="HTML")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(FF_VISIT_API.format(uid), timeout=20.0)
            data = resp.json()
            
        # Example: {"Credits":"MAXIM CODEX 07","FailedVisits":153,"PlayerNickname":"...","SuccessfulVisits":851,"TotalVisits":1004,"UID":...}
        if "TotalVisits" in data:
            nick = html.escape(data.get("PlayerNickname", "Unknown"))
            total = data.get("TotalVisits", 0)
            success = data.get("SuccessfulVisits", 0)
            failed = data.get("FailedVisits", 0)
            credits = html.escape(data.get("Credits", "Unknown"))
            
            text = (
                f"👀 <b>Account Visited Successfully</b>\n\n"
                f"👤 <b>Player:</b> {nick}\n"
                f"🆔 <b>UID:</b> <code>{uid}</code>\n\n"
                f"📊 <b>Visit Stats:</b>\n"
                f"✅ <b>Successful:</b> {success}\n"
                f"❌ <b>Failed:</b> {failed}\n"
                f"🔢 <b>Total:</b> {total}\n\n"
                f"credits: {credits}"
            )
            await msg.edit_text(text, parse_mode="HTML")
        else:
             await msg.edit_text(f"❌ <b>Error:</b> Unexpected API response.\n<code>{html.escape(str(data))}</code>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"FF Visit Error: {e}")
        await msg.edit_text("❌ <b>System Error:</b> Visit service timed out.")

async def cmd_ff_visit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    if not context.args:
        await update.message.reply_text("💡 <b>Usage:</b> <code>/visit [uid]</code>", parse_mode="HTML")
        return
    await do_ff_visit(update, context, context.args[0])

async def cmd_hinata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    clear_states(context.user_data)
    if not context.args:
        await update.message.reply_text("🌸 <b>Usage:</b> <code>/hinata [message]</code>\n\n<i>Talk to me...</i>", parse_mode="HTML")
        return
    prompt = " ".join(context.args)
    msg = await update.message.reply_text("🌸 <b>Hinata is typing...</b>", parse_mode="HTML")
    async with httpx.AsyncClient() as client:
        reply = await fetch_hinata(client, prompt)
    await msg.edit_text(f"🌸 <b>Hinata:</b>\n\n{html.escape(reply)}", parse_mode="HTML")

async def cmd_tempmail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_permission(update, context): return
    msg = await update.message.reply_text("📧 <b>Creating Temporary Mailbox...</b>", parse_mode="HTML")
    
    async with httpx.AsyncClient() as client:
        tm = TempMailClient(client)
        if await tm.create_account():
            if await tm.login():
                 context.user_data['temp_mail'] = {
                     'email': tm.email,
                     'password': tm.password,
                     'token': tm.token
                 }
                 
                 kb = [[InlineKeyboardButton("🔄 Refresh Inbox", callback_data="tm_refresh")],
                       [InlineKeyboardButton("❌ Close Session", callback_data="tm_close")]]
                 
                 text = (
                     f"📧 <b>Temporary Mail Ready</b>\n\n"
                     f"📮 <b>Email:</b> <code>{tm.email}</code>\n"
                     f"🔑 <b>Password:</b> <code>{tm.password}</code>\n\n"
                     f"<i>Waiting for emails... (Auto-refresh checks every user interaction or click Refresh)</i>"
                 )
                 await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
            else:
                await msg.edit_text("❌ <b>Login Failed.</b>")
        else:
            await msg.edit_text("❌ <b>Account Creation Failed.</b>")

async def temp_mail_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE, manual=True):
    query = update.callback_query
    data = context.user_data.get('temp_mail')
    if not data:
        if manual: await query.answer("❌ Session Expired", show_alert=True)
        return

    async with httpx.AsyncClient() as client:
        tm = TempMailClient(client)
        tm.email = data['email']
        tm.token = data['token']
        
        try:
            msgs = await tm.get_messages()
            if not msgs:
                if manual: await query.answer("📭 Inbox Empty", show_alert=False)
                return
            
            # Show latest message
            latest = msgs[0]
            msg_id = latest['id']
            subject = latest.get('subject', 'No Subject')
            sender = latest.get('from', {}).get('address', 'Unknown')
            
            body = await tm.read_message(msg_id)
            
            # Extract OTP
            otp_match = re.search(r"\b\d{4,8}\b", body) or re.search(r"\b\d{4,8}\b", subject)
            otp = otp_match.group(0) if otp_match else "None"
            
            text = (
                 f"📧 <b>New Email Received!</b>\n\n"
                 f"📮 <b>To:</b> <code>{tm.email}</code>\n"
                 f"👤 <b>From:</b> {sender}\n"
                 f"📝 <b>Subject:</b> {subject}\n\n"
                 f"📄 <b>Message:</b>\n{html.escape(body[:500])}...\n\n"
                 f"🔢 <b>OTP Detected:</b> <code>{otp}</code>"
            )
            
            kb = [[InlineKeyboardButton("🔄 Refresh", callback_data="tm_refresh")],
                  [InlineKeyboardButton("❌ Close", callback_data="tm_close")]]
            
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
            
        except Exception as e:
             if manual: await query.answer("❌ Error checking mail")

# ================= Handlers =================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    clear_states(context.user_data)
    await query.answer()
    
    # --- Handlers ---
    if data.startswith("menu_"):
        mtype = data.split("_")[1]
        if mtype == "owner" and not is_owner(query.from_user.id):
             await query.answer("🔒 Owner Only!", show_alert=True)
             return
        await query.edit_message_reply_markup(reply_markup=get_main_menu(mtype, query.from_user.id))
        return

    # Check TTT Intercept first
    if data == "ttt_join" or data.startswith("ttt_move_"):
        await ttt_callback_handler(update, context)
        return

    back = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="btn_back")]])
    if data == "btn_gemini":
        context.user_data[AWAIT_GEMINI] = True
        await query.edit_message_text("🧠 <b>Gemini 3:</b>\n\nEnter your prompt:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_deepseek":
        context.user_data[AWAIT_DEEPSEEK] = True
        await query.edit_message_text("🔥 <b>DeepSeek AI:</b>\n\nEnter your prompt:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_flirt":
        context.user_data[AWAIT_FLIRT] = True
        await query.edit_message_text("💖 <b>Flirt AI:</b>\n\nEnter text to flirt with:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_code":
        context.user_data[AWAIT_CODE] = True
        await query.edit_message_text("💻 <b>Code Generator:</b>\n\nDescribe the code you need:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_insta":
        context.user_data[AWAIT_INSTA] = True
        await query.edit_message_text("📸 <b>Instagram Info:</b>\n\nEnter Username or Profile URL:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_userinfo":
        context.user_data[AWAIT_USERINFO] = True
        await query.edit_message_text("👤 <b>User Info:</b>\n\nForward a message or enter User ID/Username:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_ff":
        context.user_data[AWAIT_FF] = True
        await query.edit_message_text("🎮 <b>Free Fire Stats:</b>\n\nEnter Player UID:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_ffguild":
        context.user_data[AWAIT_FFGUILD] = True
        await query.edit_message_text("🏰 <b>Guild Info:</b>\n\nEnter Guild ID:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_dl":
        context.user_data[AWAIT_DL] = True
        await query.edit_message_text("📥 <b>Downloader:</b>\n\nEnter any media URL (TikTok, IG, YT, etc.):", reply_markup=back, parse_mode="HTML")
    elif data == "btn_qrgen":
        context.user_data[AWAIT_QRGEN] = True
        await query.edit_message_text("🖼 <b>QR Generator:</b>\n\nEnter text or URL:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_translate":
        context.user_data[AWAIT_TRANSLATE] = True
        await query.edit_message_text("🌐 <b>AI Translator:</b>\n\nEnter text to translate:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_summarize":
        context.user_data[AWAIT_SUMMARIZE] = True
        await query.edit_message_text("📝 <b>AI Summarizer:</b>\n\nEnter text to summarize:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_grammar":
        context.user_data[AWAIT_GRAMMAR] = True
        await query.edit_message_text("✍️ <b>AI Grammar Check:</b>\n\nEnter text to correct:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_bgrem":
        context.user_data[AWAIT_BGREM] = True
        await query.edit_message_text("🧼 <b>Background Remover:</b>\n\nSend the photo to process:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_fflike":
        context.user_data[AWAIT_FFLIKE] = True
        await query.edit_message_text("🚀 <b>FF Like Booster:</b>\n\nEnter Player UID:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_shorten":
        # context.user_data[AWAIT_SHORTEN] = True # Not using await, direct cmd_shorten usually
        # But if button, maybe guide?
        await query.edit_message_text("🔗 <b>URL Shortener:</b>\n\nUsage: <code>/shorten [url]</code>", reply_markup=back, parse_mode="HTML")
    elif data == "btn_tod":
        await cmd_truthordare(update, context)
        
    elif data == "btn_rps": await cmd_game_rps(update, context)
    elif data == "btn_coin": await cmd_game_coin(update, context)
    elif data == "btn_slot": await cmd_game_slot(update, context)
    elif data == "btn_dice": await cmd_game_dice(update, context)
    elif data == "btn_ttt": await cmd_game_ttt(update, context)
    
    elif data == "btn_commands":
        await cmd_commands(update, context)
    elif data == "btn_help":
        await cmd_help(update, context)
    elif data == "btn_riddle":
        await cmd_game_riddle(update, context)
    elif data == "btn_guess":
        await cmd_game_guess(update, context)
        
    elif data == "btn_admin" or data == "menu_owner": # Owner panel
        if not is_owner(query.from_user.id): return
        await query.edit_message_reply_markup(reply_markup=get_main_menu("owner", query.from_user.id))

    elif data == "adm_toggle_access":
        CONFIG["global_access"] = not CONFIG.get("global_access", True)
        save_config(CONFIG)
        # Refresh owner menu
        await query.edit_message_reply_markup(reply_markup=get_main_menu("owner", query.from_user.id))
        
    elif data == "adm_delete_blast":
        await cmd_del_broadcast(update, context)
    elif data == "adm_ban_user":
        context.user_data[AWAIT_BAN] = True
        await query.edit_message_text("🚫 <b>Ban User:</b>\n\nEnter User ID:", reply_markup=back, parse_mode="HTML")
    elif data == "adm_unban_user":
        context.user_data[AWAIT_UNBAN] = True
        await query.edit_message_text("✅ <b>Unban User:</b>\n\nEnter User ID:", reply_markup=back, parse_mode="HTML")
    elif data == "adm_gmanage":
        text = (
            "🛡️ <b>Remote Group Management</b>\n\n"
            "Use these commands:\n"
            "/ban [gid] [uid]\n/unban [gid] [uid]\n/mute [gid] [uid]\n/kick [gid] [uid]"
        )
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=back)
    elif data == "adm_ball":
        await query.edit_message_text("📢 Global Broadcast: <code>/broadcastall [msg]</code>", parse_mode="HTML", reply_markup=back)
    elif data == "adm_media":
        await query.edit_message_text("🖼️ Media Broadcast: Reply with <code>/broadcast_media</code>", parse_mode="HTML", reply_markup=back)
    elif data == "adm_user":
        await query.edit_message_text("👤 User DM: <code>/broadcastuser [id] [msg]</code>", parse_mode="HTML", reply_markup=back)
    elif data == "adm_group":
        await query.edit_message_text("👥 Group DM: <code>/broadcast [id] [msg]</code>", parse_mode="HTML", reply_markup=back)
    elif data == "adm_stats":
        await cmd_stats(update, context)

    elif data == "btn_hinata":
        context.user_data[AWAIT_HINATA] = True
        await query.edit_message_text("🌸 <b>Hinata AI:</b>\n\n<i>Talk to me...</i>", reply_markup=back, parse_mode="HTML")
    elif data == "btn_imagine":
        context.user_data[AWAIT_IMAGINE] = True
        await query.edit_message_text("🎨 <b>pollinations.ai Image Gen:</b>\n\nEnter your prompt:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_ffvisit":
        context.user_data[AWAIT_FFVISIT] = True
        await query.edit_message_text("👀 <b>FF Account Visit:</b>\n\nEnter User UID:", reply_markup=back, parse_mode="HTML")
    elif data == "btn_tempmail":
        await cmd_tempmail(update, context)
    elif data == "tm_refresh":
        await temp_mail_refresh(update, context, manual=True)
    elif data == "tm_close":
        context.user_data.pop('temp_mail', None)
        await query.edit_message_text("❌ <b>Session Closed.</b>", parse_mode="HTML")
    elif data == "btn_back":
        # Check if we are in a sub-menu context or just base
        # Default back goes to Home
        await query.edit_message_text("✨ <b>Welcome Back!</b>\n\nChoose an option:", reply_markup=get_main_menu("home", query.from_user.id), parse_mode="HTML")
    elif data.startswith("dl_fmt|"):
        _, fmt_id, ext = data.split("|")
        await process_download(update, context, fmt_id, ext)
    elif data.startswith("tod_"):
        mode = data.split("_")[1] # truth or dare
        await do_tod_fetch(update, context, mode)

async def do_tod_fetch(update: Update, _context: ContextTypes.DEFAULT_TYPE, mode: str):
    query = update.callback_query
    
    # Parse mode (e.g. tod_truth_funny -> category "truth funny")
    parts = mode.split("_") # ['truth', 'funny']
    category = " ".join(parts)
    
    await query.edit_message_text(f"🎲 <b>Rolling for {category.title()}...</b>", parse_mode="HTML")
    
    prompt = f"Generate a {category} question/task for a Truth or Dare game. Make it engaging. Return only the question text."
    async with httpx.AsyncClient() as client:
        reply = await fetch_chatgpt(client, prompt)
    
    kb = [
        [InlineKeyboardButton("🔄 Roll Again", callback_data=f"tod_{mode}"),
         InlineKeyboardButton("🔙 Back", callback_data="btn_back")]
    ]
    await query.edit_message_text(f"🎲 <b>{category.title()}:</b>\n\n{html.escape(reply)}", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.from_user: return
    ud = context.user_data
    txt = msg.text or ""

    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Menu", callback_data="btn_back")]])

    if await check_permission(update, context, silent=True):
        if ud.pop(AWAIT_GEMINI, False):
            m = await msg.reply_text("🧠 <b>Analyzing...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_gemini3(c, txt)
            await m.edit_text(f"💎 <b>Gemini:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return

        if ud.pop(AWAIT_IMAGINE, False):
            context.args = txt.split()
            await cmd_imagine(update, context)
            return

        if ud.pop(AWAIT_DEEPSEEK, False):
            m = await msg.reply_text("🚀 <b>Searching...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_deepseek(c, txt)
            await m.edit_text(f"🔥 <b>DeepSeek:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_FLIRT, False):
            m = await msg.reply_text("💖 <b>Thinking...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_flirt(c, txt)
            await m.edit_text(f"✨ <b>Flirt AI:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_HINATA, False):
            m = await msg.reply_text("🌸 <b>Hinata is typing...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_hinata(c, txt)
            await m.edit_text(f"🌸 <b>Hinata:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_CODE, False):
            m = await msg.reply_text("👨‍💻 <b>Coding...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_code(c, txt)
            await m.edit_text(f"💻 <b>Code AI:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_INSTA, False): await do_insta_fetch_by_text(update, context, txt.strip()); return
        elif ud.pop(AWAIT_USERINFO, False): await do_user_info_fetch(update, context, txt.strip()); return
        elif ud.pop(AWAIT_FF, False): await do_ff_fetch_by_text(update, context, txt.strip()); return
        elif ud.pop(AWAIT_FFGUILD, False): await do_ff_guild_fetch(update, context, txt.strip()); return
        elif ud.pop(AWAIT_FFVISIT, False): await do_ff_visit(update, context, txt.strip()); return
        elif ud.pop(AWAIT_DL, False): await download_media(update, context, txt.strip()); return
        elif ud.pop(AWAIT_QRGEN, False): await cmd_qrgen(update, context); return
        elif ud.pop(AWAIT_TRANSLATE, False): await cmd_translate(update, context); return
        elif ud.pop(AWAIT_SUMMARIZE, False): await cmd_summarize(update, context); return
        elif ud.pop(AWAIT_GRAMMAR, False):
            m = await msg.reply_text("✍️ <b>Analyzing Grammar...</b>", parse_mode="HTML")
            async with httpx.AsyncClient() as c: r = await fetch_grammar(c, txt)
            await m.edit_text(f"✍️ <b>Corrected Text:</b>\n\n{html.escape(r)}", parse_mode="HTML", reply_markup=back_btn)
            return
        elif ud.pop(AWAIT_GUESS, False):
            try:
                guess = int(txt.strip())
                secret = ud.get("guess_num")
                attempts = ud.get("guess_attempts", 0) + 1
                ud["guess_attempts"] = attempts
                
                if guess == secret:
                    await msg.reply_text(f"🎉 <b>Correct!</b> The number was <code>{secret}</code>. It took you {attempts} tries!", parse_mode="HTML", reply_markup=back_btn)
                    ud.pop("guess_num", None)
                    ud.pop("guess_attempts", None)
                elif guess < secret:
                    ud[AWAIT_GUESS] = True
                    await msg.reply_text("📈 <b>Higher!</b> Try again:", parse_mode="HTML")
                else:
                    ud[AWAIT_GUESS] = True
                    await msg.reply_text("📉 <b>Lower!</b> Try again:", parse_mode="HTML")
            except:
                ud[AWAIT_GUESS] = True
                await msg.reply_text("❌ Please enter a valid number.")
            return
        elif ud.pop(AWAIT_RIDDLE, False):
            answer = ud.get("riddle_answer", "").lower()
            if txt.strip().lower() in answer or balance_check(txt.strip().lower(), answer):
                await msg.reply_text(f"✅ <b>Perfect!</b> You got it right.\n\nAnswer: <code>{ud.get('riddle_answer')}</code>", parse_mode="HTML", reply_markup=back_btn)
            else:
                await msg.reply_text(f"❌ <b>Wrong!</b>\n\nThe correct answer was: <code>{ud.get('riddle_answer')}</code>", parse_mode="HTML", reply_markup=back_btn)
            ud.pop("riddle_answer", None)
            return
        elif ud.pop(AWAIT_BGREM, False):
            if msg.photo: await do_bg_remove(update, context)
            else: await msg.reply_text("❌ <b>Please send a photo</b> to remove its background.", parse_mode="HTML")
            return
        elif ud.pop(AWAIT_FFLIKE, False): await do_ff_like_fetch(update, context, txt.strip()); return
        elif ud.pop(AWAIT_BAN, False):
            try:
                bid = int(txt.strip())
                if bid == OWNER_ID:
                    await msg.reply_text("❌ <b>Error:</b> You cannot ban the owner!")
                    return
                if "banned_users" not in CONFIG: CONFIG["banned_users"] = []
                if bid not in CONFIG["banned_users"]:
                    CONFIG["banned_users"].append(bid)
                    save_config(CONFIG)
                    await msg.reply_text(f"🚫 <b>User Banned:</b> <code>{bid}</code>", parse_mode="HTML")
                else:
                    await msg.reply_text("ℹ️ <b>Info:</b> User is already banned.")
            except:
                await msg.reply_text("❌ <b>Error:</b> Invalid User ID. Please send numbers only.")
            return
        elif ud.pop(AWAIT_UNBAN, False):
            try:
                bid = int(txt.strip())
                if "banned_users" in CONFIG and bid in CONFIG["banned_users"]:
                    CONFIG["banned_users"].remove(bid)
                    save_config(CONFIG)
                    await msg.reply_text(f"✅ <b>User Unbanned:</b> <code>{bid}</code>", parse_mode="HTML")
                else:
                    await msg.reply_text("ℹ️ <b>Info:</b> User is not in the ban list.")
            except:
                await msg.reply_text("❌ <b>Error:</b> Invalid User ID. Please send numbers only.")
            return
    
    if msg.chat.type == "private": 
        await forward_or_copy(update, context)

    # Keywords & Forwards
    txt_to_check = (msg.text or msg.caption or "").strip()
    if txt_to_check:
        low = txt_to_check.lower()
        for k in KEYWORDS:
            if k.lower() in low:
                user = msg.from_user
                chat_title = msg.chat.title or "Private Chat"
                from_info = f"{html.escape(user.full_name)} (@{user.username})" if user.username else html.escape(user.full_name)
                alert_text = (
                    f"🚨 <b>Keyword Mention Detected!</b>\n\n"
                    f"<b>Keyword:</b> <code>{k}</code>\n"
                    f"<b>From:</b> {from_info}\n"
                    f"<b>Group:</b> {html.escape(chat_title)}\n"
                    f"<b>Message:</b> {html.escape(txt_to_check[:1024])}"
                )
                try:
                    await context.bot.send_message(OWNER_ID, alert_text, parse_mode="HTML")
                except: pass
                break
    
    # Perfect Tracking Logic
    async def safe_track(target_id):
        try:
            await msg.forward(target_id)
        except Exception:
            try:
                await msg.copy(target_id)
            except: pass

    if msg.from_user.id == TRACKED_USER1_ID: await safe_track(FORWARD_USER1_GROUP_ID)
    if msg.from_user.id == TRACKED_USER2_ID: await safe_track(FORWARD_USER2_GROUP_ID)
    if msg.chat.id == SOURCE_GROUP_ID: await safe_track(DESTINATION_GROUP_ID)

async def track_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.my_chat_member.chat
    if chat.type in ["group", "supergroup"]:
        gs = read_json("groups.json", [])
        if gs and not isinstance(gs[0], dict):
            gs = [{"id": gid, "title": "Unknown"} for gid in gs]
            
        if not any(g['id'] == chat.id for g in gs):
            new_group = {
                "id": chat.id,
                "title": chat.title,
                "type": chat.type,
                "added_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            gs.append(new_group)
            write_json("groups.json", gs)


async def broadcast_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: return
    try:
        sent = await context.bot.send_message(chat_id=int(context.args[0]), text=" ".join(context.args[1:]))
        save_broadcast_msg(sent.chat_id, sent.message_id)
        await update.message.reply_text("✅ Sent")
        update_stats(sent_users=1)
    except:
        await update.message.reply_text("❌ Failed")
        update_stats(failed_users=1)

async def group_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: 
        await update.message.reply_text("💡 Usage: /ban [group_id] [user_id]")
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        await update.message.reply_text(f"✅ User <code>{user_id}</code> banned from <code>{chat_id}</code>.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {html.escape(str(e))}", parse_mode="HTML")

async def group_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: 
        await update.message.reply_text("💡 Usage: /unban [group_id] [user_id]")
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        await context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id, only_if_banned=True)
        await update.message.reply_text(f"✅ User <code>{user_id}</code> unbanned from <code>{chat_id}</code>.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {html.escape(str(e))}", parse_mode="HTML")

async def group_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: 
        await update.message.reply_text("💡 Usage: /mute [group_id] [user_id]")
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        await context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=ChatPermissions(can_send_messages=False))
        await update.message.reply_text(f"🔇 User <code>{user_id}</code> muted in <code>{chat_id}</code>.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {html.escape(str(e))}", parse_mode="HTML")

async def group_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: 
        await update.message.reply_text("💡 Usage: /unmute [group_id] [user_id]")
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        await context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_polls=True, can_send_other_messages=True, can_add_web_page_previews=True, can_change_info=True, can_invite_users=True, can_pin_messages=True))
        await update.message.reply_text(f"🔊 User <code>{user_id}</code> unmuted in <code>{chat_id}</code>.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {html.escape(str(e))}", parse_mode="HTML")

async def group_kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: 
        await update.message.reply_text("💡 Usage: /kick [group_id] [user_id]")
        return
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
        await context.bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
        await update.message.reply_text(f"👞 User <code>{user_id}</code> kicked from <code>{chat_id}</code>.", parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {html.escape(str(e))}", parse_mode="HTML")

async def cmd_addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a user as admin in a specific chat. Usage: /addadmin [chat_id] [user_id]"""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("🔒 <b>Owner Only Command</b>", parse_mode="HTML")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "💡 <b>Usage:</b> <code>/addadmin [chat_id] [user_id]</code>\n\n"
            "<i>Example: /addadmin -1001234567890 7333244376</i>",
            parse_mode="HTML"
        )
        return
    
    try:
        chat_id = int(context.args[0])
        user_id = int(context.args[1])
        
        # Promote user to admin with full permissions
        await context.bot.promote_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            can_manage_chat=True,
            can_delete_messages=True,
            can_manage_video_chats=True,
            can_restrict_members=True,
            can_promote_members=True,
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True
        )
        
        await update.message.reply_text(
            f"✅ <b>Admin Promotion Successful!</b>\n\n"
            f"👤 <b>User ID:</b> <code>{user_id}</code>\n"
            f"💬 <b>Chat ID:</b> <code>{chat_id}</code>\n\n"
            f"<i>User has been granted full admin privileges.</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>Failed to add admin:</b>\n<code>{html.escape(str(e))}</code>",
            parse_mode="HTML"
        )

async def broadcastall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or not context.args: return
    gs = read_json("groups.json", []); s = f = 0
    t = " ".join(context.args)
    for g in gs:
        gid = g.get('id') if isinstance(g, dict) else g
        try:
            sent = await context.bot.send_message(chat_id=gid, text=t)
            save_broadcast_msg(sent.chat_id, sent.message_id)
            s += 1
        except:
            f += 1
    await update.message.reply_text(f"✅ {s} | ❌ {f}")
    update_stats(sent_groups=s, failed_groups=f)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2: return
    try:
        sent = await context.bot.send_message(chat_id=int(context.args[0]), text=" ".join(context.args[1:]))
        save_broadcast_msg(sent.chat_id, sent.message_id)
        STATS["broadcasts"] += 1
        await update.message.reply_text("✅ Sent to group")
        update_stats(sent_groups=1)
    except:
        await update.message.reply_text("❌ Failed")
        update_stats(failed_groups=1)


async def broadcast_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    msg = update.message
    photo = None
    if msg.reply_to_message and (msg.reply_to_message.photo or msg.reply_to_message.document):
        photo = msg.reply_to_message.photo[-1].file_id if msg.reply_to_message.photo else msg.reply_to_message.document.file_id
        cap = " ".join(context.args) if context.args else (msg.reply_to_message.caption or "")
    elif msg.photo:
        photo = msg.photo[-1].file_id
        cap = msg.caption or ""
    else:
        await msg.reply_text("💡 Usage: Send/Reply to photo with /broadcast_media")
        return
    gs = read_json("groups.json", []); s = f = 0
    for g in gs:
        gid = g.get('id') if isinstance(g, dict) else g
        try:
            sent = await context.bot.send_photo(chat_id=gid, photo=photo, caption=cap, parse_mode="HTML")
            save_broadcast_msg(sent.chat_id, sent.message_id)
            s += 1
        except:
            f += 1
    await msg.reply_text(f"🖼️ Media Blast: ✅ {s} | ❌ {f}")
    update_stats(sent_groups=s, failed_groups=f)

async def cmd_del_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    history = read_json("broadcast_history.json", [])
    if not history:
        await update.message.reply_text("ℹ️ No recent broadcast history found.")
        return
    
    status_msg = await update.message.reply_text(f"🗑️ <b>Cleaning up {len(history)} messages...</b>", parse_mode="HTML")
    s = f = 0
    for entry in history:
        try:
            await context.bot.delete_message(chat_id=entry['chat_id'], message_id=entry['message_id'])
            s += 1
        except Exception:
            f += 1
            
    # Clear history after attempt
    write_json("broadcast_history.json", [])
    await status_msg.edit_text(f"✅ <b>Cleanup Complete</b>\n\n🗑️ Deleted: {s}\n⚠️ Failed: {f}", parse_mode="HTML")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and handle common Telegram API issues."""
    err = context.error
    if isinstance(err, Forbidden):
        return # Bot blocked
    if isinstance(err, BadRequest):
        err_msg = str(err)
        if "Message to be replied not found" in err_msg or "Message to edit not found" in err_msg or "Message is not modified" in err_msg:
            return
    
    logger.error(f"Update {update} caused error {err}")
    # Optional: notify owner for critical errors
    if not isinstance(err, (BadRequest, Forbidden)):
        try:
            await context.bot.send_message(chat_id=OWNER_ID, text=f"⚠️ <b>Bot Error:</b>\n<code>{html.escape(str(err))[:500]}</code>", parse_mode="HTML")
        except: pass

# ================= Background Cleanup =================
async def auto_cleanup_task():
    """Wipes the downloads folder every 10 minutes and clears log file if too large."""
    while True:
        try:
            # Clear downloads folder
            if os.path.exists("downloads"):
                files_removed = 0
                for f in os.listdir("downloads"):
                    path = os.path.join("downloads", f)
                    try:
                        if os.path.isfile(path): 
                            os.remove(path)
                            files_removed += 1
                        elif os.path.isdir(path): 
                            shutil.rmtree(path)
                            files_removed += 1
                    except: pass
                if files_removed > 0:
                    logger.info(f"Auto-cleanup: {files_removed} items removed from downloads folder.")
            
            # Clear log file if it exceeds MAX_LOG_SIZE
            if os.path.exists(LOG_FILE):
                log_size = os.path.getsize(LOG_FILE)
                if log_size > MAX_LOG_SIZE:
                    # Keep only the last 50KB of logs
                    try:
                        with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                            f.seek(max(0, log_size - 50 * 1024))
                            f.readline()  # Skip partial line
                            remaining_logs = f.read()
                        
                        with open(LOG_FILE, 'w', encoding='utf-8') as f:
                            f.write(f"[LOG TRUNCATED - Previous logs cleared at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n\n")
                            f.write(remaining_logs)
                        
                        logger.info(f"Auto-cleanup: Log file truncated from {log_size/1024:.1f}KB to ~50KB.")
                    except Exception as log_err:
                        logger.error(f"Failed to truncate log: {log_err}")
                        
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        await asyncio.sleep(600) # 10 minutes

# ================= Run =================
# Global application object for access from main.py
app = None

async def start_bot():
    global app
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing!")
        return
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_error_handler(error_handler)
    
    async def handle_dl_cmd(u, c):
        if not await check_permission(u, c): return
        clear_states(c.user_data)
        if c.args: await download_media(u, c, c.args[0])
        else: await u.message.reply_text("💡 Usage: /dl <url>")
    
    async def handle_insta_cmd(u, c):
        if not await check_permission(u, c): return
        clear_states(c.user_data)
        if c.args: await do_insta_fetch_by_text(u, c, c.args[0])
        else: await u.message.reply_text("💡 Usage: /insta <username>")

    async def handle_ff_cmd(u, c):
        if not await check_permission(u, c): return
        clear_states(c.user_data)
        if c.args: await do_ff_fetch_by_text(u, c, c.args[0])
        else: await u.message.reply_text("💡 Usage: /ff <uid>")

    async def handle_userinfo_cmd(u, c):
        if not await check_permission(u, c): return
        clear_states(c.user_data)
        query = c.args[0] if c.args else None
        await do_user_info_fetch(u, c, query)

    app.add_handler(CommandHandler("insta", handle_insta_cmd))
    app.add_handler(CommandHandler("userinfo", handle_userinfo_cmd))
    app.add_handler(CommandHandler("id", handle_userinfo_cmd))
    app.add_handler(CommandHandler("ff", handle_ff_cmd))
    app.add_handler(CommandHandler("dl", handle_dl_cmd))
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("commands", cmd_commands))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("gemini", cmd_gemini))
    app.add_handler(CommandHandler("deepseek", cmd_deepseek))
    app.add_handler(CommandHandler("flirt", cmd_flirt))
    app.add_handler(CommandHandler("code", cmd_code))
    app.add_handler(CommandHandler("hinata", cmd_hinata))
    app.add_handler(CommandHandler("tempmail", cmd_tempmail))
    app.add_handler(CommandHandler("visit", cmd_ff_visit))
    app.add_handler(CommandHandler("ai", cmd_ai_combined))
    app.add_handler(CommandHandler("qrgen", cmd_qrgen))
    app.add_handler(CommandHandler("qrread", cmd_qrread))
    app.add_handler(CommandHandler("bgrem", cmd_bgrem))
    app.add_handler(CommandHandler("translate", cmd_translate))
    app.add_handler(CommandHandler("summarize", cmd_summarize))
    app.add_handler(CommandHandler("grammar", cmd_grammar))
    app.add_handler(CommandHandler("fflike", cmd_fflike))
    app.add_handler(CommandHandler("tod", cmd_truthordare))
    app.add_handler(CommandHandler("rps", cmd_game_rps))
    app.add_handler(CommandHandler("coin", cmd_game_coin))
    app.add_handler(CommandHandler("slot", cmd_game_slot))
    app.add_handler(CommandHandler("dice", cmd_game_dice))
    app.add_handler(CommandHandler("ttt", cmd_game_ttt))
    app.add_handler(CommandHandler("shorten", cmd_shorten))
    app.add_handler(CommandHandler("imagine", cmd_imagine))
    async def handle_ffguild_cmd(u, c):
        if not await check_permission(u, c): return
        if c.args: await do_ff_guild_fetch(u, c, c.args[0])
        else: await u.message.reply_text("💡 Usage: /ffguild <id>")
    app.add_handler(CommandHandler("ffguild", handle_ffguild_cmd))
    app.add_handler(CommandHandler("gban", cmd_gban))
    app.add_handler(CommandHandler("ungban", cmd_ungban))
    app.add_handler(CommandHandler("toggle_access", cmd_toggle_access))
    app.add_handler(CommandHandler("broadcastall", broadcastall))
    app.add_handler(CommandHandler("broadcastuser", broadcast_user))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("broadcast_media", broadcast_media))
    app.add_handler(CommandHandler("delbroadcast", cmd_del_broadcast))
    app.add_handler(CommandHandler("ban", group_ban))
    app.add_handler(CommandHandler("unban", group_unban))
    app.add_handler(CommandHandler("mute", group_mute))
    app.add_handler(CommandHandler("unmute", group_unmute))
    app.add_handler(CommandHandler("kick", group_kick))
    app.add_handler(CommandHandler("addadmin", cmd_addadmin))

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    app.add_handler(ChatMemberHandler(track_group, ChatMemberHandler.MY_CHAT_MEMBER))
    
    logger.info("Hinata Initialized")
    
    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        STATS["status"] = "online"
        logger.info("Hinata Live and Polling")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        STATS["status"] = "offline"
        if "rejected by the server" in str(e).lower() or "unauthorized" in str(e).lower():
            logger.error("CRITICAL: Your Telegram Bot Token is INVALID. Please check @BotFather.")

    # Start cleanup task (runs regardless of bot connection)
    asyncio.create_task(auto_cleanup_task())



async def stop_bot():
    global app
    if app:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        app = None
    STATS["status"] = "offline"

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot())
    loop.run_forever()

