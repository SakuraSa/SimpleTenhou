#!/usr/bin/env python
#coding=utf-8

import re
import web
import math
import json
import hashlib
import datetime
import requests
import itertools
from DAO import *

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

def selectByLinker(linkKey, linkValue, linkTarget, linkTable, targetDAO):
    #Warning: may not be compatible with other database formats
    #         compatible with: SQLite
    query = r"""
    select * from %s
    where %s in (
        select %s from %s
        where %s = $%s)
    """ % (targetDAO.TABLENAME, targetDAO.SEQCOLUMN, linkTarget, linkTable, linkKey, linkKey)
    sqliter = DAO.DATABASE.query(query, vars={linkKey: linkValue})
    return [targetDAO().set(**row) for row in sqliter]

def checkLogin(name, password, needHash = True):
    if needHash:
        password = saltHash(password)
    return DAOuser.selectFirst(
        where=web.db.sqlwhere({
            'name': name,
            'password': password
    }))

def register(name, password, needHash = True):
    if needHash:
        password = saltHash(password)
    DAOuser().set(
        name=name,
        password=password,
        id_role=3
    ).insert()
    return checkLogin(name, password, needHash = False)

def checkStrInput(key):
    value = web.input().get(key, None)
    if value is None:
        raise web.notfound("param '%s' is not found." % key)
    return value

def checkIntInput(key):
    value = checkStrInput(key)
    try:
        return int(value)
    except Exception, e:
        raise web.notfound("param %s = '%s' can not convert to int" % (key, value))

def checkFloatInput(key):
    value = checkStrInput(key)
    try:
        return float(value)
    except Exception, e:
        raise web.notfound("param %s = '%s' can not convert to float" % (key, value))

def checkDatetimeInput(key, format=r"%Y-%m-%d %H:%M:%S"):
    value = checkStrInput(key)
    try:
        return datetime.datetime.strptime(value, format)
    except Exception, e:
        raise web.notfound("param %s = '%s' can not convert to datetime" % (key, value))

def checkDAOinput(key, DAOtarget):
    id = checkStrInput(key)
    DAO = DAOtarget.selectById(id)
    if DAO is None:
        raise web.notfound("can not find %s that %s = %s", (DAOtarget.__name__, DAOtarget.SEQCOLUMN, id))
    return DAO

def jumpBack():
    referer = web.ctx.env.get('HTTP_REFERER', '/')
    raise web.seeother(referer)

def jumpHome():
    raise web.seeother('/')

def jumpTo(baseUrl):
    nav = web.input().get('jumpTo', '')
    raise web.seeother(baseUrl + nav)

def saltHash(text, salt='rnd495'):
    return hashlib.sha256(text + salt).hexdigest()

ref_regex = re.compile(r"(\d{10}gm-\w{4}-\d{4,5}-\w{8})")

def get_info_from_ref(ref):
    arr = ref.split('-')
    date = datetime.datetime.strptime(arr[0][:-2], "%Y%m%d%H")
    ruleCode = arr[1]
    lobby = arr[2]
    return dict(date     = date,
                ruleCode = ruleCode,
                lobby    = lobby)

def downloadLog(url, baseUrl = None):
    ref = ref_regex.findall(url)
    if not ref:
        raise Exception("Unexpected URL: %s" % url)
    if not baseUrl:
        reqUrl = r"http://tenhou.net/5/mjlog2json.cgi?" + ref[0]
    else:
        reqUrl = baseUrl + ref[0]
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "zh-CN,zh;q=0.8",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "If-Modified-Since": "Thu, 01 Jun 1970 00:00:00 GMT",
        "Host": "tenhou.net",
        "Referer": reqUrl,
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36",
    }
    req = requests.get(reqUrl, headers = headers)
    if req.status_code != 200:
        raise Exception("Can not connect with %s" % reqUrl)
    if req.text.strip() == "INVALID PATH":
        raise Exception("Return Unexpected text: %s" % req.text.strip())
    try:
        obj = req.json()
    except Exception, e:
        raise Exception("unexcepted returns [%s]" % req.text)

    while(not obj["name"][-1]):
        obj["name"].pop()
    if len(obj["name"]) != 4:
        raise Exception("Not 4 Player Game, skipped.")
    if not "sc" in obj:
        raise Exception("Game was stopped by host, skipped.")
    return obj, req.text

def createLog(ref, id_game):
    ref = ref_regex.findall(ref)
    if not ref:
        raise Exception("Unexpected URL: %s" % ref)
    else:
        ref = ref[0]
    #checkRoom(ref, id_game)
    log = DAOlogs.has(ref)
    if log:
        return log
    obj, text = downloadLog(ref)
    info = get_info_from_ref(ref)
    log = DAOlogs().set(
        ref=obj['ref'],
        json=text,
        gameat=info['date'],
        rulecode=info['ruleCode'],
        lobby=info['lobby'],
        createat=datetime.datetime.now(),
        id_game=id_game
    ).insert()
    for i in range(len(obj['name'])):
        DAOlogs_name().set(
            ref=ref,
            name=obj['name'][i],
            sex=obj['sx'][i],
            rate=obj['rate'][i],
            dan=obj['dan'][i],
            score=obj['sc'][i * 2],
            point=obj['sc'][i * 2 + 1]
        ).insert()
    return log

def createLogs(refs, id_game):
    return [createLog(ref, id_game) for ref in ref_regex.findall(refs)]

room_regex = re.compile(r'\d+')
def checkRoom(ref, id_game):
    game = DAOgame.selectById(id_game)
    lobby = room_regex.findall(game.url)[-1]
    info = get_info_from_ref(ref)
    if not info['lobby'] == lobby:
        raise Exception("Unexpected lobby %s found, while looking for %s" % (info['lobby'], lobby))

def jsonChart(title, subtitle, dataLines, dataNames, dataLabels, ticks=5000, dataZoom=False):
    maxV, minV = 0, 25000
    for line in dataLines:
        for dt in line:
            maxV = max(dt, maxV)
            minV = min(dt, minV)
    option = dict(
        title=dict(
            text=long_str(title, 30),
            subtext=long_str(subtitle, 40)
        ),
        tooltip=dict(trigger='axis'),
        legend=dict(data=dataNames),
        toolbox=dict(
            show=True,
            feature=dict(
                dataView=dict(show=True, readOnly=True),
                saveAsImage=dict(show=True),
                dataZoom=dict(show=dataZoom)
            ),
        ),
        calculable=False,
        yAxis=[
            dict(
                type='value',
                splitArea=dict(show=True),
                max=maxV,
                min=minV
            )
        ],
        xAxis=[
            dict(
                type='category',
                boundaryGap=False,
                data=dataLabels
            )
        ],
        series=[
            dict(
                name=dataNames[i],
                type='line',
                data=dataLines[i]
            )
            for i in range(len(dataNames))
        ],
        dataZoom=dict(show=dataZoom)
    )
    return json.dumps(option)

def jsonPie(title, subtitle, datas, dataNames):
    option = {
        'title' : {
            'text': title,
            'subtext': subtitle,
            'x': 'center'
        },
        'tooltip': {
            'trigger': 'item',
            'formatter': "{a} <br/>{b} : {c} ({d}%)"
        },
        'legend': {
            'orient': 'vertical',
            'x': 'left',
            'data': dataNames
        },
        'toolbox': {
            'show': True,
            'feature': {
                'dataView': {'show': True, 'readOnly': False},
                'saveAsImage': {'show': True}
            }
        },
        'calculable' : False,
        'series' : [
            {
                'name': '得分分布',
                'type': 'pie',
                'radius': [30, 110],
                'center': ['50%', 200],
                'roseType': 'radius',
                'data':[
                    {'value': d, 'name': n}
                    for d, n in zip(datas, dataNames)
                ]
            }
        ]
    }
    return json.dumps(option)

def date_str(date):
    now = datetime.datetime.now()
    if date > now:
        tsp = date - now
    else:
        tsp = now - date
    sb = list()
    if tsp.days:
        days = tsp.days
        if days >= 365:
            sb.append(u"%d 年" % (days / 365))
        elif days >= 30:
            sb.append(u"%d 月" % (days / 30))
        elif days >= 7:
            sb.append(u"%d 周" % (days / 7))
        else:
            sb.append(u"%d 天" % days)
    elif tsp.seconds:
        seconds = tsp.seconds
        if seconds >= 3600:
            sb.append(u"%d 小时" % (seconds / 3600))
        elif seconds >= 60:
            sb.append(u"%d 分" % (seconds / 60))
        else:
            sb.append(u"%d 秒" % seconds)
    else:
        sb.append(u"刚刚")
    if tsp.seconds > 0:
        sb.append(u"前")
    elif tsp.seconds < 0:
        sb.append(u"后")
    return u"".join(sb)

def long_str(text, maxLength=12):
    if len(text) > maxLength:
        return text[0:maxLength] + '...'
    return text

def long_tag(text, maxLength=12):
    tag = long_str(text, maxLength)
    if tag == text:
        return web.htmlquote(text)
    else:
        return u'<abbr title="%s">%s</abbr>' % (web.htmlquote(text), web.htmlquote(tag))

def SC_func(row):
    return row.point / 10.0 + 20

def get_aspect(game):
    ret = []

    #高得点
    for pl in game.players:
        if pl.score >= 60000:
            ret.append(Aspect(
                2.5 + (pl.score - 60000) / 10000.0,
                pl.name,
                u"暴君",
                u"最终得点大于6w"
            ))
            break

    #无铳
    loser = set()
    for log in game.logs:
        if not log.isDraw:
            for pli in log.loserIndex:
                loser.add(pli)
    for pl in game.players:
        if not pl.index in loser:
            ret.append(Aspect(
                1,
                pl.name,
                u"铁壁",
                u"没有放铳"
            ))

    #5和了
    winner = list()
    for log in game.logs:
        if not log.isDraw:
            for pli in log.winnerIndex:
                winner.append(pli)
    for pl in game.players:
        cnt = winner.count(pl.index)
        if cnt >= 5:
            ret.append(Aspect(
                2 + cnt / 5.0,
                pl.name,
                u"火力压制",
                u"和了5次以上"
            ))


    for pl in game.players:
        if pl.rank == 1:
            winner = pl
            break
    #大逆转
    if game.logs[-1].startScore[winner.index] == min(game.logs[-1].startScore):
        ret.append(Aspect(
            3.5,
            winner.name,
            u"大逆转",
            u"All Last 以4位身份逆1"
        ))
    #坐收渔利
    if game.logs[-1].startScore[winner.index] != max(game.logs[-1].startScore):
        if not game.logs[-1].isDraw and not winner.index in game.logs[-1].winnerIndex:
            ret.append(Aspect(
                4.5,
                winner.name,
                u"坐收渔利",
                u"All Last 因为其他玩家自摸或荣和，上升为一位"
            ))
    #绝对王者
    if all(log.endScore[winner.index] == max(log.endScore) for log in game.logs):
        ret.append(Aspect(
            4.5,
            winner.name,
            u"王者",
            u"保持1位不变"
        ))

    dead_pl_list = [pl for pl in game.players if pl.score < 0]
    last_log = game.logs[-1]
    if (not last_log.isDraw) and len(dead_pl_list) > 1:
        winner = game.players[last_log.winnerIndex[0]]
        ret.append(Aspect(
            3.5 + (len(dead_pl_list) - 2) * 3,
            winner.name,
            u"大杀四方",
            u"%s 一局内击飞2或3名玩家" % last_log.name
        ))

    #双龙竞合
    pl1 = pl2 = None
    for pl in game.players:
        if pl.rank == 1:
            pl1 = pl
        elif pl.rank == 2:
            pl2 = pl
    if pl1.score == pl2.score:
        ret.append(Aspect(
            3.7,
            pl1.name,
            u"双龙竞合",
            u"同分1位"
        ))

    #连庄
    for host_list in itertools.groupby(game.logs, lambda log: log.gameWindIndex):
        log_list = list(host_list[1])
        host_len = len(log_list) - 1
        pl = game.players[log_list[0].gameWindIndex % 4]
        if host_len >= 8:
            ret.append(Aspect(
                5.0 + (host_len - 8) / 1.0,
                pl.name,
                u"风神",
                u"%s 8连庄或以上" % log_list[-1].name
            ))
        elif host_len >= 5:
            ret.append(Aspect(
                3.5 + (host_len - 5) / 3.0,
                pl.name,
                u"永远の风",
                u"%s 5连庄或以上" % log_list[-1].name
            ))

    for lg in game.logs:
        #双响和了
        if len(lg.winnerIndex) > 1:
            for pid in lg.winnerIndex:
                ret.append(Aspect(
                    1.3,
                    game.players[pid].name,
                    u"英雄同见",
                    u"%s 双响和了" % lg.name
                ))
        #特殊役
        yns = lg.yakuNames
        for idx in range(len(yns)):
            row = yns[idx]
            pid = lg.winnerIndex[idx]

            #立直一発自摸
            if u"立直" in row and u"一発" in row and u"門前清自摸和" in row:
                ret.append(Aspect(
                    2.1,
                    game.players[pid].name,
                    u"未来视",
                    u"%s 立直一発自摸和了" % lg.name
                ))

            #岭上
            if u"嶺上開花" in row:
                ret.append(Aspect(
                    3,
                    game.players[pid],
                    u"岭上清风",
                    u"%s 岭上和了" % lg.name
                ))

            #槍槓
            if u"槍槓" in row:
                ret.append(Aspect(
                    3.2,
                    game.players[pid].name,
                    u"岭上击破",
                    u"%s 抢杠和了" % lg.name
                ))

            #海底摸月
            if u"海底摸月" in row:
                ret.append(Aspect(
                    3,
                    game.players[pid].name,
                    u"海底明月",
                    u"%s 海底摸月和了" % lg.name
                ))

            #河底撈魚
            if u"河底撈魚" in row:
                ret.append(Aspect(
                    2.2,
                    game.players[pid].name,
                    u"渔者",
                    u"%s 河底撈魚和了" % lg.name
                ))

            #里宝4
            if lg.dora_inner[idx] >= 4:
                ret.append(Aspect(
                    2 + lg.dora_inner[idx] / 4.0,
                    game.players[pid].name,
                    u"龙宝眷顾",
                    u"%s 4里宝以上和了" % lg.name
                ))

            #役满
            if lg.fan[idx] >= 13:
                ret.append(Aspect(
                    5,
                    game.players[pid].name,
                    u"十三杰",
                    u"%s 役满和了" % lg.name
                ))
    for aspect in ret:
        aspect.ref = game.ref
    ret.sort(lambda a, b: int(a.weight - b.weight), reverse=True)
    return ret


class Aspect:
    def __init__(self, weight, name, title, des, ref=None):
        self.weight = weight
        self.name = name
        self.title = title
        self.des = des
        self.ref = ref

    def get_dict(self):
        return dict(
            weight=self.weight,
            name=self.name,
            title=self.title,
            des=self.des,
            ref=self.ref
        )

def get_statistics(log_list):
    game_list = [tenhouLog.game(json.loads(log.json)) for log in log_list]
    player_list = set()
    aspect_list = list()
    for game in game_list:
        aspect_list.extend(get_aspect(game))
        for pl in game.players:
            player_list.add(pl.name)
    player_list = list(player_list)
    pl_st_dic = {
        player: get_statistics_by_name(player, game_list)
        for player in player_list
    }
    for player in player_list:
        pl_st_dic[player]["aspect_cnt"] = 0
    aspect_group = dict()
    for aspect in aspect_list:
        if aspect.name in aspect_group:
            aspect_group[aspect.name].append(aspect.get_dict())
        else:
            aspect_group[aspect.name] = [aspect.get_dict()]
    for player in aspect_group:
        pl_st_dic[player]["aspect_list"] = aspect_group[player]
        pl_st_dic[player]["aspect_cnt"] = sum(asp['weight'] for asp in aspect_group[player])

    return pl_st_dic

def get_statistics_by_name(player, game_list):
    count = 0
    rank_cnt = 0
    score_cnt = 0
    sc_cnt = 0
    winner_cnt = 0
    winner_score_cnt = 0
    loser_cnt = 0
    loser_score_cnt = 0
    for game in game_list:
        index = game.getPlayerIndex_ByName(player)
        if index < 0:
            continue
        count += 1
        pl = game.players[index]
        rank_cnt += pl.rank
        score_cnt += pl.score
        sc_cnt += SC_func(pl)
        for log in game.logs:
            if index in log.winnerIndex:
                winner_cnt += 1
                winner_score_cnt += log.endScore[index] - log.startScore[index]
            elif index in log.loserIndex:
                loser_cnt += 1
                loser_score_cnt += log.endScore[index] - log.startScore[index]
        if count <= 0:
            count = 1
    return dict(
        count=count,
        rank_cnt=rank_cnt,
        rank_avg=rank_cnt / float(count),
        score_cnt=score_cnt,
        score_avg=score_cnt / float(count),
        sc_cnt=sc_cnt,
        sc_avg=sc_cnt / float(count),
        winner_cnt=winner_cnt,
        winner_avg=winner_cnt / float(count),
        winner_score_cnt=winner_score_cnt,
        winner_score_avg=winner_score_cnt / float(count),
        loser_cnt=loser_cnt,
        loser_avg=loser_cnt / float(count),
        loser_score_cnt=loser_score_cnt,
        loser_score_avg=loser_score_cnt / float(count),
    )


if __name__ == '__main__':
    pass