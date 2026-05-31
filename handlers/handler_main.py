from aiogram import Router, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import requests
import os
from dotenv import load_dotenv

# выгрузка дотенва
load_dotenv()

class Form(StatesGroup):
    city = State()

start_router = Router()
text = "Добро пожаловать!\nЯ один из ботов-портфолио.\nЯ помогу определить тебе погоду!\nДля этого введи /help\nМой Создатель - @suetx ."
help_txt = "Напиши /get_weather и введи название своего города и все."

@start_router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(help_txt)

async def get_coordinates(city_name: str):
    geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=ru&format=json"
    
    try:
        response = requests.get(geocoding_url)
        response.raise_for_status()
        data = response.json()
        
        if data and data.get('results'):
            result = data['results'][0]
            return {
                'lat': result['latitude'],
                'lon': result['longitude'],
                'name': result['name'],
                'country': result.get('country', '')
            }
        return None
    except requests.RequestException as e:
        print(f"Ошибка при получении координат: {e}")
        return None


async def get_weather(lat: float, lon: float):
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,relativehumidity_2m,windspeed_10m&timezone=auto"
    
    try:
        response = requests.get(weather_url)
        response.raise_for_status()
        data = response.json()
        
        if data and 'current_weather' in data:
            current = data['current_weather']
            
            
            humidity = None
            if 'hourly' in data and 'relativehumidity_2m' in data['hourly']:
                
                humidity = data['hourly']['relativehumidity_2m'][0]
            
            return {
                'temperature': current['temperature'],
                'windspeed': current['windspeed'],
                'winddirection': current['winddirection'],
                'humidity': humidity
            }
        return None
    except requests.RequestException as e:
        print(f"Ошибка при получении погоды: {e}")
        return None


def get_weather_description(temp: float):
    if temp < -20:
        return "🥶 экстремально холодно"
    elif temp < -10:
        return "❄️ очень холодно"
    elif temp < 0:
        return "☁️ холодно"
    elif temp < 10:
        return "🌡️ прохладно"
    elif temp < 20:
        return "🌤️ тепло"
    elif temp < 30:
        return "☀️ жарко"
    else:
        return "🔥 очень жарко"

@start_router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(text)

@start_router.message(Command("get_weather"))
async def get_weather_command(message: types.Message, state: FSMContext):
    await state.set_state(Form.city)
    await message.answer("Введите ваш город: (Пример: Владикавказ, Москва, Санкт-Петербург)")

@start_router.message(Form.city)
async def process_city(message: types.Message, state: FSMContext):
    if message.text is None:
        await message.answer("Пожалуйста, введите название города текстом.")
        return
    
    city = message.text.strip()
    if not city:  
        await message.answer("Название города не может быть пустым. Попробуйте ещё раз.")
        return
    
   
    loading_msg = await message.answer("🔍 Ищу город и получаю данные о погоде...")
    
    
    city_data = await get_coordinates(city)
    
    if not city_data:
        await loading_msg.delete()
        await message.answer("❌ Город не найден. Попробуйте ввести другое название или проверьте правильность написания.")
        await state.clear()
        return
    
    
    weather_data = await get_weather(city_data['lat'], city_data['lon'])
    
    if not weather_data:
        await loading_msg.delete()
        await message.answer("❌ Не удалось получить данные о погоде. Попробуйте позже.")
        await state.clear()
        return
    
  
    weather_desc = get_weather_description(weather_data['temperature'])

    wind_dir = get_wind_direction(weather_data['winddirection'])
    
    response = f"🌍 **Погода в {city_data['name']}**"
    if city_data['country']:
        response += f", {city_data['country']}"
    
    response += f"\n\n🌡️ **Температура:** {weather_data['temperature']:.1f}°C"
    response += f"\n📝 **Описание:** {weather_desc}"
    
    if weather_data['humidity'] is not None:
        response += f"\n💧 **Влажность:** {weather_data['humidity']}%"
    
    response += f"\n💨 **Ветер:** {weather_data['windspeed']:.1f} км/ч, направление {wind_dir}"
    
    # Добавляем эмодзи в зависимости от погоды
    if weather_data['temperature'] > 25:
        response += "\n\n☀️ Не забудьте головной убор и воду!"
    elif weather_data['temperature'] < 0:
        response += "\n\n🧣 Не забудьте тепло одеться!"
    elif weather_data['windspeed'] > 30:
        response += "\n\n🍃 Сегодня ветрено, одевайтесь теплее!"
    
    await loading_msg.delete()
    await message.answer(response, parse_mode="Markdown")  
    await state.clear()

def get_wind_direction(degrees: float):
    directions = [
        (0, "северное"), (22.5, "северо-северо-восточное"),
        (45, "северо-восточное"), (67.5, "восточно-северо-восточное"),
        (90, "восточное"), (112.5, "восточно-юго-восточное"),
        (135, "юго-восточное"), (157.5, "юго-юго-восточное"),
        (180, "южное"), (202.5, "юго-юго-западное"),
        (225, "юго-западное"), (247.5, "западно-юго-западное"),
        (270, "западное"), (292.5, "западно-северо-западное"),
        (315, "северо-западное"), (337.5, "северо-северо-западное")
    ]
    

    for angle, direction in directions:
        if degrees >= angle:
            continue
        return direction
    return "северное"