from flask import Flask, request
import requests
from google import genai

app = Flask(__name__)

INSTANCE_ID = "instance177209"
TOKEN = "ue1g1m1yt1m3n5ns"
GEMINI_API_KEY = "AIzaSyBpRSntDcBmj_IS3vcD25wxrIi_jVbB-I4"

client = genai.Client(api_key=GEMINI_API_KEY)

assignments = {}

def send_reply(phone, message):
    requests.post(
        f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat",
        data={"token": TOKEN, "to": phone, "body": message}
    )

def ai_generate(prompt):
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text
    except Exception as e:
        return "⏳ AI is busy, try again in a moment!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return "ok"

    message = data.get("body", "").strip()
    phone = data.get("from", "")
    msg_type = data.get("type", "")

    # Ignore non-text and outgoing messages
    if msg_type != "chat" or data.get("fromMe"):
        return "ok"

    # Remove @c.us from phone
    phone = phone.replace("@c.us", "")

    print(f"Message from {phone}: {message}")

    # Handle commands
    if message.lower() in ["/start", "hi", "hello", "start"]:
        reply = (
            "👋 Welcome to StudyMind AI on WhatsApp!\n\n"
            "Commands:\n"
            "add <subject> <DD-MM-YYYY> — Add assignment\n"
            "list — View all tasks\n"
            "summarize <topic> — AI study summary\n"
            "plan — AI daily plan\n"
            "quiz <topic> — Practice questions\n"
            "motivate — Get motivated!\n"
            "tips <subject> — Exam strategy\n"
            "internships — Latest internships\n"
            "hackathons — Find hackathons\n"
            "help — Show this menu"
        )
        send_reply(phone, reply)

    elif message.lower().startswith("add "):
        parts = message.split()
        if len(parts) >= 3:
            subject = parts[1]
            deadline = parts[2]
            if phone not in assignments:
                assignments[phone] = []
            assignments[phone].append({
                "subject": subject,
                "deadline": deadline,
                "done": False
            })
            send_reply(phone, f"✅ Added!\n📚 {subject}\n📅 Due: {deadline}")
        else:
            send_reply(phone, "Usage: add <subject> <DD-MM-YYYY>\nExample: add Marketing 25-05-2026")

    elif message.lower() == "list":
        user_tasks = assignments.get(phone, [])
        if not user_tasks:
            send_reply(phone, "No assignments yet! Type: add Marketing 25-05-2026")
        else:
            msg = "📋 Your Tasks:\n\n"
            for i, a in enumerate(user_tasks, 1):
                status = "✅" if a["done"] else "⏳"
                msg += f"{status} {i}. {a['subject']} — {a['deadline']}\n"
            send_reply(phone, msg)

    elif message.lower().startswith("summarize "):
        topic = message[10:].strip()
        send_reply(phone, f"🤖 Generating summary for '{topic}'... please wait!")
        prompt = f"""
        You are a study assistant for Indian BBA students.
        Create a concise study summary for: {topic}
        Format:
        📚 {topic} — Study Summary
        🔑 Key Concepts:
        • [concept 1]
        • [concept 2]
        • [concept 3]
        📝 Important Topics:
        • [topic 1]
        • [topic 2]
        🎯 Exam Tips:
        • [tip 1]
        • [tip 2]
        ⚡ Quick Revision: [2 lines]
        """
        send_reply(phone, ai_generate(prompt))

    elif message.lower() == "plan":
        send_reply(phone, "🤖 Creating your study plan...")
        user_tasks = assignments.get(phone, [])
        pending = [a for a in user_tasks if not a["done"]]
        task_list = "\n".join([f"- {a['subject']} due {a['deadline']}" for a in pending]) if pending else "No pending tasks"
        prompt = f"""
        You are a study planner for an Indian BBA student.
        Pending tasks: {task_list}
        Create a short motivating daily study plan.
        Format:
        📅 Your Study Plan for Today
        ⏰ Morning: [task]
        ☀️ Afternoon: [task]
        🌙 Evening: [task]
        💪 Motivation: [one sentence]
        """
        send_reply(phone, ai_generate(prompt))

    elif message.lower().startswith("quiz "):
        topic = message[5:].strip()
        send_reply(phone, f"🧠 Generating quiz for '{topic}'...")
        prompt = f"""
        Generate 5 MCQ questions for Indian BBA students on: {topic}
        Format:
        🧠 Quiz: {topic}
        Q1. [question]
        A) [option] B) [option] C) [option] D) [option]
        ✅ Answer: [answer]
        (repeat for Q2-Q5)
        💡 Tip: [study tip]
        """
        send_reply(phone, ai_generate(prompt))

    elif message.lower() == "motivate":
        prompt = f"""
        Write a short powerful motivational message for an Indian BBA student.
        Reference Indian student life and dreams.
        End with a quote from a successful Indian personality.
        Under 100 words.
        Format:
        💪 Hey Student!
        [message]
        🌟 Quote: "[quote]" — [person]
        """
        send_reply(phone, ai_generate(prompt))

    elif message.lower().startswith("tips "):
        subject = message[5:].strip()
        send_reply(phone, f"📖 Getting exam tips for '{subject}'...")
        prompt = f"""
        Give exam strategy tips for Indian BBA students for: {subject}
        Format:
        📖 Exam Strategy: {subject}
        ⏰ Time Management: [tips]
        📝 Focus On: [topics]
        ❌ Avoid: [mistakes]
        🎯 Last Day: [strategy]
        ✅ Easy Marks: [topics]
        """
        send_reply(phone, ai_generate(prompt))

    elif message.lower() == "internships":
        send_reply(phone,
            "💼 Find BBA Internships:\n\n"
            "1️⃣ Internshala\n"
            "   internshala.com/internships\n\n"
            "2️⃣ LinkedIn\n"
            "   linkedin.com/jobs\n\n"
            "3️⃣ Naukri\n"
            "   naukri.com/internship-jobs\n\n"
            "4️⃣ Indeed\n"
            "   indeed.co.in\n\n"
            "💡 Search: BBA intern Hyderabad"
        )

    elif message.lower() == "hackathons":
        send_reply(phone,
            "🏆 Find Hackathons:\n\n"
            "1️⃣ Smart India Hackathon\n   sih.gov.in\n\n"
            "2️⃣ Unstop\n   unstop.com/hackathons\n\n"
            "3️⃣ Devfolio\n   devfolio.co/hackathons\n\n"
            "4️⃣ HackerEarth\n   hackerearth.com/challenges\n\n"
            "💡 Register on Unstop for alerts!"
        )

    elif message.lower() in ["help", "/help"]:
        reply = (
            "📋 StudyMind AI Commands:\n\n"
            "add <subject> <date> — Add task\n"
            "list — View tasks\n"
            "summarize <topic> — AI summary\n"
            "plan — Daily study plan\n"
            "quiz <topic> — Practice quiz\n"
            "motivate — Motivation\n"
            "tips <subject> — Exam tips\n"
            "internships — Find internships\n"
            "hackathons — Find hackathons"
        )
        send_reply(phone, reply)

    else:
        send_reply(phone,
            "❓ Unknown command!\n\n"
            "Type *help* to see all commands 📋"
        )

    return "ok"

if __name__ == "__main__":
    print("🤖 StudyMind WhatsApp Bot starting...")
    app.run(port=5000, debug=False)