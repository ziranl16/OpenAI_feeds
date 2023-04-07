import praw
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import time

# Set up Reddit API credentials
try:
    reddit = praw.Reddit(client_id="client_id",
                         client_secret="client_secret",
                         user_agent="user_agent")
except Exception as e:
    print(f"Error setting up Reddit API: {e}")

# Set up Telegram bot token
try:
    updater = Updater("updater", use_context=True)
except Exception as e:
    print(f"Error setting up Telegram bot: {e}")

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Set the default upvote threshold
upvote_threshold = 10


# Function to fetch posts from OpenAI subreddit
def fetch_top_posts(threshold=upvote_threshold, retries=3):
    top_posts = []
    for attempt in range(retries):
        try:
            subreddit = reddit.subreddit("OpenAI")

            for post in subreddit.top('day', limit=10):
                if post.score > threshold:
                    top_posts.append(f"{post.title}\n{post.url}")
            break
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                print(f"Error fetching top posts from Reddit after {retries} attempts: {e}")

    return top_posts


# Function to send top posts to a specified chat
def send_posts(update: Update, context: CallbackContext, threshold=upvote_threshold):
    chat_id = update.effective_chat.id
    top_posts = fetch_top_posts(threshold=threshold)

    for post in top_posts:
        for attempt in range(3):
            try:
                context.bot.send_message(chat_id=chat_id, text=post)
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    print(f"Error sending post to chat after 3 attempts: {e}")
                    context.bot.send_message(chat_id=chat_id, text="An error occurred while sending a post.")

    if not top_posts:
        context.bot.send_message(chat_id=chat_id, text="No trending posts today.")


def get_posts(update: Update, context: CallbackContext):
    try:
        threshold = int(context.args[0])
    except IndexError:
        threshold = upvote_threshold
    except ValueError:
        update.message.reply_text("Please provide a valid integer for the upvote threshold")

    send_posts(update, context=context, threshold=threshold)


# Function to handle /start command
def start(update: Update, context: CallbackContext):
    intro_msg = "Hi there! I'm a bot CREATED BY CHATGPT WITHIN 30 MINS that provides daily trending posts from the " \
                "OpenAI subreddit. \n" \
                "Here are the available commands:\n" \
                "/start - Start the bot and get a brief introduction\n" \
                "/help - see the help messages.\n" \
                "/get_posts [upvote_threshold] - Get today's trending posts from the OpenAI subreddit openAI [with " \
                "threshold for upvote].\n "
    update.message.reply_text(intro_msg)


# Function to handle /help command
def help(update: Update, context: CallbackContext):
    help_msg = "Here are the available commands:\n" \
               "/start - Start the bot and get a brief introduction\n" \
               "/help - see the help messages.\n" \
               "/get_posts [upvote_threshold] - Get today's trending posts from the OpenAI subreddit openAI [with " \
               "threshold for upvote].\n "
    update.message.reply_text(help_msg)


# Add command handler to send top posts
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler("get_posts", get_posts))
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("help", help))

# Start the bot
updater.start_polling()

# Keep the script running
updater.idle()
