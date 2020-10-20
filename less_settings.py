from functools import lru_cache


LESS_CFG = {
    'settings': {
        'providertts',
        'providerstt',
        'ip',
        'phrase_time_limit',
        'chrome_mode',
        'lang',
    },
    'listener': {
        'stream_recognition',
        'vad_mode',
        'vad_chrome',
        'silent_multiplier',
        'speech_timeout',
    },
    'smarthome': {
        'ip',
        'token',
        'terminal',
        'username',
        'password',
        'object_name',
        'object_method',
        'heartbeat_timeout',
    },
    'music': {
        'control',
        'type',
        'ip',
        'port',
        'username',
        'password',
        'pause',
        'smoothly',
        'quieter',
        'wait_resume',
        'lms_player',
    },
    'plugins': {
        'enable',
    },
    'system': {
        'ws_token',
    }
}


@lru_cache(maxsize=1)
def less_settings(cfg: dict, less_type):
    def gts(key_, default=None):
        return cfg['settings'].get(key_, default)
    result = less_type()
    stts = {gts(name) for name in ('providertts', 'providerstt') if gts(name) and gts(name) not in LESS_CFG}
    for key, val in cfg.items():
        if key in LESS_CFG:
            result[key] = make_section(val, LESS_CFG[key]) if key != 'music' else make_music_section(val, LESS_CFG[key])
        elif key in stts:
            result[key] = make_section(val, {'*'})
    return result


def make_section(sec: dict, allow: set) -> dict:
    return {key: val for key, val in sec.items() if key in allow or '*' in allow}


def make_music_section(sec: dict, allow: set) -> dict:
    # mpd, lms, volumio2, dlna
    type_ = sec.get('type', None)
    result = dict()
    for key, val in sec.items():
        if key == 'port' and type_ == 'dlna' or \
           key == 'lms_player' and type_ != 'lms' or\
           key not in allow:
            continue
        result[key] = val
    return result
