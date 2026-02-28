import os
import pandas as pd
import instaloader
from instaloader import Post, Profile
from instaloader import (
    ProfileNotExistsException,
    ConnectionException,
    BadResponseException,
    QueryReturnedForbiddenException,
    LoginRequiredException
)
import json

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes


# PUT YOUR TOKEN HERE
TOKEN = "8778991484:AAETLAVco3ojpCXj_Fqlr-upRv_YUlkbY8I"


# INSTALOADER
L = instaloader.Instaloader(
user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
)


# Extract shortcode
def get_shortcode(url):

    try:
        url = url.strip().split('?')[0]
        parts = url.rstrip('/').split('/')

        if 'reels' in parts:
            return parts[parts.index('reels') + 1]

        elif 'reel' in parts:
            return parts[parts.index('reel') + 1]

        elif 'p' in parts:
            return parts[parts.index('p') + 1]

        return None

    except:
        return None


# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Send Reel Link\n\nBot will send NEW reels in Excel file."
    )



# HANDLE USER MESSAGE
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_input = update.message.text.strip()

    await update.message.reply_text("Processing...")

    shortcode = get_shortcode(user_input)

    if not shortcode:

        await update.message.reply_text("Error")
        return


    try:

        # Reference Reel
        ref_post = Post.from_shortcode(L.context, shortcode)

        username = ref_post.owner_username
        ref_date = ref_post.date_utc


        # Profile
        profile = Profile.from_username(L.context, username)


        if profile.is_private:

            await update.message.reply_text(
                "Cannot access this account (18+ or restricted)"
            )
            return


        new_reels_links = []


        # Find new reels
        for post in profile.get_posts():

            if post.date_utc <= ref_date:
                break

            if post.is_video:

                reel_url = f"https://www.instagram.com/reels/{post.shortcode}/"
                new_reels_links.append(reel_url)



        if not new_reels_links:

            await update.message.reply_text(
                f"Account: {username}\nNo New Reels"
            )
            return



        ###################################
        # SAVE TXT FILE
        ###################################

        txtname = f"{username}_reels.txt"

        with open(txtname,"w",encoding="utf-8") as f:

            f.write(f"Username: {username}\n\n")

            for link in new_reels_links:

                f.write(link+"\n")



        ###################################
        # SAVE EXCEL FILE
        ###################################

        xlsxname = f"{username}_reels.xlsx"

        df = pd.DataFrame(new_reels_links, columns=["Reel Links"])

        df.to_excel(xlsxname,index=False)



        ###################################
        # SEND FILES
        ###################################

        await update.message.reply_text(
            f"Account: {username}\nTotal New Reels: {len(new_reels_links)}"
        )


        await update.message.reply_document(
            document=open(xlsxname,"rb")
        )


        await update.message.reply_document(
            document=open(txtname,"rb")
        )


        await update.message.reply_text("FINISHED")



    except (LoginRequiredException, QueryReturnedForbiddenException):

        await update.message.reply_text(
            "Cannot access this account (18+ or restricted)"
        )


    except (ProfileNotExistsException,
            BadResponseException,
            json.JSONDecodeError,
            ConnectionException):

        await update.message.reply_text("Error")


    except Exception:

        await update.message.reply_text("Error")



###################################
# RUN TELEGRAM BOT
###################################

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(MessageHandler(filters.TEXT, handle_message))


print("BOT RUNNING...")

app.run_polling()