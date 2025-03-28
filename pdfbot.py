import fitz  # PyMuPDF
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext

TOKEN = "7695782694:AAGXXwOs9sCVA2BMTeLKkv9GpaYFgSrR-8c"  # Replace with your bot token

PDF, SEARCH = range(2)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Please send me a PDF file.")
    return PDF

async def handle_pdf(update: Update, context: CallbackContext) -> int:
    file = update.message.document
    if file.mime_type != "application/pdf":
        await update.message.reply_text("This is not a PDF file. Please send a valid PDF.")
        return PDF

    file_path = "downloaded.pdf"
    new_file = await file.get_file()
    await new_file.download_to_drive(file_path)

    await update.message.reply_text("PDF received! Now send me a word to search for.")
    context.user_data["pdf_path"] = file_path  # Save file path
    return SEARCH

async def search_word(update: Update, context: CallbackContext) -> int:
    word = update.message.text.lower()
    pdf_path = context.user_data.get("pdf_path")

    if not pdf_path:
        await update.message.reply_text("No PDF found. Please send a PDF first.")
        return PDF

    doc = fitz.open(pdf_path)
    found_pages = []

    for page_num in range(len(doc)):
        text = doc[page_num].get_text("text").lower()
        if word in text:
            found_pages.append(page_num + 1)  # Pages are 1-based

    if found_pages:
        await update.message.reply_text(f"'{word}' found on pages: {', '.join(map(str, found_pages))}")
    else:
        await update.message.reply_text(f"'{word}' not found in the PDF.")

    os.remove(pdf_path)  # Delete file after processing
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Process canceled.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PDF: [MessageHandler(filters.Document.MimeType("application/pdf"), handle_pdf)],
            SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_word)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    logging.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
