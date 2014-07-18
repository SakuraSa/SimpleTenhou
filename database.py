#!/usr/bin/env python
#coding=utf-8

import web
import hashlib

databaseInitFile = "init.sql"
databaseInitFileData = "initData.sql"
databaseName = "tenhou.db"

database = web.database(dbn='sqlite', db=databaseName)

def excuteFile(filePath):
    with open(filePath, 'r') as sqlFile:
        for cmd in sqlFile.read().split(";"):
            database.query(cmd)

def initDatabase():
    excuteFile(databaseInitFile)
    excuteFile(databaseInitFileData)

if __name__ == '__main__':
    initDatabase()
