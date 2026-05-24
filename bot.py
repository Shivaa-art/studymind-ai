import logging
import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from google import genai
import requests
from bs4 import BeautifulSoup

# Works both locally and on Railway
TOKEN = os.environ.get("TOKEN", "8985167446:AAHhmQHv4GkVB5WTAerSUrPAg3QFv974Ljo")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBpRSntDcBmj_IS3vcD25wxrIi_jVbB-I4")
ULTRAMSG_INSTANCE = os.environ.get("INSTANCE_ID", "instance177209")
ULTRAMSG_TOKEN = os.environ.get("ULTRAMSG_TOKEN", "ue1g1m1yt1m3n5ns")
MY_PHONE = os.environ.get("MY_PHONE", "+918341282018")

client = genai.Client(api_key=GEMINI_API_KEY)
assignments = {}
user_chat_ids = {}

logging.basicConfig(level=logging.INFO)

def send_whatsapp(phone, message):
    try:
        url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE}/messages/chat"
        payload = {"token": ULTRAMSG_TOKEN, "to": phone, "body": message}
        response = requests.post(url, data=payload)
        return response.json()
    except Exception as e:
        print(f"WhatsApp error: {e}")
        return {}

def ai_generate(prompt):
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text
    except Exception as e:
        if "503" in str(e) or "UNAVAILABLE" in str(e):
            return "⏳ Gemini AI is busy right now. Please try again in 1-2 minutes!"
        return f"❌ AI error: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_chat_ids[update.effective_user.id] = update.effective_chat.id
    await update.message.reply_text(
        "👋 Welcome to StudyMind AI!\n\n"
        "Commands:\n"
        "/add <subject> <DD-MM-YYYY> — Add assignment\n"
        "/exam <subject> <DD-MM-YYYY> — Add exam\n"
        "/list — View all tasks\n"
        "/done <number> — Mark as completed\n"
        "/summarize <topic> — AI study summary\n"
        "/plan — AI study plan for today\n"
        "/countdown — Exam countdowns\n"
        "/internships — Latest BBA internships\n"
        "/hackathons — Find hackathons\n"
        "/quiz <topic> — Practice questions\n"
        "/motivate — Get motivated!\n"
        "/tips <subject> — Exam strategy\n"
        "/help — Show this menu\n\n"
        "⏰ You will get automatic reminders 24h before deadlines!"
    )

async def add_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chat_ids[user_id] = update.effective_chat.id
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /add <subject> <DD-MM-YYYY>\nExample: /add Marketing 15-05-2026")
        return
    subject = args[0]
    deadline_str = args[1]
    try:
        deadline = datetime.strptime(deadline_str, "%d-%m-%Y")
    except ValueError:
        await update.message.reply_text("❌ Wrong date format! Use DD-MM-YYYY\nExample: /add Marketing 15-05-2026")
        return
    if user_id not in assignments:
        assignments[user_id] = []
    assignments[user_id].append({
        "subject": subject,
        "deadline": deadline,
        "deadline_str": deadline_str,
        "type": "assignment",
        "done": False
    })
    days_left = (deadline - datetime.now()).days
    await update.message.reply_text(
        f"✅ Added!\n📚 Subject: {subject}\n📅 Deadline: {deadline_str}\n⏳ Days left: {days_left} days\n\n🔔 You'll get a reminder 24h before!"
    )

async def add_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chat_ids[user_id] = update.effective_chat.id
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /exam <subject> <DD-MM-YYYY>\nExample: /exam Operations 16-05-2026")
        return
    subject = args[0]
    date_str = args[1]
    try:
        exam_date = datetime.strptime(date_str, "%d-%m-%Y")
    except ValueError:
        await update.message.reply_text("❌ Use DD-MM-YYYY format!")
        return
    if user_id not in assignments:
        assignments[user_id] = []
    assignments[user_id].append({
        "subject": subject,
        "deadline": exam_date,
        "deadline_str": date_str,
        "type": "exam",
        "done": False
    })
    days_left = (exam_date - datetime.now()).days
    await update.message.reply_text(
        f"📝 Exam Added!\n📚 Subject: {subject}\n📅 Exam Date: {date_str}\n⏳ Days left: {days_left} days\n\n🔔 You'll get a reminder 24h before!"
    )

async def list_assignments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in assignments or len(assignments[user_id]) == 0:
        await update.message.reply_text("No assignments yet! Use /add to add one.")
        return
    msg = "📋 Your Tasks:\n\n"
    for i, a in enumerate(assignments[user_id], 1):
        status = "✅" if a["done"] else "⏳"
        emoji = "📝" if a["type"] == "exam" else "📚"
        days_left = (a["deadline"] - datetime.now()).days
        msg += f"{status} {i}. {emoji} {a['subject']} — {a['deadline_str']} ({days_left}d left)\n"
    await update.message.reply_text(msg)

async def countdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in assignments or len(assignments[user_id]) == 0:
        await update.message.reply_text("No exams added yet! Use /exam to add one.")
        return
    exams = [a for a in assignments[user_id] if a["type"] == "exam" and not a["done"]]
    if not exams:
        await update.message.reply_text("No upcoming exams! Use /exam to add one.")
        return
    msg = "⏳ Exam Countdown:\n\n"
    for e in sorted(exams, key=lambda x: x["deadline"]):
        days_left = (e["deadline"] - datetime.now()).days
        if days_left < 0:
            emoji = "❌"
            days_text = "Past due!"
        elif days_left == 0:
            emoji = "🔥"
            days_text = "TODAY!"
        elif days_left == 1:
            emoji = "⚠️"
            days_text = "TOMORROW!"
        elif days_left <= 3:
            emoji = "😰"
            days_text = f"{days_left} days left"
        else:
            emoji = "📅"
            days_text = f"{days_left} days left"
        msg += f"{emoji} {e['subject']} — {days_text}\n"
    await update.message.reply_text(msg)

async def mark_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if not args or not args[0].i