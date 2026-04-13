"""
Telegram Bot as Web Service (for Render free tier)
Uses webhooks instead of polling
"""

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import asyncio
import re
from gmail_sender import GmailSender
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize bot handler
gmail = GmailSender(
    email=settings.COMPANY_EMAIL,
    app_password=settings.GMAIL_APP_PASSWORD
)

pending_emails = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "👋 Welcome to The One'z and Zero Lead Bot!\n\n"
        "When you get a lead alert with an email draft:\n"
        "1. Reply with: SEND\n"
        "2. I'll ask for the prospect's email\n"
        "3. Provide the email\n"
        "4. I'll send it automatically!\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/help - Get help"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "📧 How to send emails:\n\n"
        "After receiving a lead alert:\n"
        "1. Reply: SEND\n"
        "2. I'll ask for email address\n"
        "3. Type the email: name@example.com\n"
        "4. Email sent! ✅\n\n"
        "Other commands:\n"
        "SKIP - Skip this lead\n"
        "STATUS - Check pending emails"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages"""
    global pending_emails
    
    user_id = update.effective_user.id
    message_text = update.message.text.strip()
    
    logger.info(f"Received message from {user_id}: {message_text}")
    
    # Check if waiting for email
    if user_id in pending_emails and pending_emails[user_id].get('waiting_for_email'):
        await process_email_address(update, context, message_text)
        return
    
    # Handle commands
    command = message_text.upper()
    
    if command == 'SEND':
        await handle_send(update, context)
    elif command == 'SKIP':
        await handle_skip(update, context)
    elif command == 'STATUS':
        await handle_status(update, context)
    else:
        await update.message.reply_text(
            "I didn't understand that. Try:\n"
            "• SEND - to send the last email draft\n"
            "• SKIP - to skip the current lead\n"
            "• /help - for more help"
        )


async def handle_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle SEND command"""
    global pending_emails
    
    user_id = update.effective_user.id
    pending_emails[user_id] = {'waiting_for_email': True}
    
    await update.message.reply_text(
        "📧 Great! Please provide the prospect's email address:\n\n"
        "Example: john@example.com"
    )


async def handle_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle SKIP command"""
    global pending_emails
    
    user_id = update.effective_user.id
    if user_id in pending_emails:
        del pending_emails[user_id]
    
    await update.message.reply_text(
        "✅ Lead skipped. I'll notify you about the next hot lead!"
    )


async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle STATUS command"""
    global pending_emails
    
    user_id = update.effective_user.id
    
    if user_id in pending_emails and pending_emails[user_id].get('waiting_for_email'):
        await update.message.reply_text(
            "⏳ Waiting for you to provide an email address.\n\n"
            "Type SKIP to cancel."
        )
    else:
        await update.message.reply_text(
            "✅ No pending actions.\n\n"
            "Waiting for the next lead alert!"
        )


async def process_email_address(update: Update, context: ContextTypes.DEFAULT_TYPE, email_text: str):
    """Process email address and send"""
    global pending_emails
    
    user_id = update.effective_user.id
    
    # Validate email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email_text):
        await update.message.reply_text(
            "❌ That doesn't look like a valid email address.\n\n"
            "Please provide a valid email:\n"
            "Example: john@example.com\n\n"
            "Or type SKIP to cancel."
        )
        return
    
    # Load draft from file
    import json
    import os
    draft_data = None
    
    try:
        if os.path.exists('/tmp/last_email_draft.json'):
            with open('/tmp/last_email_draft.json', 'r') as f:
                draft_data = json.load(f)
            logger.info("Draft loaded successfully")
    except Exception as e:
        logger.error(f"Could not load draft: {e}")
    
    if not draft_data:
        await update.message.reply_text(
            "❌ No email draft found.\n\n"
            "Please capture a lead first using the Chrome extension."
        )
        if user_id in pending_emails:
            del pending_emails[user_id]
        return
    
    # Send email
    await update.message.reply_text(f"📤 Sending email to {email_text}...")
    
    try:
        success = gmail.send_email(
            to_email=email_text,
            subject=draft_data.get('subject', 'Re: Automation Solutions'),
            body=draft_data.get('body', ''),
            to_name=draft_data.get('lead_name', 'there')
        )
        
        if success:
            await update.message.reply_text(
                f"✅ Email sent successfully to {email_text}!\n\n"
                f"To: {draft_data.get('lead_name')}\n"
                f"Subject: {draft_data.get('subject')}\n\n"
                "Lead contacted! 🎉"
            )
            
            # Delete draft
            try:
                os.remove('/tmp/last_email_draft.json')
            except:
                pass
        else:
            await update.message.reply_text(
                f"❌ Failed to send email to {email_text}\n\n"
                "Please check your Gmail settings."
            )
    
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)}")
    
    # Clear pending
    if user_id in pending_emails:
        del pending_emails[user_id]


# Initialize application
application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


@app.post("/webhook")
async def webhook(request: Request):
    """Handle Telegram webhook"""
    try:
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"ok": False, "error": str(e)}


@app.get("/")
async def root():
    """Health check"""
    return {"status": "Telegram bot is running", "service": "webhook mode"}


@app.get("/health")
async def health():
    """Health check for Render"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup():
    """Set webhook on startup"""
    webhook_url = f"https://telegram-bot-worker.onrender.com/webhook"
    await application.bot.set_webhook(webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
