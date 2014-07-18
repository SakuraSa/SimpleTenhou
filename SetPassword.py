from DAO import *
from service import saltHash
from web.db import sqlwhere

if __name__ == "__main__":
    username = raw_input("username:")
    user = DAOuser.selectFirst(where=sqlwhere({'name': username}))
    if not user:
        print "user not found."
        exit()
    password = raw_input("password:")
    user.update(password=saltHash(password))
    print "ok"
