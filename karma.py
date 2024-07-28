import database

import logging
import peewee
import telebot


def get_user_karma(user: telebot.types.User):
    """func to get user's karma

    Args:
        user (telebot.types.User): user.

    Returns:
        int | None: int if there's no errors, none if exception is raised.
    """
    check_user_in_database(user)
    try:
        _user = database.User.select().where(database.User.id == str(user.id)).get()
        return _user.karma
    except Exception as exception:
        logging.error(exception)
        return None
    
        
def check_user_in_database(user: telebot.types.User):
    """check if user in database. if not - add him.

    Args:
        user (telebot.types.User): user.
    """
    try:
        database.User.select().where(database.User.id == str(user.id)).get()
    except peewee.DoesNotExist:
        add_new_user_to_database(user)


def add_new_user_to_database(user: telebot.types.User):
    """func to add new user to database.

    args:
        user (telebot.types.User): the user. that's all.
    """
    for _user in database.User.select():
        if _user.id == str(user.id):
            logging.warning(f"User with id={_user.id} already exists!")
            return
        
    database.User.create(id=str(user.id),
                         name=str(user.first_name),
                         karma=0,
                         warns=0,
                         state=0,
                        )
    logging.info(f"Added new user: {user.full_name} with id={user.id}).")


def change_user_karma(user: telebot.types.User, amount: int = 1):
    """func to change user's karma.

    args:
        user (telebot.types.User): user.
        amount (int, optional): amount of karma to change. defaults to 1.
    """
    _user = database.User.select().where(database.User.id == user.id).get()
    _user.karma += amount
    
    try:
        _user.save()
        logging.info(f"Changed karma for user: {user.full_name}, now karma = {_user.karma}")
    except Exception as exception:
        logging.error(exception)
        
