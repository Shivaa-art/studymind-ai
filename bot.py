import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from google import genai
import requests
from bs4 import BeautifulSoup

from config import TOKEN, GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)
assignments = {}
user_chat_ids = {}

logging.basicConfig(level=logging.INFO)

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
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /done <number>\nExample: /done 1")
        return
    index = int(args[0]) - 1
    if user_id not in assignments or index >= len(assignments[user_id]):
        await update.message.reply_text("Assignment not found!")
        return
    assignments[user_id][index]["done"] = True
    subject = assignments[user_id][index]["subject"]
    await update.message.reply_text(f"🎉 Great job! '{subject}' marked as done!")

async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /summarize <topic>")
        return
    topic = " ".join(args)
    await update.message.reply_text(f"🤖 Generating AI summary for '{topic}'... please wait!")
    prompt = f"""
    You are a helpful study assistant for Indian college students (BBA/MBA level).
    Create a concise study summary for: {topic}
    Format:
    📚 {topic} — Study Summary
    🔑 Key Concepts:
    • [concept 1]
    • [concept 2]
    • [concept 3]
    • [concept 4]
    • [concept 5]
    📝 Important Topics to Study:
    • [topic 1]
    • [topic 2]
    • [topic 3]
    🎯 Exam Tips:
    • [tip 1]
    • [tip 2]
    • [tip 3]
    ⚡ Quick Revision (3 lines max):
    [short paragraph]
    """
    await update.message.reply_text(ai_generate(prompt))

async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("🤖 Creating your personalized study plan...")
    user_assignments = assignments.get(user_id, [])
    pending = [a for a in user_assignments if not a["done"]]
    if pending:
        assignment_list = "\n".join([f"- {a['subject']} ({a['type']}) due {a['deadline_str']}" for a in pending])
    else:
        assignment_list = "No pending assignments"
    prompt = f"""
    You are a study planner for an Indian BBA college student.
    Pending assignments/exams: {assignment_list}
    Create a motivating daily study plan for today. Keep it short and practical.
    Format:
    📅 Your Study Plan for Today
    ⏰ Morning (9am - 12pm):
    • [task]
    ☀️ Afternoon (2pm - 5pm):
    • [task]
    🌙 Evening (7pm - 9pm):
    • [task]
    💪 Motivation: [one motivating sentence]
    """
    await update.message.reply_text(ai_generate(prompt))

async def internships(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Searching for latest internships... please wait!")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        url = "https://internshala.com/internships/business-administration-internship"
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        internships_list = soup.find_all("div", class_="individual_internship", limit=5)
        if not internships_list:
            await update.message.reply_text("⚠️ Could not fetch internships right now.\nVisit: https://internshala.com/internships/business-administration-internship")
            return
        msg = "💼 Latest BBA Internships on Internshala:\n\n"
        for i, intern in enumerate(internships_list, 1):
            title = intern.find("h3", class_="job-internship-name") or intern.find("div", class_="profile") or intern.find("h3")
            company = intern.find("h4", class_="company-name") or intern.find("p", class_="company-name") or intern.find("a", class_="link_display_like_text")
            location = intern.find("a", class_="location_link") or intern.find("div", class_="location_names") or intern.find("span", class_="location")
            stipend = intern.find("span", class_="stipend") or intern.find("div", class_="stipend") or intern.find("span", class_="amount")
            title_text = title.text.strip() if title else "BBA Internship"
            company_text = company.text.strip() if company else "See Internshala"
            location_text = location.text.strip() if location else "Work from Home"
            stipend_text = stipend.text.strip() if stipend else "Unpaid"
            msg += f"🏢 {i}. {title_text}\n   Company: {company_text}\n   📍 {location_text}\n   💰 {stipend_text}\n\n"
        msg += "🔗 Apply: https://internshala.com/internships/business-administration-internship"
        await update.message.reply_text(msg)
    except Exception:
        await update.message.reply_text("⚠️ Could not fetch internships right now.\nVisit: https://internshala.com/internships/business-administration-internship")

async def hackathons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏆 Top Platforms for Hackathons:\n\n"
        "1️⃣ Smart India Hackathon\n   🔗 sih.gov.in\n\n"
        "2️⃣ Unstop Hackathons\n   🔗 unstop.com/hackathons\n\n"
        "3️⃣ Devfolio\n   🔗 devfolio.co/hackathons\n\n"
        "4️⃣ HackerEarth\n   🔗 hackerearth.com/challenges\n\n"
        "5️⃣ Internshala Competitions\n   🔗 internshala.com/competitions\n\n"
        "💡 Tip: Register on Unstop — it sends automatic alerts for new hackathons!"
    )

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /quiz <topic>\nExample: /quiz Marketing Management")
        return
    topic = " ".join(args)
    await update.message.reply_text(f"🧠 Generating quiz for '{topic}'... please wait!")
    prompt = f"""
    You are an exam coach for Indian BBA college students.
    Generate 5 multiple choice questions for: {topic}
    Format exactly like this:
    🧠 Quiz: {topic}
    Q1. [question]
    A) [option]  B) [option]  C) [option]  D) [option]
    ✅ Answer: [correct option letter and text]
    (repeat for Q2 to Q5)
    💡 Tip: [one study tip for this topic]
    """
    await update.message.reply_text(ai_generate(prompt))

async def motivate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    user_assignments = assignments.get(user_id, [])
    pending = len([a for a in user_assignments if not a["done"]])
    completed = len([a for a in user_assignments if a["done"]])
    prompt = f"""
    You are an encouraging mentor for an Indian BBA student named {user_name}.
    Situation: {pending} pending tasks, {completed} completed tasks.
    Write a short powerful motivational message under 100 words.
    Reference Indian student life and dreams.
    End with one quote from a successful Indian personality.
    Format:
    💪 Hey {user_name}!
    [motivational message]
    🌟 Quote: "[quote]" — [person]
    """
    await update.message.reply_text(ai_generate(prompt))

async def tips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /tips <subject>\nExample: /tips Financial Management")
        return
    subject = " ".join(args)
    await update.message.reply_text(f"📖 Getting exam tips for '{subject}'... please wait!")
    prompt = f"""
    You are an exam strategy coach for Indian BBA students.
    Give powerful exam tips for: {subject}
    Format:
    📖 Exam Strategy: {subject}
    ⏰ Time Management:
    • [tip]  • [tip]
    📝 What to Focus On:
    • [topic 1]  • [topic 2]  • [topic 3]
    ❌ Common Mistakes to Avoid:
    • [mistake 1]  • [mistake 2]
    🎯 Last Day Strategy:
    • [24h before]  • [1h before]
    ✅ Guaranteed Marks Topics:
    • [topic 1]  • [topic 2]  • [topic 3]
    """
    await update.message.reply_text(ai_generate(prompt))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def check_reminders(app):
    now = datetime.now()
    for user_id, user_assignments in assignments.items():
        for a in user_assignments:
            if a["done"]:
                continue
            time_left = a["deadline"] - now
            if timedelta(hours=23) <= time_left <= timedelta(hours=25):
                chat_id = user_chat_ids.get(user_id)
                if chat_id:
                    emoji = "📝" if a["type"] == "exam" else "📚"
                    await app.bot.send_message(
                        chat_id=chat_id,
                        text=f"⏰ REMINDER!\n\n{emoji} {a['subject']} is due TOMORROW!\n📅 Deadline: {a['deadline_str']}\n\nDon't forget to prepare! 💪"
                    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_assignment))
    app.add_handler(CommandHandler("exam", add_exam))
    app.add_handler(CommandHandler("list", list_assignments))
    app.add_handler(CommandHandler("done", mark_done))
    app.add_handler(CommandHandler("summarize", summarize))
    app.add_handler(CommandHandler("plan", plan))
    app.add_handler(CommandHandler("countdown", countdown))
    app.add_handler(CommandHandler("internships", internships))
    app.add_handler(CommandHandler("hackathons", hackathons))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("motivate", motivate))
    app.add_handler(CommandHandler("tips", tips))
    app.add_handler(CommandHandler("help", help_command))
    job_queue = app.job_queue
    job_queue.run_repeating(
        lambda context: check_reminders(app),
        interval=3600,
        first=10
    )
    print("🤖 StudyMind AI is running with reminders enabled!")
    app.run_polling()

if __name__ == "__main__":
    main()