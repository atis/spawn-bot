import logging
import telegram
import math
from telegram.error import NetworkError, Unauthorized
from time import sleep
from peewee import *

db = SqliteDatabase('people.db')

class Users(Model):
    userID = BigIntegerField()
    lat = CharField()
    lon = CharField()
    distance= IntegerField()
    enabled= BooleanField()
    class Meta:
        database = db # This model uses the "people.db" database.

db.create_tables([Users])

update_id = None


def main():
    """Run the bot."""
    global update_id
    # Telegram Bot Authorization Token
    bot = telegram.Bot('BOT:TOKEN')

    # get the first pending update_id, this is so we can skip over it in case
    # we get an "Unauthorized" exception.
    try:
        update_id = bot.get_updates()[0].update_id
    except IndexError:
        update_id = None

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    while True:
        try:
            echo(bot)
        except NetworkError:
            sleep(1)
        except Unauthorized:
            update_id += 1
def distance(lat1,lon1, lat2,lon2):
    radius = 6371000 # km

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return d

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def updateDistance(user,distance):
        dbUser = Users.select().where(Users.userID == user).get()
        dbUser.distance=distance
        dbUser.save()

def updateStatus(user,status):
        dbUser = Users.select().where(Users.userID == user).get()
        dbUser.enabled=status
        dbUser.save()        

def updateLocation(user,latitude,longitude):
        dbUser = Users.select().where(Users.userID == user).get()
        dbUser.lat=latitude
        dbUser.lon=longitude
        dbUser.save()

def register(user,latitude,longitude):
        userSave= Users(userID=user, lat=latitude, lon=longitude,distance='1000',enabled=True)
        userSave.save()

def userExist(user):
    count = Users.select().where(Users.userID == user).count()
    if count==0:
        return False
    else:
        return True

def echo(bot):
    """Echo the message the user sent."""
    global update_id
    # Request updates after the last update_id
    for update in bot.get_updates(offset=update_id, timeout=10):
        update_id = update.update_id + 1
        print 'update received'
        print update.message.chat.type
        if ((update.message.location) and update.message.from_user.id != None and (update.message.chat.type=='private')):
            if userExist(update.message.from_user.id)==False:
                print update.message.from_user.id
                register(update.message.from_user.id,update.message.location.latitude,update.message.location.longitude)
            updateLocation(update.message.from_user.id,update.message.location.latitude,update.message.location.longitude)
            bot.send_message(chat_id=update.message.chat_id, text="Lokacija mainita")
        if (update.message.text and update.message.from_user.id != None and (update.message.chat.type=='private')):
            if (RepresentsInt(update.message.text) and update.message.from_user.id != None and (update.message.chat.type=='private')):
                if userExist(update.message.from_user.id)==False:
                    print update.message.from_user.id
                    register(update.message.from_user.id,0,0)
                updateDistance(update.message.from_user.id,update.message.text) 
                bot.send_message(chat_id=update.message.chat_id, text="Distance mainita")

            if (update.message.text.lower()=='enable'):
                if userExist(update.message.from_user.id)==False:
                    print update.message.from_user.id
                    register(update.message.from_user.id,0,0)
                updateStatus(update.message.from_user.id,True) 
                bot.send_message(chat_id=update.message.chat_id, text="Paznojumi ieslegti")

            if (update.message.text.lower()=='disable'):
                if userExist(update.message.from_user.id)==False:
                    print update.message.from_user.id
                    register(update.message.from_user.id,0,0)
                updateStatus(update.message.from_user.id,False) 
                bot.send_message(chat_id=update.message.chat_id, text="Pazinojumi izslegti")

        if ((update.message.location) and (update.message.chat.type=='supergroup' or update.message.chat.type=='group')):
            query = Users.select().where(Users.enabled == True)
            for users in query:
                print 'checkDistance'
                distanceBetween=distance(update.message.location.latitude,update.message.location.longitude,float(users.lat),float(users.lon))
                if distanceBetween<users.distance:
                    bot.send_message(chat_id=users.userID, text="Pokemons "+str(round(distanceBetween,1))+" metru attaluma")



if __name__ == '__main__':
    main()