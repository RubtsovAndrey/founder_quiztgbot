import aiosqlite
from aiogram import types, Dispatcher
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F
from database import get_quiz_index, update_quiz_index, update_user_score, finalize_quiz, DB_NAME
from quiz_data import quiz_data


def generate_options_keyboard(answer_options, right_answer):
    builder = InlineKeyboardBuilder()
    for index, option in enumerate(answer_options):
        builder.add(types.InlineKeyboardButton(
            text=option,
            callback_data=f"answer_{index}")
        )
    builder.adjust(1)
    return builder.as_markup()


async def process_answer(callback: types.CallbackQuery):
    selected_index = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    current_question_index = await get_quiz_index(user_id)

    if current_question_index >= len(quiz_data):
        await callback.message.answer("Квиз завершен. Вы уже ответили на все вопросы.")
        return

    correct_index = quiz_data[current_question_index]['correct_option']
    selected_option = quiz_data[current_question_index]['options'][selected_index]
    correct_option = quiz_data[current_question_index]['options'][correct_index]

    if selected_index == correct_index:
        await callback.message.answer(f"Вы выбрали: {selected_option}. Это верно!")
        await update_user_score(user_id, True)
    else:
        await callback.message.answer(f"Вы выбрали: {selected_option}. Это неверно. Правильный ответ: {correct_option}")
        await update_user_score(user_id, False)

    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    current_question_index += 1
    if current_question_index < len(quiz_data):
        await update_quiz_index(user_id, current_question_index)
        await get_question(callback.message, user_id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")
        await finalize_quiz(user_id)


async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    await reset_user_score(user_id)
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    await message.answer("Добро пожаловать в квиз! Нажмите 'Начать игру', чтобы начать.",
                         reply_markup=builder.as_markup(resize_keyboard=True))


async def cmd_quiz(message: types.Message):
    user_id = message.from_user.id
    await reset_user_score(user_id)
    await message.answer("Давайте начнем квиз!")
    await new_quiz(message)


async def cmd_stats(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT user_id, correct_answers FROM user_scores') as cursor:
            results = await cursor.fetchall()
            stats = '\n'.join([
                f"Пользователь {user_id}: {correct_answers} "
                f"{'правильный ответ' if correct_answers == 1 else 'правильных ответа'}"
                for user_id, correct_answers in results
            ])
            await message.answer(f"Статистика:\n{stats}")


async def get_question(message, user_id):
    current_question_index = await get_quiz_index(user_id)

    if current_question_index >= len(quiz_data):
        await message.answer("Квиз завершен. Вы ответили на все вопросы.")
        return

    correct_index = quiz_data[current_question_index]['correct_option']
    opts = quiz_data[current_question_index]['options']
    kb = generate_options_keyboard(opts, opts[correct_index])
    await message.answer(f"{quiz_data[current_question_index]['question']}", reply_markup=kb)


async def new_quiz(message):
    user_id = message.from_user.id
    await update_quiz_index(user_id, 0)
    await get_question(message, user_id)


async def reset_user_score(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('UPDATE user_scores SET correct_answers = 0 WHERE user_id = ?', (user_id,))
        await db.commit()


def register_handlers(dp: Dispatcher):
    dp.message(Command("start"))(cmd_start)
    dp.message(F.text == "Начать игру")(cmd_quiz)
    dp.message(Command("stats"))(cmd_stats)
    dp.callback_query(F.data.startswith("answer_"))(process_answer)
