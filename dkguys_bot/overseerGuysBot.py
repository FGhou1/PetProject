import re
import brawlstats
import asyncio

from config import Config
from sqlClass import Database

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile 

bot = Bot(Config.bot_token)
dp = Dispatcher()
db = Database()

global photo
photo=FSInputFile(path=Config.example_img_path)

global status_waiting 
status_waiting = {}

global brawlstats_ID_flag 
brawlstats_ID_flag = {}

global sent_message_admin
sent_message_admin = {}

global sent_message_user
sent_message_user = {}

global picture_sender
picture_sender = {}

global player_list
player_list = {}

client = brawlstats.Client(Config.API_key)

@dp.message(Command("start"))
async def start_handler(message: Message):


    if str(message.chat.id) == Config.admin_chat:
        pass
    else:
        user_id = message.from_user.id

        global status_waiting
        status_waiting[user_id] = False

        try:     
            if db.check_user(user_id): 
                await message.reply("Прив! Рад тебя видеть снова :3\nЗапомнил тебя с прощлого раза 👾")

            else:
                await message.reply("🆔 Введите свой BrawlStars тег:\n<blockquote>Пример:  PPGCYCVYL</blockquote>\n<b>Будьте внимательны! Не путайте ноль и букву 'O', тк её не может быть в теге. </b>", parse_mode="html")


        except Exception as e: await message.reply(f"Произошла ошибка {e}")


@dp.message(F.text)
async def register_user(message: Message): 

    if str(message.chat.id) == Config.admin_chat:
        pass
    
    else:

        user_id = message.from_user.id

        if status_waiting[user_id] == False:

            if db.check_user(user_id) == False:

                user_teg = message.text.strip().upper()

                if re.match(r'#?[0289PYLQGRJCUV]{8,10}$', user_teg):

                    if user_teg[0] == '#': user_teg = user_teg[1:]

                    try:
                        global player_list
                        player_list[user_id] = client.get_player(user_teg)

                        await message.reply("Отправьте скрин вашего профиля.\nДля подтверждения того, что тег принадлежит вам.")

                        global photo
                        await bot.send_photo(chat_id=message.chat.id, photo=photo, caption="<blockquote>Пример</blockquote>", parse_mode="html")

                        global brawlstats_ID_flag 
                        brawlstats_ID_flag[user_id] = True

                    except brawlstats.errors.NotFoundError: await message.reply("Ошибка! Не удалось найти профиль.")
                    except brawlstats.errors.RequestError as e: await message.reply("Возникли неполадки :(")
                else:  
                    await message.reply("Ошибка! Неверный ввод. \nМожно использовать только:\n • латинские буквы (PYLQGRJCUV)\n • цифры (0289)\n")

            else: await message.reply("Я уже дал тебе все что мог 😓\nБольше я ничем помочь не могу... 😶")

        else: await message.reply("Ожидаем, пока админ налюбуется ващей картинкой 😶‍🌫️")

@dp.message(F.photo)
async def handle_photo(message: Message):

    global player_list
    global status_waiting

    if str(message.chat.id) == Config.admin_chat: pass

    else:

        user_id = message.from_user.id

        if status_waiting[user_id] == False:
            
            if db.check_user(user_id) == False:

                global brawlstats_ID_flag

                if brawlstats_ID_flag[user_id] == True:
                    
                    user_id = message.from_user.id

                    username = (f"@{message.from_user.username}" if message.from_user.username else "?").replace("_", "\\_")

                    photo = message.photo[-1]

                    global picture_sender
                    picture_sender[user_id] = file_id = photo.file_id

                    kb = [
                        InlineKeyboardButton(text="✅ Одобрить", callback_data=f'approve_{user_id}'),
                        InlineKeyboardButton(text="❌ Отклонить", callback_data=f'reject_{user_id}')
                    ]

                    keyboard = InlineKeyboardMarkup(inline_keyboard=[kb])

                    global sent_message_admin
                    sent_message_admin[user_id] = await bot.send_photo(
                        chat_id=Config.admin_chat,
                        photo=file_id,
                        caption=(
                            f"📸 *Новое изображение!* \n"
                            f"*От:* {username}\n"
                            f"🆔 *User ID:* `{user_id}`\n"
                            f"⬇️*Указанные параметры*⬇️\n"
                            f"*Имя ака:* `{player_list[user_id].name}`\n"
                            f"*Тег:* `{player_list[user_id].tag}`\n"
                            f"*Кубки:* `{player_list[user_id].trophies}`\n"
                        ),
                        parse_mode="Markdown", reply_markup=keyboard
                    )

                    global sent_message_user
                    sent_message_user[user_id] = await message.reply("✅ Ваше изображение отправлено на проверку. Ожидайте дальнейших инструкций.")

                    status_waiting[user_id] = True  
                    brawlstats_ID_flag[user_id] = False
                
                else: await message.reply("Сначала укажите свой тег!")

            else: await message.reply("Я уже дал тебе все что мог 😓\nБольше я ничем помочь не могу... 😶")

        else: await message.reply("Ожидаем, пока админ налюбуется ващей картинкой 😶‍🌫️")
        
@dp.callback_query()
async def process_callback(callback_query: CallbackQuery):

    data = callback_query.data

    user_id = int(data.split('_')[1])

    global player_list
    global sent_message_admin
    global sent_message_user
    global status_waiting
    status_waiting[user_id] = False

    await bot.delete_message(chat_id = user_id, message_id = sent_message_user[user_id].message_id)

    if data.startswith('approve_'):

        try:
            await bot.send_message(chat_id=user_id, text="✅ Ваше изображение было одобрено!") 
            await bot.send_message(
                chat_id=user_id, 
                text= (f"Спасибо, {player_list[user_id].name}!\n" 
                       f"Вы были успешно зарегистрированы.\n"
                       f"Ссылка на группу: [DK | Guys]({Config.group_link})"
                ), parse_mode="Markdown"
            )

            try:
                db.add_users(user_id, player_list[user_id].tag, player_list[user_id].trophies)
            except Exception as error:
                await callback_query.answer("⚠️ Произошла ошибка при добаавлении игрока!")

            await callback_query.answer(f"✅ Чел принят на работу")

            await bot.send_photo(
                        chat_id=Config.save_chat,
                        photo=picture_sender[user_id],
                        caption=(
                            f"*User ID:* `{user_id}`\n"
                            f"*Тег:* `{player_list[user_id].tag}`\n"
                        ),
                        parse_mode="Markdown"
            )
        
        except Exception as e:
            await callback_query.answer("⚠️ Произошла ошибка при обработке команды одобрения.")
        
        del status_waiting[user_id]
        del brawlstats_ID_flag[user_id]
        del player_list[user_id]

    elif data.startswith('reject_'):
        user_id = int(data.split('_')[1])

        try:
            await bot.send_message(chat_id=user_id, text=f"❌ Попытка авторизации отклонена.\nПрична: несоответствие данных.\nПройдите регистрацию заново.")
            await callback_query.answer(f"❌ Чел пошел на хуй.")
        
        except Exception as e:
            await callback_query.answer("⚠️ Произошла ошибка при обработке команды отклонения.")

    await bot.delete_message(chat_id = Config.admin_chat, message_id = (sent_message_admin[user_id]).message_id)

    del sent_message_user[user_id]
    del sent_message_admin[user_id]
    del picture_sender[user_id]

async def main(): await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

