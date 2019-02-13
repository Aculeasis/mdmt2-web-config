import hashlib
import json
import os
import threading
from functools import lru_cache

import bottle
# noinspection PyUnresolvedReferences
from wiki_parser import get_descriptions_from_wiki

import logger

NAME = 'web-config'
API = 665

WIKI_JSON = 'web_config_wiki'
SETTINGS = 'web_config_config'


class Main(threading.Thread):
    def __init__(self, cfg, log, owner):
        super().__init__()
        self.cfg = cfg
        self.log = log
        self.own = owner
        self._ini_ver = self.cfg.gt('system', 'ini_version', 0)

        self.disable = False
        self._server = None
        try:
            self._tpl = Templates(self.cfg, self._get_descriptions())
        except RuntimeError as e:
            self.log(e, logger.ERROR)
            self.disable = True
            return
        self._settings = self._get_settings()

    def _get_descriptions(self) -> dict:
        dsc = self.cfg.load_dict(WIKI_JSON)
        if not dsc or not isinstance(dsc, list) or len(dsc) != 2 or not isinstance(dsc[0], int) \
                or not isinstance(dsc[1], dict):
            self.log('Initial generate {}.json from wiki...'.format(WIKI_JSON), logger.INFO)
            dsc = self._init_descriptions()
        if dsc[0] < self._ini_ver:
            self.log('{}.json is outdated ({} < {}), update...'.format(WIKI_JSON, dsc[0], self._ini_ver), logger.INFO)
            dsc = self._init_descriptions()
        return dsc[1]

    def _init_descriptions(self) -> list:
        dsc = [self._ini_ver, get_descriptions_from_wiki()]
        self.cfg.save_dict(WIKI_JSON, dsc, True)
        self.log('SUCCESS!', logger.INFO)
        return dsc

    def _get_settings(self) -> dict:
        def_cfg = {'ip': '0.0.0.0', 'port': 8989, 'quiet': True, 'username': '', 'secure': []}
        cfg = self.cfg.load_dict(SETTINGS)
        if isinstance(cfg, dict):
            is_ok = True
            for key, val in def_cfg.items():
                if key not in cfg or not isinstance(cfg[key], type(val)):
                    is_ok = False
                    break
            if is_ok:
                return cfg
        self.cfg.save_dict(SETTINGS, def_cfg, True)
        return def_cfg

    def start(self):
        self._server = MyApp(self._settings['ip'], self._settings['port'], self._settings['quiet'])
        self._server.route('/', callback=self._do_get)
        self._server.route('/', 'POST', self._do_post)
        super().start()

    def join(self, timeout=None):
        if self._server:
            self._server.stop()
        super().join(timeout)

    def run(self):
        self.log('Web config start listen {}:{}'.format(self._server.ip, self._server.port))
        self.log('Web config available in http://{}:{}/'.format(self.cfg.gts('ip'), self._server.port), logger.INFO)
        self._server.run()

    def _configure_auth(self, user, password):
        self._settings['username'] = user
        if password:
            salt = hasher(os.urandom(64))
            hash_ = hasher(password + salt)
            self._settings['secure'] = [salt, hash_]
        else:
            self._settings['secure'] = []
        self.cfg.save_dict(SETTINGS, self._settings, True)

    def _auth_basic(self):
        if self._settings['username'] and not self._settings['secure']:
            # password authentication disabled
            return

        user, password = bottle.request.auth or (None, '')
        if not self._settings['username'] and user:
            # First start
            self._configure_auth(user, password)
            msg = 'Setup is complete. Do not forget:\nusername: {}\npassword: {}'.format(user, password)
            raise bottle.HTTPError(200, msg)
        if not user or not (user == self._settings['username'] and check_password(self._settings['secure'], password)):
            raise bottle.HTTPError(401, 'Access denied', **{'WWW-Authenticate': 'Basic realm="private"'})

    def _do_get(self):
        self._auth_basic()
        return self._tpl.cfg()

    def _do_post(self):
        self._auth_basic()
        result = {}
        for key, val in dict(bottle.request.forms.decode('utf-8')).items():
            # 'section$key': value
            key = key.split('$', 1)
            if len(key) == 2 and key[0]:
                if key[0] not in result:
                    result[key[0]] = {}
                result[key[0]][key[1]] = val
        return self._tpl.result(self.own.settings_from_srv(result))


def check_password(secure: list, password: str) -> bool:
    if not password:
        return False
    if not isinstance(secure, list) or len(secure) != 2 or not (secure[0] and secure[1]):
        return False
    salt, hash_ = secure
    return hash_ == hasher(password + salt)


def hasher(data) -> str:
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha512(data).hexdigest()


class MyApp(bottle.Bottle):
    def __init__(self, ip, port, quiet):
        super().__init__()
        self.ip, self.port, self.quiet = ip, port, quiet
        self._server = None

    def stop(self):
        if self._server:
            self._server.stop()

    def run(self):
        self._server = MyWSGIRefServer(host=self.ip, port=self.port, quiet=self.quiet)
        super().run(server=self._server)


class MyWSGIRefServer(bottle.ServerAdapter):
    server = None

    def run(self, handler):
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        quiet = self.options.pop('quiet', None)
        if quiet is not None:
            self.quiet = quiet
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass

            self.options['handler_class'] = QuietHandler
        self.server = make_server(self.host, self.port, handler, **self.options)
        self.server.serve_forever()

    def stop(self):
        if self.server:
            try:
                self.server.shutdown()
            except BrokenPipeError:
                pass
            try:
                self.server.server_close()
            except BrokenPipeError:
                pass


class Templates:
    TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

    def __init__(self, cfg, wiki: dict):
        self._cfg = cfg
        self._wiki = wiki
        self._tpl = self._load_templates()

    def _load_templates(self):
        names = ('page', 'config', 'section', 'option', 'remote_log', 'result')
        tpl = {}
        for name in names:
            path = os.path.join(self.TEMPLATES, '{}.tpl'.format(name))
            with open(path) as fp:
                tpl[name] = fp.read()
        return tpl

    def cfg(self) -> str:
        return self._make_page(self._make_config_body())

    def result(self, cfg: dict) -> str:
        return self._make_page(self._make_result_body(cfg))

    def _make_page(self, body: str) -> str:
        return self._template('page', body=body)

    def _make_result_body(self, diff: cfg) -> str:
        return self._template('result', result=json.dumps(diff, ensure_ascii=False, indent=4))

    def _make_config_body(self) -> str:
        sections = []
        tab_names = []
        for key in self._cfg:
            if not isinstance(self._cfg[key], dict):
                continue
            section = self._make_section(key)
            if not section:
                continue
            tab_names.append(key.capitalize())
            sections.append(section)
        # add remote log tab
        terminal_ip = self._cfg.gts('ip')
        terminal_ws_token = self._cfg.gt('system', 'ws_token')
        sections.append(self._template('remote_log', terminal_ip=terminal_ip, terminal_ws_token=terminal_ws_token))
        tab_names.append('[REMOTE LOG]')
        return self._template('config', tab_names=tab_names, sections=sections)

    def _make_section(self, section: str) -> str:
        values = []
        for key, val in self._cfg[section].items():
            if not isinstance(key, str) or section == 'system' and key not in ('ws_token',):
                continue
            values.append(self._make_option(section, key, val, self._wiki.get(section, {}).get(key, '')))
        wiki = self._wiki.get(section, {}).get('null', '')
        if values or wiki:
            return self._template(
                'section',
                wiki=wiki,
                section=section,
                values=values,
            )
        else:
            return ''

    @lru_cache(maxsize=256)
    def _make_option(self, section: str, key: str, value, wiki: str) -> str:
        return self._template('option', section=section, key=key, value=value, wiki=wiki)

    def _template(self, name, **kwargs) -> str:
        return bottle.template(self._tpl[name], **kwargs)