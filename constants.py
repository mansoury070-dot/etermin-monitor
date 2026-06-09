
import os
from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE = "user_config.json"
MY_BOT_TOKEN = os.getenv("MY_TELEGRAM_BOT_TOKEN")
MY_BOT_USERNAME = "my_appointment_app_bot"
ENCRYPT_KEY = os.getenv("ENCRYPT_KEY")




OFFICE_COLLECTION = {
    "Ausländerbehörde Süd": ("qtermin-stadt-duisburg-abh-sued", 71400),
    "Ausländerbehörde Hamborn": ("stadt-duisburg-abh-homberg", 53036),
    "Ausländerbehörde Homberg": ("stadt-duisburg-abh-homberg", 53036),
    "Straßenverkehrsamt": ("stadt-duisburg-zul", 51901),
    "Fahrerlaubnisbehörde": ("qterminstadtduisburgstva", 41433),
    "Bürgerservice": ("stadt-duisburg", 39575) 
    }


