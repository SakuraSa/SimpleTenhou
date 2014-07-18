#!/usr/bin/env python
#coding=utf-8

import web
import json
import database
import service
import tenhouLog

NONE = object()
def cached(f):
    def wrapper(self, *args, **kwargs):
        cache = self.__dict__.get('__cache__', NONE)
        if cache is NONE:
            cache = self.__dict__['__cache__'] = dict()
        key = "%s%s" % (f.__name__, repr((args, kwargs)))
        value = cache.get(key, NONE)
        if value is NONE:
            value = cache[key] = f(self, *args, **kwargs)
        return value
    return wrapper

class DAO(object):
    """docstring for DAO"""
    PROPERTYNAMES = list()
    PROPERTYS     = dict()
    TABLENAME     = ""
    DATABASE      = database.database
    SEQCOLUMN     = 'id'
    SEQCOLUMNTYPE = int
    CACHE         = dict()

    def __init__(self):
        object.__init__(self)
        object.__setattr__(self, 'PROPERTYS', dict(type(self).PROPERTYS))

    def __str__(self):
        return "%s%s" % (type(self).__name__, repr(self.PROPERTYS))

    def __eq__(self, e):
        return type(e) is type(self) and e.PROPERTYS[e.SEQCOLUMN] == self.PROPERTYS[self.SEQCOLUMN]

    def __getattr__(self, name):
        if name in self.PROPERTYNAMES:
            return self.PROPERTYS.get(name, None)
        else:
            raise AttributeError("%s object has no attribute '%s'" % (type(self), name))
    
    def __setattr__(self, name, value):
        if name in self.PROPERTYNAMES:
            self.PROPERTYS[name] = value
        else:
            raise AttributeError("%s object has no attribute '%s'" % (type(self), name))

    def __sqlDict__(self):
        sqlDict = dict(self.PROPERTYS)
        if self.SEQCOLUMN in sqlDict:
            del sqlDict[self.SEQCOLUMN]
        return sqlDict

    def __sqlWhere__(self):
        return web.db.sqlwhere(
            {self.SEQCOLUMN: self.PROPERTYS[self.SEQCOLUMN]}
        )

    def set(self, **kwargs):
        for key in kwargs:
            if key in self.PROPERTYNAMES:
                self.PROPERTYS[key] = kwargs[key]
        return self

    def insert(self):
        self.CACHE.clear()
        self.DATABASE.insert(self.TABLENAME, **self.__sqlDict__())
        return self

    def update(self, **kwargs):
        self.CACHE.clear()
        if kwargs:
            self.DATABASE.update(self.TABLENAME, 
                where = self.__sqlWhere__(),
                **kwargs)
            return self.set(**kwargs)
        else:
            self.DATABASE.update(self.TABLENAME, 
                where = self.__sqlWhere__(),
                **self.__sqlDict__())
            return self

    def delete(self):
        self.CACHE.clear()
        self.DATABASE.delete(self.TABLENAME,
            where = self.__sqlWhere__())
        return self

    @classmethod
    def select(cls, **kwargs):
        key = cls.TABLENAME + repr(kwargs)
        if key in cls.CACHE:
            return cls.CACHE[key]
        else:
            sqliter = cls.DATABASE.select(cls.TABLENAME, **kwargs)
            value = [cls().set(**row) for row in sqliter]
            cls.CACHE[key] = value
        return value

    @classmethod
    def selectFirst(cls, **kwargs):
        """
        :rtype : DAOlogs
        """
        DAOs = cls.select(**kwargs)
        if DAOs:
            return DAOs[0]
        else:
            return None

    @classmethod
    def selectById(cls, id):
        if not isinstance(id, cls.SEQCOLUMNTYPE):
            try:
                id = cls.SEQCOLUMNTYPE(id)
            except Exception, e:
                return None
        return cls.selectFirst(where = web.db.sqlwhere({
            cls.SEQCOLUMN: id
        }))

    @classmethod
    def deleteAll(cls, **kwargs):
        cls.DATABASE.delete(cls.TABLENAME, **kwargs)

class DAOlogs(DAO):
    """docstring for DAOlogs"""
    PROPERTYNAMES = ['id', 
                     'ref', 
                     'json', 
                     'gameat', 
                     'rulecode', 
                     'lobby', 
                     'createat',
                     'id_game']
    TABLENAME     = "logs"
    def __init__(self):
        DAO.__init__(self)

    @cached
    def getGame(self):
        return DAOgame.selectById(self.id_game)

    def empty(self):
        DAOlogs_name.deleteAll(where=web.db.sqlwhere({'ref': self.ref}))
        return self

    @cached
    def getLogs_name(self):
        return DAOlogs_name.select(where=web.db.sqlwhere({'ref': self.ref}), order="point desc")

    @cached
    def getNames(self):
        return [
            logs_name.name
            for logs_name in self.getLogs_name()
        ]

    @cached
    def getRanksByTeam(self, team):
        lns = self.getLogs_name()
        for i in range(len(lns)):
            if lns[i].name in team.getUserNames():
                return i + 1
        return None

    @cached
    def getRanksByName(self, name):
        lns = self.getLogs_name()
        for i in range(len(lns)):
            if lns[i].name == name:
                return i + 1
        return None

    @cached
    def getLogs_nameByTeam(self, team):
        teamNames = team.getUserNames()
        for ln in self.getLogs_name():
            if ln.name in teamNames:
                return ln
        return None

    @cached
    def getLogs_nameByUserName(self, name):
        for ln in self.getLogs_name():
            if ln.name == name:
                return ln
        return None

    @cached
    def getPointChart(self, game=None, dataZoom=False):
        if game is None:
            game = tenhouLog.game(json.loads(self.json))
        dataNames = [player.name for player in game.players]
        dataLabels = [u'开局'] + [log.name for log in game.logs]
        dataLines = [
            [game.logs[0].startScore[i]] + [log.endScore[i] for log in game.logs]
            for i in range(len(game.players))
        ]
        return service.jsonChart(
            u'得点折线',
            self.ref,
            dataLines,
            dataNames,
            dataLabels,
            dataZoom=dataZoom
        )

    @cached
    def getTenhouGame(self):
        return tenhouLog.game(json.loads(self.json))

    @cached
    def getAspects(self):
        game = self.getTenhouGame()
        return service.get_aspect(game)

    @classmethod
    def has(cls, ref):
        return cls.selectFirst(where=web.db.sqlwhere({'ref': ref}))

class DAOlogs_name(DAO):
    """docstring for DAOlogs_name"""
    PROPERTYNAMES = ['id', 
                     'ref',
                     'name', 
                     'sex', 
                     'rate', 
                     'dan',
                     'score',
                     'point']
    TABLENAME     = "logs_name"
    def __init__(self):
        DAO.__init__(self)

    def getSC(self):
        return service.SC_func(self)

class DAOuser(DAO):
    """docstring for DAOuser"""
    PROPERTYNAMES = ['id', 
                     'name', 
                     'password', 
                     'id_role']
    TABLENAME     = "user"
    def __init__(self):
        DAO.__init__(self)

    @cached
    def getRights(self):
        return service.selectByLinker(
            linkKey = 'id_role', 
            linkValue = self.id_role, 
            linkTarget = 'id_right', 
            linkTable = DAOroleRight.TABLENAME, 
            targetDAO = DAOright
        )

    @cached
    def getRole(self):
        return DAOrole.selectById(self.id_role)

class DAOrole(DAO):
    """docstring for DAOrole"""
    PROPERTYNAMES = ['id', 
                     'name']
    TABLENAME     = "role"
    def __init__(self):
        DAO.__init__(self)

class DAOright(DAO):
    """docstring for DAOright"""
    PROPERTYNAMES = ['id', 
                     'name']
    TABLENAME     = "right"
    def __init__(self):
        DAO.__init__(self)

class DAOroleRight(DAO):
    """docstring for DAOroleRight"""
    PROPERTYNAMES = ['id', 
                     'id_role',
                     'id_right']
    TABLENAME     = "roleRight"
    def __init__(self):
        DAO.__init__(self)

class DAOgame(DAO):
    """docstring for DAOroleRight"""
    PROPERTYNAMES = ['id', 
                     'name',
                     'url',
                     'id_statue',
                     'des']
    TABLENAME     = "game"
    def __init__(self):
        DAO.__init__(self)

    def empty(self):
        for team in self.getTeam():
            team.empty().delete()
        for log in self.getLogs():
            log.empty().delete()
        return self.delete()

    @cached
    def getTeam(self):
        return DAOteam.select(where=web.db.sqlwhere({'id_game': self.id}))

    @cached
    def getSortedTeam(self):
        scGroup = self.getSCsumGroupByTeam()
        teams = self.getTeam()
        teams.sort(lambda a,b :cmp(scGroup[a.id], scGroup[b.id]), reverse=True)
        return teams

    @cached
    def getLogs(self):
        return DAOlogs.select(where=web.db.sqlwhere({'id_game': self.id}), order="gameat desc")

    @cached
    def getLogsByUserName(self, name):
        logs = self.getLogs()
        return [log for log in logs if name in log.getNames()]

    @cached
    def getLogsGourpByTeam(self):
        ret = list()
        logs = self.getLogs()
        for team in self.getTeam():
            ret.append((team, team.getLogs(logs)))
        return ret

    @cached
    def getTeamByUserName(self, name):
        for team in self.getTeam():
            if name in team.getUserNames():
                return team
        return None

    @cached
    def getSCsumGroupByName(self):
        dic = dict()
        for log in self.getLogs():
            for ln in log.getLogs_name():
                dic[ln.name] = dic.get(ln.name, 0) + ln.getSC()
        return dic

    @cached
    def getSCsumGroupByTeam(self):
        dic = self.getSCsumGroupByName()
        ret = dict()
        for team in self.getTeam():
            s = team.getAddonSCSum()
            for name in team.getUserNames():
                s += dic.get(name, 0)
            ret[team.id] = s
        return ret

    @cached
    def getSatistics(self):
        return service.get_statistics(self.getLogs())

    @cached
    def getStatisticsJson(self):
        return json.dumps(self.getSatistics())

    @cached
    def getTeamPointChart(self):
        teamLogs = self.getLogsGourpByTeam()
        names = []
        datas = []
        for team, logs in teamLogs:
            dl = []
            ds = 0
            for log in logs[::-1]:
                ln = log.getLogs_nameByTeam(team)
                ds += ln.getSC()
                dl.append(ds)
            datas.append(dl)
            names.append(service.long_str(team.name))
        max_len = max(len(row) for row in datas)
        labels = [u"第%4d轮" % (i + 1) for i in range(max_len)]

        return service.jsonChart(
            self.name,
            u'得分折线图',
            datas,
            names,
            labels,
            ticks=10,
            dataZoom=len(labels)>8
        )

    @cached
    def getPlayerPointChart(self, title, names, logs):
        isTeam = len(names) > 1
        datas = [[] for i in range(len(names))]
        labels = list()
        cnts = [0] * len(names)
        if isTeam:
            datas.append([])
            names.append(u"团队")
        cnta = 0

        for log in logs[::-1]:
            lns = log.getLogs_name()
            for i in range(len(names)):
                for ln in lns:
                    if ln.name == names[i]:
                        SC = ln.getSC()
                        cnta += SC
                        cnts[i] += SC
                        datas[i].append(cnts[i])
                        if isTeam:
                            datas[-1].append(cnta)
                        break
            labels.append(service.date_str(log.gameat))


        return service.jsonChart(
            title,
            u'得分折线图',
            datas,
            names,
            labels,
            ticks=10
        )

class DAOgameStatue(DAO):
    """docstring for DAOgameStatue"""
    PROPERTYNAMES = ['id', 
                     'name']
    TABLENAME     = "gameStatue"
    def __init__(self):
        DAO.__init__(self)

class DAOteam(DAO):
    """docstring for DAOteam"""
    PROPERTYNAMES = ['id', 
                     'name',
                     'id_game']
    TABLENAME     = "team"
    def __init__(self):
        DAO.__init__(self)

    @cached
    def getAddon(self):
        return DAOteamAddon.select(where=web.db.sqlwhere({'id_team': self.id}))

    @cached
    def getAddonSCSum(self):
        addons = self.getAddon()
        if addons:
            return sum(addon.sc for addon in addons)
        else:
            return 0

    @cached
    def getGame(self):
        return DAOgame.selectById(self.id_game)

    @cached
    def getTeamUser(self):
        return DAOteamUser.select(where=web.db.sqlwhere({'id_team': self.id}))

    @cached
    def getUserNames(self):
        return [teamUser.name for teamUser in self.getTeamUser()]

    @cached
    def getUserNameTags(self):
        return ','.join(self.getUserNames())

    def empty(self):
        DAOteamUser.deleteAll(where=web.db.sqlwhere({'id_team': self.id}))
        return self

    @cached
    def getLogs(self, logs=None):
        if logs is None:
            logs = DAOlogs.select(
                where=web.db.sqlwhere({'id_game': self.id_game}),
                order='gameat desc'
            )
        users = set(self.getUserNames())
        return [
            log for log in logs
            if set(log.getNames()) & users
        ]

    @cached
    def createTeamUser(self, tags):
        for name in tags.split(','):
            DAOteamUser().set(
                id_team=self.id,
                name=name
            ).insert()
        return self

class DAOteamUser(DAO):
    """docstring for DAOteamUser"""
    PROPERTYNAMES = ['id', 
                     'id_team',
                     'name']
    TABLENAME     = "teamUser"

    def __init__(self):
        DAO.__init__(self)

class DAOteamAddon(DAO):
    """docstring for DAOteamAddon"""
    PROPERTYNAMES = ['id',
                     'id_team',
                     'sc',
                     'des']
    TABLENAME     = 'teamAddon'

    def __init__(self):
        DAO.__init__(self)

if __name__ == '__main__':
    log = DAOlogs.selectFirst();
    for i in range(3):
        print log.getNames()

    print log.__cache__