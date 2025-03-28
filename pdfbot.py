import fitz  # PyMuPDF
import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

TOKEN = "7695782694:AAGXXwOs9sCVA2BMTeLKkv9GpaYFgSrR-8c"  # Replace with your bot token

PDF, SEARCH = range(2)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Please send me a PDF file.")
    return PDF

def handle_pdf(update: Update, context: CallbackContext) -> int:
    file = update.message.document
    if file.mime_type != "application/pdf":
        update.message.reply_text("This is not a PDF file. Please send a valid PDF.")
        return PDF

    file_path = os.path.join("downloaded.pdf")
    file = context.bot.get_file(file.file_id)
    file.download(file_path)

    update.message.reply_text("PDF received! Now send me a word to search for.")
    context.user_data["pdf_path"] = file_path  # Save file path
    return SEARCH

def search_word(update: Update, context: CallbackContext) -> int:
    word = update.message.text.lower()
    pdf_path = context.user_data.get("pdf_path")

    if not pdf_path:
        update.message.reply_text("No PDF found. Please send a PDF first.")
        return PDF

    doc = fitz.open(pdf_path)
    found_pages = []

    for page_num in range(len(doc)):
        text = doc[page_num].get_text("text").lower()
        if word in text:
            found_pages.append(page_num + 1)  # Pages are 1-based

    if found_pages:
        update.message.reply_text(f"'{word}' found on pages: {', '.join(map(str, found_pages))}")
    else:
        update.message.reply_text(f"'{word}' not found in the PDF.")

    os.remove(pdf_path)  # Delete file after processing
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Process canceled.")
    return ConversationHandler.END

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PDF: [MessageHandler(Filters.document.mime_type("application/pdf"), handle_pdf)],
            SEARCH: [MessageHandler(Filters.text & ~Filters.command, search_word)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()