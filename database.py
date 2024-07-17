import peewee


db = peewee.SqliteDatabase('users.db')


class User(peewee.Model):
    id = peewee.CharField()
    name = peewee.CharField()
    username = peewee.CharField()
    karma = peewee.IntegerField()
    admin = peewee.BooleanField()
    warns = peewee.IntegerField()
    state = peewee.IntegerField()
    
    class Meta:
        database = db
        
        
if __name__ == '__main__':
    db.connect()
    db.create_tables([User, ])
    