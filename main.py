import config
import database
import globals
import karma

import asyncio
import datetime
import logging
import re
import telebot.async_telebot
import string


logging.basicConfig(level=logging.INFO, filename="epta_logi.log",filemode="a",
                    format="%(asctime)s %(levelname)s %(message)s", encoding='utf-8')

bot = telebot.async_telebot.AsyncTeleBot(config.BOT_TOKEN)


async def get_message_reply_user(message):
    user = None
    if not message.reply_to_message.text:
        return
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        if message.reply_to_message.from_user.is_bot:
            return None
        return user
    
    
@bot.message_handler(chat_types=['private'], commands=['start'])
async def start(message):
    await bot.send_message(message.chat.id, 'Привет, я Годетта, работаю пока что только в группе, личку не люблю...')
    

@bot.message_handler(chat_types=['supergroup',], commands=['help'])
async def help_message(message):
    await bot.reply_to(message, f'Вот что я умею:\n\nКоманды для админов:\n/warn - выдать предупреждение нарушителю. На четвертое предупреждение я автоматически поставлю мут.\n/mute [days=int|None]- замутить персонажа.\n/unmute - помиловать нарушителя.\n/ban - просто бан.\n\nКоманды для всех:\n/stats - посмотреть свою статистику или другого человека, ответив на его сообщение.\n/help - спросить у меня, что я умею.\nТакже я умею реагировать на ваши реакции, с помощью которых можно изменять карму другим. Работает это только в топиках Showcase и Полезные материалы.\nПовысить карму можно с помощью 👍, ❤, 🔥.\nПонизить карму можно с помощью 👎, 💩, 🤡.')


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
    
    
@bot.message_handler(chat_types=['supergroup'], commands=['mute'])
async def mute_user(message):
    admins = await bot.get_chat_administrators(message.chat.id)
    admins_id = [id.user.id for id in admins]
    if message.from_user.id in admins_id:
        if message.reply_to_message.from_user.id in admins_id:
            await bot.reply_to(message, 'Господа админы, прошу выяснять отношения в личных сообщениях.')
            return
        mute_after = re.findall(r'\d+', message.text)
        if mute_after:
            days = mute_after[0]
            mute_after = datetime.datetime.now() + datetime.timedelta(days=int(mute_after[0]))
        else:
            mute_after = None
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, mute_after)
        await bot.reply_to(message, f'Ня\-няя, окей, [{message.reply_to_message.from_user.first_name}](tg://user?id={message.reply_to_message.from_user.id}), ты теперь в муте на {days + " дней" if days else "НАВСЕГДА"}\.',
                           parse_mode='MarkdownV2')
        
        
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
            await bot.reply_to(message, f'Пользователь {message.reply_to_message.from_user.full_name} ({karma.get_user_karma(message.reply_to_message.from_user)}) получил предупреждение.\nСейчас их {database.get_warns_count(message.reply_to_message.from_user)}. Когда их будет 4 - я выдам тебе мут.')
        

@bot.message_handler(chat_types=['supergroup'], commands=['unmute'])
async def unmute_user(message):
    admins = await bot.get_chat_administrators(message.chat.id)
    admins_id = [id.user.id for id in admins]
    if message.from_user.id in admins_id:
        if message.reply_to_message.from_user.id in admins_id:
            await bot.reply_to(message, 'Господа админы, прошу выяснять отношения в личных сообщениях.')
            return
        database.clear_warns(message.reply_to_message.from_user)
        await bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, None,
                                       True, True, True, True)
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
    await bot.reply_to(message, f'Карма пользователя {user.full_name} сейчас составляет {karma.get_user_karma(user)}.\nПовышал другим карму {karma.get_increase_times(user)} раз(а).\nПонижал другим карму {karma.get_decrease_times(user)} раз(а).')


@bot.message_reaction_handler()
async def get_reaction(message_reaction_updated):
    if message.chat.id != config.CHAT_ID:
        return 
    if not message_reaction_updated.new_reaction:
        return
    if message_reaction_updated.new_reaction[0].emoji in globals.KARMA_THANKS_EMOJI:
        temp_message = await bot.send_message(message_reaction_updated.chat.id, 'ы', reply_to_message_id=message_reaction_updated.message_id, message_thread_id=1365)
        await bot.delete_message(temp_message.chat.id, temp_message.id)
        if temp_message.reply_to_message.message_thread_id != globals.THREADS['SHOWCASE_THREAD'] or globals.THREADS['MATERIALS_THREAD']:
            return
        if temp_message.reply_to_message.from_user.id == message_reaction_updated.user.id:
            return
        karma.check_user_in_database(temp_message.reply_to_message.from_user)
        karma.check_user_in_database(message_reaction_updated.user)
        karma.change_user_karma(temp_message.reply_to_message.from_user, message_reaction_updated.user)
        
    if message_reaction_updated.new_reaction[0].emoji in globals.KARMA_CONDEMNATION_EMOJI:
        temp_message = await bot.send_message(message_reaction_updated.chat.id, 'ы', reply_to_message_id=message_reaction_updated.message_id, message_thread_id=1)
        await bot.delete_message(temp_message.chat.id, temp_message.id)
        if temp_message.reply_to_message.message_thread_id != globals.THREADS['SHOWCASE_THREAD'] or globals.THREADS['MATERIALS_THREAD']:
            return
        if temp_message.reply_to_message.from_user.id == message_reaction_updated.user.id:
            return
        karma.check_user_in_database(temp_message.reply_to_message.from_user)
        karma.check_user_in_database(message_reaction_updated.user)
        karma.change_user_karma(temp_message.reply_to_message.from_user, message_reaction_updated.user, -1)
        

@bot.message_handler(chat_types=['supergroup'], func=lambda message: True)
async def listen_to_karma(message):
    # govnokod starts here.
    if message.chat.id != config.CHAT_ID:
        return
    if message.reply_to_message.forum_topic_created:
        return
    if message.text.lower().startswith(globals.KARMA_THANKS):
        if message.reply_to_message.from_user.is_bot:
            await bot.reply_to(message, "У меня отобрали карму... Мне ее нельзя менять.")
            return
        if message.from_user.id == message.reply_to_message.from_user.id:
            await bot.reply_to(message, 'Я понимаю, что ты самовлюбленный дурак, но не нужно этого.')
            return
        karma.check_user_in_database(message.from_user)
        karma.check_user_in_database(message.reply_to_message.from_user)
        karma.change_user_karma(message.reply_to_message.from_user, message.from_user)
        await bot.reply_to(message, f'{message.from_user.first_name} ({karma.get_user_karma(message.from_user)}) повысил карму {message.reply_to_message.from_user.first_name} ({karma.get_user_karma(message.reply_to_message.from_user)}).')
    elif message.text.lower().startswith(globals.KARMA_CONDEMNATION):
        if message.reply_to_message.from_user.is_bot:
            await bot.reply_to(message, "У меня отобрали карму... Мне ее нельзя менять.")
            return
        if message.from_user.id == message.reply_to_message.from_user.id:
            await bot.reply_to(message, 'Я понимаю, что ты самокритичный дурак, но не нужно этого.')
            return
        karma.check_user_in_database(message.from_user)
        karma.check_user_in_database(message.reply_to_message.from_user)
        karma.change_user_karma(message.reply_to_message.from_user, message.from_user, -1)
        await bot.reply_to(message, f'{message.from_user.first_name} ({karma.get_user_karma(message.from_user)}) понизил карму {message.reply_to_message.from_user.first_name} ({karma.get_user_karma(message.reply_to_message.from_user)}).')


if __name__ == '__main__':
    asyncio.run(bot.infinity_polling(allowed_updates=['message_reaction', 'message', 'chat_member']))
    
