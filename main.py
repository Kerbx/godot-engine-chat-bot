import config
import database
import globals
import karma

import asyncio
import datetime
import logging
import re
import requests
import json
import telebot.async_telebot


logging.basicConfig(level=logging.INFO, filename="epta_logi.log",filemode="a",
                    format="%(asctime)s %(levelname)s %(message)s", encoding='utf-8')

bot = telebot.async_telebot.AsyncTeleBot(config.BOT_TOKEN)


async def send_llm_request_to_godochka(text: str):
    return requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
      "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
    },
    data=json.dumps({
      "model": "google/gemma-2-9b-it",
      "messages": [
        {"role": "system", "content": f"Ты очень полезный бот в чате, посвященному игровому движку Godot. Тебя создал Егор Лукич, ты милый технарь, любишь помогать и болтать на разные темы. Ты милфа 30-ти лет, самый настоящий технарь, который не прочь покопаться в различных движках и быть по локти в масле."},
        {"role": "user", "content": f"{text}"},
      ],
      "top_p": 0.75,
      "temperature": 0.7,
      "frequency_penalty": 1.1,
      "presence_penalty": 1.1,
      "repetition_penalty": 1,
      "top_k": 0,
    })
  )
    
    
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
    await bot.send_message(message.chat.id, 'Привет, я Годочка, работаю пока что только в группе, личку не люблю...')
    

@bot.message_handler(chat_types=['supergroup',], commands=['help'])
async def help_message(message):
    await bot.reply_to(message, f'В данном чате присутствует возможность повысить другим <b>карму</b>.\nДля этого необходимо ответить на сообщение человека, а в <u>начале</u> написать: <blockquote>+, спасибо, благодарю, спс и т.п.</blockquote>\n\nТакже я умею реагировать на ваши реакции, с помощью которых можно изменять карму другим. Работает это <b>только</b> в топиках <u>Showcase</u> и <u>Полезные материалы</u>.\nПовысить карму можно с помощью 👍, ❤, 🔥.\nПонизить карму можно с помощью 👎, 💩, 🤡.\n\nКоманды для всех:\n<blockquote>/stats - посмотреть свою статистику или другого человека, ответив на его сообщение.\n/top - вывести ТОП пользователей по карме.\n/antitop - вывести АНТИТОП пользователей по карме.\n/help - спросить у меня, что я умею.</blockquote>\n\nКоманды для админов:\n<blockquote>/warn - выдать предупреждение нарушителю. На четвертое предупреждение я автоматически поставлю мут.\n/mute [days=int|None]- замутить персонажа.\n/unmute - помиловать нарушителя.\n/ban - просто бан.</blockquote>', parse_mode='HTML')


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


@bot.message_handler(chat_types=['supergroup'], commands=['top'])
async def get_top_users(message):
    top_users = karma.get_top_users('desc')
    top_users_list = ''
    i = 1
    for user in top_users:
        top_users_list += f"\n{i}. <a href='tg://user?id={user.id}'>{user.name}</a>: +{user.karma}"
        i += 1
    await bot.reply_to(message, f'🔥Вот ТОП пользоваталей по карме🔥\n{top_users_list}', parse_mode='HTML', disable_notification=True)
    
    
@bot.message_handler(chat_types=['supergroup'], commands=['antitop'])
async def get_antitop_users(message):
    antitop_users = karma.get_top_users('asc')
    antitop_users_list = ''
    i = 1
    for user in antitop_users:
        antitop_users_list += f"\n{i}<a href='tg://user?id={user.id}'>{user.name}</a>: +{user.karma}"
        i += 1
    await bot.reply_to(message, f'👎Вот АНТИТОП пользоваталей по карме👎\n{antitop_users_list}', parse_mode='HTML', disable_notification=True)
    
    
@bot.message_reaction_handler()
async def get_reaction(message_reaction_updated):
    if message_reaction_updated.chat.id != config.CHAT_ID:
        return 
    if not message_reaction_updated.new_reaction:
        return
    if message_reaction_updated.new_reaction[0].emoji in globals.KARMA_THANKS_EMOJI:
        if not database.check_thread(message_reaction_updated.message_id):
            print(message_reaction_updated.message_id)
            return
        if database.check_thread(message_reaction_updated.message_id) != globals.THREADS['SHOWCASE_THREAD'] and database.check_thread(message_reaction_updated.message_id) != globals.THREADS['MATERIALS_THREAD']:
            return
        if database.check_user(message_reaction_updated.message_id) == message_reaction_updated.user.id:
            return
        _user = await bot.get_chat_member(message_reaction_updated.chat.id,
                                        database.check_user(message_reaction_updated.message_id))
        karma.check_user_in_database(_user.user)
        karma.check_user_in_database(message_reaction_updated.user)
        karma.change_user_karma(_user.user, message_reaction_updated.user)
    if message_reaction_updated.new_reaction[0].emoji in globals.KARMA_CONDEMNATION_EMOJI:
        if not database.check_thread(message_reaction_updated.message_id):
            return
        if database.check_thread(message_reaction_updated.message_id) != globals.THREADS['SHOWCASE_THREAD'] and globals.THREADS['MATERIALS_THREAD']:
            return
        if database.check_user(message_reaction_updated.message_id) == message_reaction_updated.user.id:
            return
        karma.check_user_in_database(await bot.get_chat_member(message_reaction_updated.chat.id,
                                                               database.check_user(message_reaction_updated.message_id)))
        karma.check_user_in_database(message_reaction_updated.user)
        karma.change_user_karma(await bot.get_chat_member(message_reaction_updated.chat.id,
                                                        database.check_user(message_reaction_updated.message_id)),
                                message_reaction_updated.user, -1)


@bot.message_handler(content_types=['text', 'video', 'photo', 'document', 'audio'], func=lambda message: True)
async def listen_to_karma(message):
    if message.chat.id != config.CHAT_ID:
        return
    database.write_message_id(int(message.message_id), int(message.message_thread_id), int(message.from_user.id))
    if message.text.lower().startswith('годочка'):
        response = await send_llm_request_to_godochka(message.text)
        response = dict(response.json())["choices"][0]["message"]["content"]
        await bot.reply_to(message, f'{response}', parse_mode="MarkdownV2")

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
            await bot.reply_to(message, "У ботов не может быть кармы. Было бы глупо.")
            return
        if message.from_user.id == message.reply_to_message.from_user.id:
            await bot.reply_to(message, 'Я понимаю, что ты самокритичный дурак, но не нужно этого.')
            return
        karma.check_user_in_database(message.from_user)
        karma.check_user_in_database(message.reply_to_message.from_user)
        karma.change_user_karma(message.reply_to_message.from_user, message.from_user, -1)
        await bot.reply_to(message, f'{message.from_user.first_name} ({karma.get_user_karma(message.from_user)}) понизил карму {message.reply_to_message.from_user.first_name} ({karma.get_user_karma(message.reply_to_message.from_user)}).')
    
    
if __name__ == '__main__':
    asyncio.run(bot.infinity_polling(allowed_updates=['message_reaction', 'message', 'chat_member', 'edited_message', 'channel_post',]))
    
