#!/usr/bin/env python
#coding=utf-8

import os
import database
from pages import app

def main():
    if not os.path.exists(database.databaseName):
        print "No database found, initializing..."
        print "-" * 32
        database.initDatabase()
        print "Database initialized."
        print "-" * 32

    app.run()

if __name__ == '__main__':
    main()
