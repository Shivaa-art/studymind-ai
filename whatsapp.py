import requests

# Fill these from ultramsg.com dashboard
INSTANCE_ID = "instance177209"
TOKEN = "ue1g1m1yt1m3n5ns"
MY_PHONE = "+918341282018"  # Example: 919876543210 (91 + your 10 digit number)

def send_whatsapp(phone, message):
    url = f"https://api.ultramsg.com/{INSTANCE_ID}/messages/chat"
    payload = {
        "token": TOKEN,
        "to": phone,
        "body": message
    }
    response = requests.post(url, data=payload)
    return response.json()

def send_reminder(subject, deadline):
    message = (
        f"⏰ StudyMind AI Reminder!\n\n"
        f"📚 {subject} is due TOMORROW!\n"
        f"📅 Deadline: {deadline}\n\n"
        f"Don't forget to prepare! 💪\n\n"
        f"Powered by StudyMind AI 🤖"
    )
    return send_whatsapp(MY_PHONE, message)

def send_daily_plan(plan_text):
    message = (
        f"🌅 Good Morning from StudyMind AI!\n\n"
        f"{plan_text}\n\n"
        f"Have a productive day! 💪"
    )
    return send_whatsapp(MY_PHONE, message)

def send_internship_alert(internships_text):
    message = (
        f"💼 New Internship Alerts!\n\n"
        f"{internships_text}\n\n"
        f"Apply now before deadline! 🚀"
    )
    return send_whatsapp(MY_PHONE, message)

if __name__ == "__main__":
    print("Testing WhatsApp connection...")
    result = send_whatsapp(MY_PHONE,
        "👋 Hello from StudyMind AI!\n\n"
        "Your WhatsApp reminders are now active! ✅\n\n"
        "You will receive:\n"
        "📚 Assignment reminders\n"
        "📝 Exam alerts\n"
        "💼 Internship updates\n"
        "📅 Daily study plan every morning\n\n"
        "Powered by StudyMind AI 🤖"
    )
    print(result)
    if "true" in str(result):
        print("✅ WhatsApp message sent successfully!")
    else:
        print("❌ Failed — check your Instance ID and Token")