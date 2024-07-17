import config
import database


import asyncio
import telebot.async_telebot


bot = telebot.async_telebot.AsyncTeleBot(config.BOT_TOKEN)


@bot.message_handler(commands=['/start'])
async def start(message):
    await bot.send_message(message.chat.id, 'Привет, я Годетта, работаю пока что только в группе, личку не люблю...')
    
    
@bot.message_handler(chat_types=['supergroup',], content_types=['new_chat_members'])
async def welcome_message(message):
    await bot.delete_message(message.chat.id, message.id)
    try:
        greeting_message_id = await bot.send_message(message.chat.id,
                                                     message_thread_id=17,
                                                     text=f"""Приветствую, [{message.from_user.first_name}](tg://user?id={message.from_user.id})\!
                                                     \nПожалуйста, ознакомься с [правилами](https://t.me/godot_help_ru/35/36)\.""",
                                                     parse_mode='MarkdownV2',
                                                     link_preview_options=telebot.types.LinkPreviewOptions(True))
        greeting_message_id = greeting_message_id.message_id
    except Exception as e:
        print(e)
        await bot.send_message(message.chat.id, message_thread_id=17, text="Упс, что-то пошло не так!")
        

@bot.message_handler(chat_types=['supergroup',], content_types=['left_chat_member'])
async def clear_leave_message(message):
    await bot.delete_message(message.chat.id, message.id)
    
    
if __name__ == '__main__':
    asyncio.run(bot.polling())
    