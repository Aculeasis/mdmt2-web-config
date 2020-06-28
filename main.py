import hashlib
import json
import os
import threading
import time
from functools import lru_cache
from wsgiref.simple_server import make_server, WSGIRequestHandler

import bottle
# noinspection PyUnresolvedReferences
from less_settings import less_settings

import logger
from owner import Owner
from utils import state_cache

NAME = 'web-config'
API = 665
TERMINAL_VER_MIN = (0, 15, 3)

SETTINGS = 'web_config_config'

SELF_AUTH_CHANNEL = 'net.self.auth'


class Main(threading.Thread):
    def __init__(self, cfg, log, owner: Owner):
        super().__init__()
        self.cfg = cfg
        self.log = log
        self.own = owner

        self.disable = False
        try:
            self._tpl = Templates(self.cfg)
        except RuntimeError as e:
            self.log(e, logger.ERROR)
            self.disable = True
            return
        self._settings = self._get_settings()
        self._server = MyApp(self._settings['ip'], self._settings['port'], self._settings['quiet'])
        self._server.route('/', callback=self._do_get)
        self._server.route('/<mode>', callback=self._do_get)
        self._server.route('/', 'POST', self._do_post)
        self._server.route('/<mode>', 'POST', self._do_post)

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
        self.own.sub_call(SELF_AUTH_CHANNEL, 'add', NAME, self._tpl.check_auth)
        super().start()

    def join(self, timeout=30):
        self._stop()
        super().join(timeout)

    def _stop(self):
        self.own.sub_call(SELF_AUTH_CHANNEL, 'remove', NAME, self._tpl.check_auth)
        self._server.stop()

    def run(self):
        try:
            self._server.run()
        except OSError as e:
            self.log('Listen error: {}'.format(e), logger.CRIT)
            self._stop()
        else:
            self.log('Start listen {}:{}'.format(self._server.ip, self._server.port))
            self.log('Available in http://{}:{}/'.format(self.cfg.gts('ip'), self._server.port), logger.INFO)

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

    def _do_get(self, mode='more'):
        less = is_less(mode)
        self._auth_basic()
        return self._tpl.cfg(less=less)

    def _do_post(self, mode='more'):
        less = is_less(mode)
        self._auth_basic()
        result = {}
        for key, val in dict(bottle.request.forms.decode('utf-8')).items():
            # 'section$key': value
            key = key.split('$', 1)
            if len(key) == 2 and key[0]:
                if key[0] not in result:
                    result[key[0]] = {}
                result[key[0]][key[1]] = val
        return self._tpl.result(less, self.own.settings_from_srv(result))


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


def is_less(mode) -> bool:
    if mode == 'less':
        return True
    elif mode == 'more':
        return False
    raise bottle.HTTPError(404, "Not found: " + repr(bottle.request.path))


class MyApp(bottle.Bottle):
    def __init__(self, ip, port, quiet):
        super().__init__()
        self.ip = ip
        self.port = port
        self._server = MyWSGIRefServer(host=ip, port=port, quiet=quiet)

    def stop(self):
        time.sleep(0.1)
        self._server.stop()

    def run(self):
        super().run(server=self._server)


class MyWSGIRefServer(bottle.ServerAdapter):
    server = None

    def __init__(self, host='127.0.0.1', port=8080, **options):
        super().__init__(host, port, **options)
        quiet = self.options.pop('quiet', None)
        if quiet is not None:
            self.quiet = quiet
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            self.options['handler_class'] = QuietHandler

    def run(self, handler):
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
            self.server = None


class Templates:
    TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    MAINTENANCE = '[MAINTENANCE]'

    def __init__(self, cfg):
        self._cfg = cfg
        self._tpl = self._load_templates()

    def _load_templates(self):
        names = ('page', 'config', 'section', 'option', 'maintenance', 'result')
        tpl = {}
        for name in names:
            path = os.path.join(self.TEMPLATES, '{}.tpl'.format(name))
            with open(path) as fp:
                tpl[name] = fp.read()
        return tpl

    @property
    @state_cache(48 * 3600)
    def _token(self):
        return hashlib.sha512(os.urandom(64)).hexdigest()

    def check_auth(self, token: str, *_) -> bool:
        return self._token == token

    def cfg(self, less: bool) -> str:
        return self._make_config_page(less, less_settings(self._cfg) if less else self._cfg, self._token)

    def result(self, less: bool, cfg: dict) -> str:
        return self._make_page(self._make_result_body(less, cfg))

    def _make_page(self, body: str) -> str:
        return self._template('page', body=body)

    def _make_result_body(self, less: bool, diff: dict) -> str:
        return self._template(
            'result',
            result=json.dumps(diff, ensure_ascii=False, indent=4),
            version=self._cfg.version_str,
            less=less,
        )

    @lru_cache(maxsize=1)
    def _make_config_page(self, less, cfg, token) -> str:
        sections = []
        tab_names = []
        wiki = self._cfg.wiki_desc
        for key in cfg:
            if not isinstance(cfg[key], dict):
                continue
            section = self._make_section(key, cfg, wiki.get(key, {}))
            if not section:
                continue
            tab_names.append(key.capitalize())
            sections.append(section)
        # add maintenance tab
        terminal_ip = self._cfg.gts('ip')
        # websocket authorization
        terminal_ws_token = self._cfg.gt('system', 'ws_token')
        # authorization
        auth_request = json.dumps(
            {'method': 'authorization.self', 'params': {'token': token, 'owner': NAME}, 'id': 'Authorization'})
        sections.append(self._template(
            'maintenance', terminal_ip=terminal_ip, terminal_ws_token=terminal_ws_token, auth_request=auth_request))
        tab_names.append(self.MAINTENANCE)
        return self._make_page(self._template(
            'config',
            tab_names=tab_names, sections=sections, version=self._cfg.version_str, MAINTENANCE=self.MAINTENANCE,
            less=less,
            )
        )

    def _make_section(self, section: str, cfg: dict, wiki_desc: dict) -> str:
        values = []
        for key, val in cfg[section].items():
            if not isinstance(key, str) or section == 'system' and key not in ('ws_token',):
                continue
            values.append(self._make_option(section, key, val, wiki_desc.get(key, '')))
        wiki = wiki_desc.get('null', '')
        if values or wiki:
            return self._template(
                'section',
                wiki=wiki,
                section=section,
                values=values,
            )
        else:
            return ''

    def _make_option(self, section: str, key: str, value, wiki: str) -> str:
        return self._template('option', section=section, key=key, value=value, wiki=wiki)

    def _template(self, name, **kwargs) -> str:
        return bottle.template(self._tpl[name], **kwargs)
