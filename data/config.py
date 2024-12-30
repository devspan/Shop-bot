import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot token
BOT_TOKEN = str(os.getenv("BOT_TOKEN"))
print(f"Loaded token: {BOT_TOKEN[:5]}...{BOT_TOKEN[-5:]}")

# List of admins
ADMINS = [int(admin_id.strip()) for admin_id in os.getenv("ADMINS", "").split(',') if admin_id.strip()]
print(f"Loaded admins: {ADMINS}")

# Webhook settings
WEBHOOK_HOST = str(os.getenv("WEBHOOK_HOST", ""))
WEBHOOK_PATH = str(os.getenv("WEBHOOK_PATH", ""))
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Webserver settings
WEBAPP_HOST = str(os.getenv("WEBAPP_HOST", "0.0.0.0"))
WEBAPP_PORT = int(os.getenv("PORT", 5000))
