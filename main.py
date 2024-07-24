import config
import database
import globals
import karma

import asyncio
import logging
import telebot.async_telebot
import string


logging.basicConfig(level=logging.INFO, filename="epta_logi.log",filemode="a",
                    format="%(asctime)s %(levelname)s %(message)s", encoding='utf-8')

bot = telebot.async_telebot.AsyncTeleBot(config.BOT_TOKEN)


async def get_message_reply_user(message):
    user = None
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        if message.reply_to_message.from_user.is_bot:
            return None
        return user
    
    
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
                                link_preview_options=telebot.types.LinkPreviewOptions(False))
    except Exception as exception:
        logging.exception(exception)
        await bot.send_message(message.chat.id,
                               message_thread_id=globals.THREADS.get('GREETING_THREAD'),
                               text="Упс, что-то пошло не так!")
        

@bot.message_handler(chat_types=['supergroup',], content_types=['left_chat_member'])
async def clear_leave_message(message):
    await bot.delete_message(message.chat.id, message.id)
    

@bot.message_handler(chat_types=['supergroup'], commands=['warn'])
async def warn_user(message):
    admins = await bot.get_chat_administrators(message.chat.id)
    admins_id = [id.user.id for id in admins]
    if message.from_user.id in admins_id:
        if message.reply_to_message.from_user.id in admins_id:
            await bot.reply_to(message, 'Господа админы, прошу выяснять отношения в личных сообщениях.')
            return
        result = database.give_warn(message.reply_to_message.from_user)
        if result == 'err':
            await bot.reply_to(message, 'Произошла ошибка, чекни логи.')
        elif result == 'muted':
            await bot.reply_to(message, f'Пользователь {message.reply_to_message.from_user.full_name} ({karma.get_user_karma(message.reply_to_message.from_user)}) получил последнее предупреждение.\nТеперь посидит в молчанке.')
            await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id,
                                           None, False, False, False, False, False, False,
                                           False, False)
        else:
            await bot.reply_to(message, f'Пользователь {message.reply_to_message.from_user.full_name} ({karma.get_user_karma(message.reply_to_message.from_user)}) получил предупреждение.\nСейчас их {database.get_warns_count(message.reply_to_message.from_user)}.')
        

@bot.message_handler(chat_types=['supergroup'], commands=['unmute'])
async def unmute_user(message):
    admins = await bot.get_chat_administrators(message.chat.id)
    admins_id = [id.user.id for id in admins]
    if message.from_user.id in admins_id:
        if message.reply_to_message.from_user.id in admins_id:
            await bot.reply_to(message, 'Господа админы, прошу выяснять отношения в личных сообщениях.')
            return
        database.clear_warns(message.reply_to_message.from_user)
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id,
                                       None, True, True,)
        await bot.reply_to(message, f'Так и быть, выходи из молчанки, [{message.reply_to_message.from_user.first_name}](tg://user?id={message.reply_to_message.from_user.id})\.',
                           parse_mode='MarkdownV2')
        
        
@bot.message_handler(chat_types=['supergroup'], commands=['ban'])
async def ban_user(message):
    admins = await bot.get_chat_administrators(message.chat.id)
    admins_id = [id.user.id for id in admins]
    if message.from_user.id in admins_id:
        if message.reply_to_message.from_user.id in admins_id:
            await bot.reply_to(message, 'Господа админы, прошу выяснять отношения в личных сообщениях.')
            return
        await bot.ban_chat_member(message.chat.id, message.reply_to_message.from_user.id)
        await bot.reply_to(message, f'Пользователь {message.reply_to_message.from_user.full_name} теперь забанен. Мы не жалеем.')
        logging.info(f'User {message.reply_to_message.from_user.full_name} ({message.reply_to_message.from_user.username}) got banned.')        


@bot.message_handler(chat_types=['supergroup'], commands=['stats'])
async def get_user_stats(message):
    user = await get_message_reply_user(message)
    user = message.from_user if not user else user
    await bot.reply_to(message, f'Карма пользователя {user.full_name} сейчас составляет {karma.get_user_karma(user)}.')


@bot.message_handler(chat_types=['supergroup'], func=lambda message: True)
async def listen_to_karma(message):
    # govnokod starts here.
    if not message.reply_to_message.text:
        return
    if message.text.lower().startswith(globals.KARMA_THANKS):
        if message.from_user.id == message.reply_to_message.from_user.id:
            await bot.reply_to(message, 'Я понимаю, что ты самовлюбленный дурак, но не нужно этого.')
            return
        karma.check_user_in_database(message.from_user)
        karma.check_user_in_database(message.reply_to_message.from_user)
        karma.change_user_karma(message.reply_to_message.from_user)
        await bot.reply_to(message, f'{message.from_user.first_name} ({karma.get_user_karma(message.from_user)}) повысил карму {message.reply_to_message.from_user.first_name} ({karma.get_user_karma(message.reply_to_message.from_user)}).')
    elif message.text.lower().startswith(globals.KARMA_CONDEMNATION):
        if message.from_user.id == message.reply_to_message.from_user.id:
            await bot.reply_to(message, 'Я понимаю, что ты самокритичный дурак, но не нужно этого.')
            return
        karma.check_user_in_database(message.from_user)
        karma.check_user_in_database(message.reply_to_message.from_user)
        karma.change_user_karma(message.reply_to_message.from_user, -1)
        await bot.reply_to(message, f'{message.from_user.first_name} ({karma.get_user_karma(message.from_user)}) понизил карму {message.reply_to_message.from_user.first_name} ({karma.get_user_karma(message.reply_to_message.from_user)}).')


if __name__ == '__main__':
    asyncio.run(bot.infinity_polling())
    