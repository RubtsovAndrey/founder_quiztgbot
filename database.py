import aiosqlite

DB_NAME = 'quiz_bot.db'

async def create_tables():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY, question_index INTEGER)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS user_scores (user_id INTEGER PRIMARY KEY, correct_answers INTEGER)''')
        await db.commit()

async def get_quiz_index(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = ?', (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0

async def update_quiz_index(user_id, index):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR REPLACE INTO quiz_state (user_id, question_index) VALUES (?, ?)', (user_id, index))
        await db.commit()

async def update_user_score(user_id, correct):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT correct_answers FROM user_scores WHERE user_id = ?', (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                current_score = result[0]
                new_score = current_score + (1 if correct else 0)
                await db.execute('UPDATE user_scores SET correct_answers = ? WHERE user_id = ?', (new_score, user_id))
            else:
                new_score = 1 if correct else 0
                await db.execute('INSERT INTO user_scores (user_id, correct_answers) VALUES (?, ?)', (user_id, new_score))
        await db.commit()

async def finalize_quiz(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT correct_answers FROM user_scores WHERE user_id = ?', (user_id,)) as cursor:
            result = await cursor.fetchone()
            if result:
                pass
            else:
                await db.execute('INSERT INTO user_scores (user_id, correct_answers) VALUES (?, ?)', (user_id, 0))
        await db.commit()
