import logging
import spacy
import requests
import json
from pydispatch import dispatcher
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, filters, Filters

API_KEY = 'd69fd2b7fc4f7d3f8a2d8016bce3da2f'
BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'

# Load the spaCy language models for English, Russian and Kazakh
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
        if ent.label_ == 'GPE':
            return ent.text
    return None

def get_weather(city):
    url = f'{BASE_URL}?q={city}&appid={API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        weather = data['weather'][0]['main']
        temperature = data['main']['temp']
        wind_speed = data['wind']['speed']
        thunderstorm = any(weather in x for x in ['Thunderstorm', 'Squall'])
        return weather, temperature, wind_speed, thunderstorm
    else:
        return None

def get_clothing_recommendation(temperature, language='en'):
    if language == 'en':
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
    elif language == 'ru':
        if temperature > 30:
            return "Жарко. Наденьте легкую, светлую и свободную одежду, чтобы оставаться прохладным."
        elif temperature > 20:
            return "Тепло. Наденьте светлую и дышащую одежду, чтобы чувствовать себя комфортно."
        elif temperature > 10:
            return "Прохладно. Наденьте легкую куртку или свитер, чтобы оставаться теплым."
        elif temperature > 0:
            return "Холодно. Наденьте теплую куртку или пальто, чтобы оставаться теплым."
        else:
            return "Очень холодно. Наденьте теплое пальто, шапку и перчатки, чтобы оставаться теплым."

def send_weather(chat_id, text, language='en'):
    if language == 'en':
        city = extract_city(text, 'en')
        greeting = "Hello! "
        sorry = "Sorry, something does not work, write to our programmer)"
        the_weather_in = "The weather in "
        and_the_temperature_is = " and the temperature is "
        its = "It's "
        windy = "windy. Wear a windbreaker or a jacket to protect yourself from the wind."
        raining = "It's raining. Wear a raincoat or take an umbrella to stay dry."
    elif language == 'ru':
        city = extract_city(text, 'ru')
        greeting = "Здравствуйте! "
        sorry = "Извините, что-то не работает, напишите нашему программисту)"
        the_weather_in = "Погода в городе "
        and_the_temperature_is = " и температура "
        its = "Сейчас "
        windy = "ветрено. Наденьте ветровку или куртку, чтобы защитить себя от ветра."
        raining = "идет дождь. Наденьте плащ или возьмите зонт, чтобы остаться сухим."
    else:
        bot.send_message(chat_id, "Sorry, I don't support this language yet.")
        return
    if city:
        weather, temperature, wind_speed, thunderstorm = get_weather(city)
        if weather and temperature:
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
                if language == 'en':
                    message += '\n\n⚠️ Warning: Thunderstorm expected. Please take necessary precautions.'
                elif language == 'ru':
                    message += '\n\n⚠️ Внимание: Ожидается гроза. Примите необходимые меры.'

            bot.send_message(chat_id, message)
        else:
            bot.send_message(chat_id, f'{sorry}')

def handle_message(update, context):
    text = update.message.text
    # do something with the text message
    update.message.reply_text("Hello, type any city/Привет, напиши любой город")

def main():
    updater = Updater(token='6185530892:AAHJlXZGun7fER2PkEZ4wj0Y12_7ZDeA4jE', use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    updater.start_polling()
    updater.idle()

main()