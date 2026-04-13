"""
Interactive Telegram Bot Handler
Handles user replies in Telegram to send emails
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from gmail_sender import GmailSender
from config import settings
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramBotHandler:
    """
    Handle interactive Telegram conversations
    """
    
    def __init__(self):
        self.gmail = GmailSender(
            email=settings.COMPANY_EMAIL,
            app_password=settings.GMAIL_APP_PASSWORD
        )
        # Store pending emails (in production, use a database)
        self.pending_emails = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user messages"""
        user_id = update.effective_user.id
        message_text = update.message.text.strip()
        
        logger.info(f"Received message from {user_id}: {message_text}")
        
        # Check if user is waiting to provide email
        if user_id in self.pending_emails and self.pending_emails[user_id].get('waiting_for_email'):
            await self.process_email_address(update, context, message_text)
            return
        
        # Handle commands
        command = message_text.upper()
        
        if command == 'SEND':
            await self.handle_send(update, context)
        elif command == 'SKIP':
            await self.handle_skip(update, context)
        elif command == 'STATUS':
            await self.handle_status(update, context)
        else:
            await update.message.reply_text(
                "I didn't understand that. Try:\n"
                "• SEND - to send the last email draft\n"
                "• SKIP - to skip the current lead\n"
                "• /help - for more help"
            )
    
    async def handle_send(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle SEND command"""
        user_id = update.effective_user.id
        
        # Store that we're waiting for email address
        self.pending_emails[user_id] = {
            'waiting_for_email': True,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        await update.message.reply_text(
            "📧 Great! Please provide the prospect's email address:\n\n"
            "Example: john@example.com"
        )
    
    async def handle_skip(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle SKIP command"""
        user_id = update.effective_user.id
        
        if user_id in self.pending_emails:
            del self.pending_emails[user_id]
        
        await update.message.reply_text(
            "✅ Lead skipped. I'll notify you about the next hot lead!"
        )
    
    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle STATUS command"""
        user_id = update.effective_user.id
        
        if user_id in self.pending_emails and self.pending_emails[user_id].get('waiting_for_email'):
            await update.message.reply_text(
                "⏳ Waiting for you to provide an email address.\n\n"
                "Type SKIP to cancel."
            )
        else:
            await update.message.reply_text(
                "✅ No pending actions.\n\n"
                "Waiting for the next lead alert!"
            )
    
    async def process_email_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE, email_text: str):
        """Process the provided email address and send email"""
        user_id = update.effective_user.id
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email_text):
            await update.message.reply_text(
                "❌ That doesn't look like a valid email address.\n\n"
                "Please provide a valid email:\n"
                "Example: john@example.com\n\n"
                "Or type SKIP to cancel."
            )
            return
        
        # Load the last email draft from home directory
        import json
        import os
        draft_data = None
        
        try:
            draft_path = os.path.expanduser('~/last_email_draft.json')
            with open(draft_path, 'r') as f:
                draft_data = json.load(f)
            logger.info(f"Draft loaded from {draft_path}")
        except FileNotFoundError:
            logger.error(f"Draft file not found at {draft_path}")
        except Exception as e:
            logger.error(f"Could not load draft: {e}")
        
        if not draft_data:
            await update.message.reply_text(
                "❌ No email draft found.\n\n"
                "Please capture a lead first using the Chrome extension,\n"
                "then reply SEND when you get the alert."
            )
            del self.pending_emails[user_id]
            return
        
        # Send email
        await update.message.reply_text(
            f"📤 Sending email to {email_text}..."
        )
        
        try:
            success = self.gmail.send_email(
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
                
                # Delete the draft file
                try:
                    import os
                    draft_path = os.path.expanduser('~/last_email_draft.json')
                    os.remove(draft_path)
                    logger.info("Draft file deleted")
                except:
                    pass
            else:
                await update.message.reply_text(
                    f"❌ Failed to send email to {email_text}\n\n"
                    "Please check your Gmail settings and try again."
                )
        
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            await update.message.reply_text(
                f"❌ Error sending email: {str(e)}\n\n"
                "Please try again or contact support."
            )
        
        # Clear pending state
        if user_id in self.pending_emails:
            del self.pending_emails[user_id]


def main():
    """Run the Telegram bot"""
    
    logger.info("Starting Telegram bot handler...")
    
    # Create application
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # Initialize handler
    handler = TelegramBotHandler()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", handler.start))
    application.add_handler(CommandHandler("help", handler.help_command))
    
    # Add message handler for text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler.handle_message))
    
    # Start the bot
    logger.info("Bot is running! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
    