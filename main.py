from config import THREADS

import config
import database

import asyncio
import logging
import telebot.async_telebot


bot = telebot.async_telebot.AsyncTeleBot(config.BOT_TOKEN)


@bot.message_handler(chat_types=['private'], commands=['/start'])
async def start(message):
    await bot.send_message(message.chat.id, 'Привет, я Годетта, работаю пока что только в группе, личку не люблю...')
    
    
@bot.message_handler(chat_types=['supergroup',], content_types=['new_chat_members'])
async def welcome_message(message):
    await bot.delete_message(message.chat.id, message.id)
    
    # add user to database.
    user: telebot.types.User = message.from_user
    
    
    # greeting message.
    try:
        # TODO: get greeting message id to delete this shit after time.
        # delete_message() with timeout agrument does not work. mb stupid me idk.
        greeting_message_id = await bot.send_message(message.chat.id,
                                                     message_thread_id=THREADS.get('GREETING_THREAD'),
                                                     text=f"""Приветствую, [{message.from_user.first_name}](tg://user?id={message.from_user.id})\!
                                                     \nПожалуйста, ознакомься с [правилами](https://t.me/godot_help_ru/35/36)\.""",
                                                     parse_mode='MarkdownV2',
                                                     link_preview_options=telebot.types.LinkPreviewOptions(True))
        greeting_message_id = greeting_message_id.message_id
    except Exception as exception:
        logging.error(exception)
        
        await bot.send_message(message.chat.id,
                               message_thread_id=THREADS.get('GREETING_THREAD'),
                               text="Упс, что-то пошло не так!")
        

@bot.message_handler(chat_types=['supergroup',], content_types=['left_chat_member'])
async def clear_leave_message(message):
    await bot.delete_message(message.chat.id, message.id)
    

@bot.message_handler(chat_types=['supergroup'], func=lambda message: True)
async def listen_to_karma(message):
    pass


if __name__ == '__main__':
    asyncio.run(bot.polling())
    