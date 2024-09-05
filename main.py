import asyncio
from aiogram import Bot, Dispatcher
from database import create_tables
from handlers import register_handlers

API_TOKEN = '6897823883:AAEbeOeXFY2zYzhzgQe6C8UmiVvOx9xSWZY'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

async def main():
    await create_tables()
    register_handlers(dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
