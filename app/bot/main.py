import asyncio
import httpx
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from app.config import settings
from app.utils.logging import setup_logger

logger = setup_logger()

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработка команды /start"""
    await message.answer(
        "Здравствуйте! 👋\n\n"
        "Я AI-ассистент службы поддержки по вопросам торгового эквайринга.\n"
        "Задайте мне любой вопрос, и я постараюсь помочь вам!\n\n"
        "Например:\n"
        "• Как сделать возврат?\n"
        "• Какие тарифы на эквайринг?\n"
        "• Что делать, если терминал не работает?"
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработка команды /help"""
    await cmd_start(message)


@dp.message()
async def handle_message(message: types.Message):
    """Обработка всех сообщений"""
    # Показываем индикатор набора текста
    await bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # Отправляем запрос в backend
        async with httpx.AsyncClient(timeout=40.0) as client:
            response = await client.post(
                f"{settings.BACKEND_URL}/api/chat",
                json={
                    "tg_user_id": message.from_user.id,
                    "question": message.text
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data["answer"]
                
                # Отправляем ответ
                await message.answer(answer, parse_mode="HTML")
                
                # Если fallback - уведомляем пользователя
                if data["status"] == "FALLBACK_OPERATOR":
                    logger.info(f"Fallback for user {message.from_user.id}")
            else:
                await message.answer(
                    "Извините, произошла ошибка. Попробуйте еще раз через минуту."
                )
                
    except httpx.TimeoutException:
        await message.answer(
            "Временные технические неполадки. Попробуйте через 2 минуты или обратитесь к оператору."
        )
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        await message.answer(
            "Произошла ошибка. Пожалуйста, попробуйте позже."
        )


async def main():
    """Запуск бота"""
    logger.info("Starting Telegram bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
