from aiogram import Bot,Dispatcher, types, F
from aiogram.fsm.state import State,StatesGroup
import asyncio
import logging
import os
from dotenv import load_dotenv
from config import countries
from aiogram.fsm.context import FSMContext
from handlers.handler_main import start_router
import requests



load_dotenv()

TOKEN = os.getenv("TOKEN")
if TOKEN is None:
    raise ValueError("Переменная токен не найдена")
#логи
logging.basicConfig(level=logging.INFO)

#инциализация
bot = Bot(token=TOKEN)
dp = Dispatcher()

#роутеры ыыы

dp.include_router(start_router)

async def main():
    await dp.start_polling(bot)

    

if __name__ == "__main__":
    asyncio.run(main())