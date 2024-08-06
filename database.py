import karma

import logging
import peewee
import telebot


db = peewee.SqliteDatabase('users.db')


class User(peewee.Model):
    id = peewee.CharField()
    name = peewee.CharField()
    username = peewee.CharField()
    karma = peewee.IntegerField()
    warns = peewee.IntegerField()
    state = peewee.IntegerField()
    increase_karma = peewee.IntegerField()
    decrease_karma = peewee.IntegerField()
    class Meta:
        database = db
        

def get_warns_count(user: telebot.types.User):
    karma.check_user_in_database(user)
    _user = User.select().where(User.id == str(user.id)).get()
    return _user.warns


def give_warn(user: telebot.types.User):
    karma.check_user_in_database(user)
    _user = User.select().where(User.id == str(user.id)).get()
    _user.warns += 1
    try:
        _user.save()
        logging.info(f'User {user.full_name} ({user.username}) got warn (now {get_warns_count(user)})!')
    except Exception as exception:
        logging.error(exception)
        return 'err'
    else:
        if get_warns_count(_user) > 3:
            return 'muted'
    
    
def clear_warns(user: telebot.types.User):
    karma.check_user_in_database(user)
    _user = User.select().where(User.id == str(user.id)).get()
    _user.warns = 0
    try:
        _user.save()
        logging.info(f'User {user.full_name} ({user.username}) forgiven.')
    except Exception as exception:
        logging.error(exception)
    
    
if __name__ == '__main__':
    db.connect()
    db.create_tables([User, ])
    