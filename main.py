import config
import database
import globals

import asyncio
import logging
import karma
import telebot.async_telebot


logging.basicConfig(level=logging.INFO, filename="epta_logi.log",filemode="a",
                    format="%(asctime)s %(levelname)s %(message)s")

bot = telebot.async_telebot.AsyncTeleBot(config.BOT_TOKEN)


@bot.message_handler(chat_types=['private'], commands=['/start'])
async def start(message):
    await bot.send_message(message.chat.id, 'Привет, я Годетта, работаю пока что только в группе, личку не люблю...')
    

@bot.message_handler(chat_types=['supergroup',], content_types=['new_chat_members'])
async def welcome_message(message):
    await bot.delete_message(message.chat.id, message.id)
    
    # add user to database.
    karma.check_user_in_database(message.from_user)
    
    # greeting message.
    try:
        # TODO: get greeting message id to delete this shit after time.
        # delete_message() with timeout agrument does not work. mb stupid me idk.
        greeting_text = f"""Приветствую, [{message.from_user.first_name}](tg://user?id={message.from_user.id})\!
                        \nПожалуйста, ознакомься с [правилами](https://t.me/godot_help_ru/35/36)\."""
        await bot.send_message(message.chat.id,
                                message_thread_id=globals.THREADS.get('GREETING_THREAD'),
                                text=greeting_text,
                                parse_mode='MarkdownV2',
                                link_preview_options=telebot.types.LinkPreviewOptions(True))
    except Exception as exception:
        logging.error(exception)
        await bot.send_message(message.chat.id,
                               message_thread_id=globals.THREADS.get('GREETING_THREAD'),
                               text="Упс, что-то пошло не так!")
        

@bot.message_handler(chat_types=['supergroup',], content_types=['left_chat_member'])
async def clear_leave_message(message):
    await bot.delete_message(message.chat.id, message.id)
    

@bot.message_handler(chat_types=['supergroup'], func=lambda message: True)
async def listen_to_karma(message):
    # govnokod starts here.
    if message.text.startswith(globals.KARMA_THANKS):
        karma.check_user_in_database(message.from_user)
        karma.check_user_in_database(message.reply_to_message.from_user)
        karma.change_user_karma(message.reply_to_message.from_user)
        await bot.reply_to(message, f'{message.from_user.first_name} ({karma.get_user_karma(message.from_user)})\
                            повысил карму {message.reply_to_message.from_user}\
                            ({karma.get_user_karma(message.reply_to_message.from_user)}).')
    elif message.text.startswith(globals.KARMA_CONDEMNATION):
        karma.check_user_in_database(message.from_user)
        karma.check_user_in_database(message.reply_to_message.from_user)
        karma.change_user_karma(message.reply_to_message, -1)
        await bot.reply_to(message, f'{message.from_user.first_name} ({karma.get_user_karma(message.from_user)})\
                            понизил карму {message.reply_to_message.from_user}\
                            ({karma.get_user_karma(message.reply_to_message.from_user)}).')


if __name__ == '__main__':
    asyncio.run(bot.polling())
    