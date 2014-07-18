#!/usr/bin/env python
#coding=utf-8

import web
import service
from DAO import *

web.config.debug = False

class pageManager(object):
    """docstring for pageManager"""
    PageTypes = dict()
    Session = None
    Render = None

    def __init__(self):
        object.__init__(self)

    @classmethod
    def registePage(cls, page):
        if not issubclass(page, pageBase):
            raise TypeError('not Page class registed.')
        if not page.Name in cls.PageTypes:
            cls.PageTypes[page.Name] = page
        return page

    @classmethod
    def createApplication(cls):
        mapping = list()
        fvars = dict()
        for page in cls.PageTypes.values():
            mapping.append(page.Mapping)
            mapping.append(page.Name)
            fvars[page.Name] = page
        return web.application(mapping, fvars)

    @classmethod
    def createSession(cls, application, initializer):
        cls.Session = web.session.Session(application, web.session.DiskStore('sessions'), initializer=initializer)
        return cls.Session

    @classmethod
    def createRender(cls, templatesPath = 'templates', base = 'base'):
        kwargs = dict(
            loc = templatesPath,
            globals  = {'session': cls.Session,
                        'sum': sum, 'max': max, 'min': min,
                        'date_str': service.date_str,
                        'long_str': service.long_str,
                        'long_tag': service.long_tag})
        kwargs['globals']['render'] = web.template.render(**kwargs)
        if not base is None:
            kwargs['base'] = base
        cls.Render = web.template.render(**kwargs)
        return cls.Render

def AuthorizationRights(rights=[]):
    def funcDec(pageFunc):
        def retFunc(*args, **kwargs):
            if any(not r in session.rights for r in rights):
                raise web.Forbidden()
            return pageFunc(*args, **kwargs)
        return retFunc
    return funcDec

def AuthorizationLogin(pageFunc):
    def retFunc(*args, **kwargs):
        if session.user is None:
            raise web.Forbidden()
        return pageFunc(*args, **kwargs)
    return retFunc

class pageBase(object):
    """docstring for pageBase"""
    Name = "base"
    Mapping = "/.*"

    def __init__(self):
        object.__init__(self)


def staticPage(name, mapping, template):
    @pageManager.registePage
    class staticPageTemplate(pageBase):
        """docstring for staticPageTemplate"""
        Name = name
        Mapping = mapping

        def __init__(self):
            pageBase.__init__(self)

        def GET(self):
            return render.__getattr__(template)()
    return staticPageTemplate

@pageManager.registePage
class pageIndex(pageBase):
    """docstring for pageIndex"""
    Name = "index"
    Mapping = "/"

    def __init__(self):
        pageBase.__init__(self)

    def GET(self):
        web.header('X-XSS-Protection', '0', unique=True)
        return render.gameList(DAOgame.select())

@pageManager.registePage
class pageLogin(pageBase):
    """docstring for pageLogin"""
    Name = "login"
    Mapping = "/login"

    def __init__(self):
        pageBase.__init__(self)

    def GET(self):
        return render.login("", "")

    def POST(self):
        username = service.checkStrInput('username')
        password = service.checkStrInput('password')
        user = service.checkLogin(username, password)
        if user:
            pageLogin.login(user)
            raise web.seeother('/')
        else:
            return render.login("has-error", username)

    @staticmethod
    def login(user):
        session.user = user
        session.rights = [right.id for right in user.getRights()]
        session.role = user.getRole()

@pageManager.registePage
class pageLogout(pageBase):
    """docstring for pageLogout"""
    Name = "logout"
    Mapping = "/logout"

    def __init__(self):
        pageBase.__init__(self)

    def GET(self):
        session.kill()
        raise web.seeother('/')

@pageManager.registePage
class pageRegister(pageBase):
    """docstring for pageRegister"""
    Name = "register"
    Mapping = "/register"

    def __init__(self):
        pageBase.__init__(self)

    def GET(self):
        return render.register("", "", "")

    def POST(self):
        username = service.checkStrInput('username')
        password = service.checkStrInput('password')
        passwordcfm = service.checkStrInput('passwordcfm')
        if password != passwordcfm:
            return render.register("has-error", username, u"两次密码输入不一致")
        if DAOuser.select(where=web.db.sqlwhere({"name": username})):
            return render.register("has-error", username, u"用户名已经存在")
        user = service.register(username, password)
        pageLogin.login(user)
        raise web.seeother('/')

@pageManager.registePage
class pageUserList(pageBase):
    """docstring for pageUserList"""
    Name = "userList"
    Mapping = "/userList"

    def __init__(self):
        pageBase.__init__(self)

    @AuthorizationRights([1])
    def GET(self):
        method = web.input().get('method', 'view')
        if method == 'view':
            return self.view()
        elif method == 'delete':
            return self.delete()
        elif method == 'setRole':
            return self.setRole()
        else:
            raise web.notfound()

    def view(self):
        return render.userList(DAOuser.select())

    def delete(self):
        user = service.checkDAOinput('id_user', DAOuser)
        if user.id_role == 1:
            raise web.Forbidden()
        elif 1 in session.rights or (user.id_role == 3 and 2 in session.rights):
            user.delete()
            service.jumpBack()
        else:
            raise web.Forbidden()

    def setRole(self):
        user = service.checkDAOinput('id_user', DAOuser)
        if not self.rightCheck(user):
            raise web.Forbidden()
        role = service.checkDAOinput('id_role', DAOrole)
        user.set(id_role=role.id)
        if not self.rightCheck(user):
            raise web.Forbidden()
        user.update()
        service.jumpBack()

    def rightCheck(self, user):
        if user.id_role == 1:
            return False
        if user.id_role == 2 and session.user.id_role == 2:
            return False
        return True

@pageManager.registePage
class pageGameEdit(pageBase):
    """docstring for pageGameEdit"""
    Name = "gameEdit"
    Mapping = "/gameEdit"

    def __init__(self):
        pageBase.__init__(self)

    @AuthorizationRights([2])
    def GET(self):
        method = service.checkStrInput('method')
        if method == 'create':
            return self.create()
        elif method == 'edit':
            return self.edit()
        elif method == 'delete':
            return self.delete()
        else:
            raise web.notfound()

    def create(self):
        return render.gameEdit(None)

    def delete(self):
        if not_confirm():
            return check_confirm(u"您确认要比赛删除么？")
        service.checkDAOinput('id_game', DAOgame).empty().delete()
        service.jumpHome()

    def edit(self):
        game = service.checkDAOinput('id_game', DAOgame)
        return render.gameEdit(game)

    @AuthorizationRights([2])
    def POST(self):
        if not web.input().get('id', None) is None:
            game = service.checkDAOinput('id', DAOgame)
            game.update(
                name=service.checkStrInput('name'),
                url=service.checkStrInput('url'),
                id_statue=service.checkIntInput('id_statue'),
                des=service.checkStrInput('des')
            )
        else:
            DAOgame().set(
                name=service.checkStrInput('name'),
                url=service.checkStrInput('url'),
                id_statue=service.checkIntInput('id_statue'),
                des=service.checkStrInput('des')
            ).insert()
        raise web.seeother('/')

@pageManager.registePage
class pageTeamEdit(pageBase):
    """docstring for pageTeamEdit"""
    Name = "teamEdit"
    Mapping = "/teamEdit"

    def __init__(self):
        pageBase.__init__(self)

    @AuthorizationRights([2])
    def POST(self):
        method = service.checkStrInput('method')
        if method == 'create':
            return self.create()
        elif method == 'edit':
            return  self.edit()
        elif method == 'delete':
            return  self.delete()
        else:
            raise web.notfound()

    def create(self):
        team = DAOteam().set(
            name = service.checkStrInput('name'),
            id_game = service.checkIntInput('id_game')
        ).insert()
        service.jumpTo('/gameEdit?method=edit&id_game=%d' % team.id_game)

    def edit(self):
        team = service.checkDAOinput('id_team', DAOteam)
        name = service.checkStrInput('name')
        tags = service.checkStrInput('userNameTags')
        team.empty().createTeamUser(tags).update(name=name)
        service.jumpTo('/gameEdit?method=edit&id_game=%d' % team.id_game)

    def delete(self):
        team = service.checkDAOinput('id_team', DAOteam).delete()
        service.jumpTo('/gameEdit?method=edit&id_game=%d' % team.id_game)

@pageManager.registePage
class pageLog(pageBase):
    """docstring for pageLog"""
    Name = "log"
    Mapping = "/log"

    def __init__(self):
        pageBase.__init__(self)

    def GET(self):
        method = web.input().get('method', 'view')
        if method == 'view':
            return self.view()
        elif method == 'delete':
            return self.delete()
        else:
            raise web.notfound()

    @AuthorizationRights([2])
    def POST(self):
        method = service.checkStrInput('method')
        if method == 'upload':
            return self.upload()
        else:
            raise web.notfound()

    def view(self):
        ref = service.checkStrInput('ref')
        log = DAOlogs.selectFirst(where=web.db.sqlwhere({'ref': ref}))
        if log is None:
            raise web.notfound()
        return render.log(log)

    @AuthorizationRights([2])
    def delete(self):
        log = service.checkDAOinput('id_log', DAOlogs)
        log.empty().delete()
        service.jumpTo('/gameEdit?method=edit&id_game=%d#panel_round' % log.id_game)

    def upload(self):
        ref = service.checkStrInput('ref')
        id_game = service.checkIntInput('id_game')
        try:
            service.createLogs(ref, id_game)
        except Exception, e:
            return str(type(e)) + str(e)
        service.jumpTo('/gameEdit?method=edit&id_game=%d#panel_round' % id_game)

@pageManager.registePage
class pageGameView(pageBase):
    """docstring for pageGameView"""
    Name = "gameView"
    Mapping = "/gameView"

    def __init__(self):
        pageBase.__init__(self)

    def GET(self):
        game = service.checkDAOinput('id_game', DAOgame)
        return render.gameView(game)

@pageManager.registePage
class pagePlayerView(pageBase):
    """docstring for pagePlayerView"""
    Name = "playerView"
    Mapping = "/playerView"

    def __init__(self):
        pageBase.__init__(self)

    def GET(self):
        game = service.checkDAOinput('id_game', DAOgame)
        player = service.checkStrInput('name')
        return render.playerView(game, player)

@pageManager.registePage
class pageTeamView(pageBase):
    """docstring for pageTeamView"""
    Name = "teamView"
    Mapping = "/teamView"

    def __init__(self):
        pageBase.__init__(self)

    def GET(self):
        team = service.checkDAOinput('id_team', DAOteam)
        return render.teamView(team)

@pageManager.registePage
class pageAddonEdit(pageBase):
    """docstring for pageAddonEdit"""
    Name = "addonEdit"
    Mapping = "/addonEdit"

    def __init__(self):
        pageBase.__init__(self)

    @AuthorizationRights([2])
    def GET(self):
        method = web.input().get('method', 'edit')
        if method == 'edit':
            return self.edit()
        elif method == 'delete':
            return self.delete()
        else:
            raise web.notfound()

    @AuthorizationRights([2])
    def POST(self):
        method = service.checkStrInput('method')
        if method == 'create':
            return self.create()
        else:
            raise web.notfound()

    def edit(self):
        game = service.checkDAOinput('id_game', DAOgame)
        return render.addonEdit(game)

    def delete(self):
        addon = service.checkDAOinput('id_addon', DAOteamAddon)
        addon.delete()
        service.jumpBack()

    def create(self):
        game = service.checkDAOinput('id_game', DAOgame)
        team = service.checkDAOinput('id_team', DAOteam)
        sc   = service.checkFloatInput('sc')
        des  = service.checkStrInput('des')
        addon = DAOteamAddon().set(
            id_team=team.id,
            sc=sc,
            des=des
        ).insert()
        service.jumpTo("/addonEdit?method=edit&id_game=%d" % game.id)

@pageManager.registePage
class pagePlayerBillboard(pageBase):
    """docstring for pagePlayerBillboard"""
    Name = "playerBillboard"
    Mapping = "/playerBillboard"

    def __init__(self):
        pageBase.__init__(self)

    def GET(self):
        game = service.checkDAOinput('id_game', DAOgame)
        return render.playerBillboard(game)

def not_confirm():
    return web.input().get('confirm', 'no') != 'yes'

def check_confirm(msg):
    path = web.ctx.fullpath
    query = web.ctx.query
    back = web.ctx.env.get('HTTP_REFERER', path)
    if query:
        ok = path + "&confirm=yes"
    else:
        ok = path + "?confirm=yes"
    return render.confirm(msg, ok, back)

#init pageBase
app = pageManager.createApplication()
session = pageManager.createSession(app, {
    'user': None,
    'rights': list(),
    'role': None,
})
render = pageManager.createRender()

if __name__ == '__main__':
    if pageManager.PageTypes:
        print "Pages:"
        for name, page in pageManager.PageTypes.items():
            print "%20s %30s" % (name, page.Mapping)
    else:
        print "No pages was registed to pageManager."