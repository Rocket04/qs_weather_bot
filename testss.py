import logging
from langcodes import LANGUAGE_NAME_IMPORT_MESSAGE, Language
import spacy
import requests
import json
from geopy.geocoders import Nominatim
from pydispatch import dispatcher
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, filters, Filters

API_KEY = 'd69fd2b7fc4f7d3f8a2d8016bce3da2f'
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'

# Load the spaCy language models for English
nlp_en = spacy.load('en_core_web_sm')
nlp_ru = spacy.load('ru_core_news_sm')


# Replace YOUR_API_TOKEN with your Telegram bot API token
bot = Bot(token='6185530892:AAHJlXZGun7fER2PkEZ4wj0Y12_7ZDeA4jE')


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Hi {user.first_name}! How can I help you?")

def extract_city(text, language='en'):
    if language == 'en':
        doc = nlp_en(text)
    elif language == 'ru':
        doc = nlp_ru(text)
    else:
        return None

    for ent in doc.ents:
        if ent.label_ in ['GPE', 'LOC', 'FAC']:
            return ent.text.strip().lower()

    return None

def get_weather(city):
    geolocator = Nominatim(user_agent='telegram_weather_bot')
    location = geolocator.geocode(city, exactly_one=True, language='en')
    if location:
        lat, lon = location.latitude, location.longitude
        url = f'{BASE_URL}?lat={lat}&lon={lon}&appid={API_KEY}'
        response = requests.get(url)
        if response.status_code == 200:
            data = json.loads(response.text)
            weather = data['weather'][0]['main']
            temperature = data['main']['temp']
            wind_speed = data['wind']['speed']
            thunderstorm = any(weather in x for x in ['Thunderstorm', 'Squall'])
            return weather, temperature, wind_speed, thunderstorm
    return None
    
def get_clothing_recommendation(temperature, language=nlp_en):
    if language == nlp_en:
        if temperature > 30:
            return "It's very hot. Wear lightweight, light-colored, and loose-fitting clothes to stay cool."
        elif temperature > 20:
            return "It's warm. Wear light-colored and breathable clothes to stay comfortable."
        elif temperature > 10:
            return "It's mild. Wear a light jacket or a sweater to stay warm."
        elif temperature > 0:
            return "It's chilly. Wear a warm jacket or a coat to stay warm."
        else:
            return "It's very cold. Wear a heavy coat, a hat, and gloves to stay warm."

def send_weather(chat_id, text, language=nlp_en):
    
    city = extract_city(text, language)
    if not city:
        bot.send_message(chat_id, "Sorry, I couldn't recognize the city name in your message.")
        return

    
    greeting = "Hello! "
    the_weather_in = "The weather in "
    and_the_temperature_is = " and the temperature is "
    its = "It's "
    windy = "windy. Wear a windbreaker or a jacket to protect yourself from the wind."
    raining = "It's raining. Wear a raincoat or take an umbrella to stay dry."
   
        
    weather, temperature, wind_speed, thunderstorm = get_weather(city)
    if not (weather and temperature):
        bot.send_message(chat_id, "Sorry, I couldn't get the weather information for this city.")
        return
        
    # Convert temperature from Kelvins to Celsius
    temperature = temperature - 273.15
    
    message = f'{greeting}{the_weather_in}{city}{and_the_temperature_is}{temperature:.1f} °C. {its}{weather}.\n\n'
    clothing_recommendation = get_clothing_recommendation(temperature)
    message += clothing_recommendation
    
    if wind_speed > 10:
        message += f"\n\n{its}{windy}"
    
    if 'Rain' in weather:
        message += f"\n\n{its}{raining}"
        
    if thunderstorm:
        if language is nlp_en:
            message += '\n\n⚠️ Warning: Thunderstorm expected. Please take necessary precautions.'


    bot.send_message(chat_id, message)


def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages that contain a city name."""
    text = update.message.text
    city = extract_city(text)
    if city:
        weather_info = city
        if weather_info:
            send_weather(update.message.chat_id, weather_info, context.user_data.get('language', 'en'))
        else:
            bot.send_message(update.message.chat_id, "Sorry, I couldn't find weather information for the city.")
    else:
        bot.send_message(update.message.chat_id, "Sorry, I couldn't recognize the city name in your message.")

def main():
    updater = Updater(token='6185530892:AAHJlXZGun7fER2PkEZ4wj0Y12_7ZDeA4jE', use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()