import time
import logging
import threading

from connections import get, post
from hooks import get_token, get_session, get_msid
from utils import subtypes, intervals, save_account

logging.basicConfig(
    format='[%(asctime)s][%(levelname)s]: %(message)s',
    level=logging.DEBUG, datefmt='%d/%b/%Y:%H:%M:%S'
)
# Logging logging.INFO only so it doesnt floaded with logging.DEBUG
for logs in logging.Logger.manager.loggerDict:
    logging.getLogger(logs).setLevel(logging.INFO)


class Account:
    def __init__(self):
        self.msid = None
        self.session_lobby = None
        self.cookies_lobby = None
        self.headers_lobby = None
        self.details = None

        self.lobby_api = 'https://lobby.kingdoms.com/api/index.php'
        self.gameworld_api = 'https://%s.kingdoms.com/api/?'


    def build_avatar(self, gameworld, gameworld_id, get_ranking, path):
        return Avatar(self, get_ranking, path, gameworld, gameworld_id)


class Avatar(threading.Thread):
    __attrs__ = ['msid', 'session_lobby', 'cookies_lobby',
                 'headers_lobby', 'lobby_api', 'gameworld_api'
                ]


    def __init__(self, account, get_ranking, path, gameworld, gameworld_id):
        threading.Thread.__init__(self, name=gameworld, daemon=True)

        for attr in self.__attrs__:
            setattr(self, attr, getattr(account, attr, None))

        self.get_ranking = get_ranking
        self.path = path
        self.gameworld = gameworld.upper()
        self.gameworld_id = gameworld_id

        self.gameworld_api = self.gameworld_api % (self.gameworld.lower(),)

        self.session_gameworld = None
        self.cookies_gameworld = None
        self.headers_gameworld = None

        self.login()


    def login(self):
        url = 'https://mellon-t5.traviangames.com/game-world/join/' + \
              f'gameWorldId/{self.gameworld_id}?msname=msid&msid={self.msid}'
        r = get(url,
                headers=self.headers_lobby,
                cookies=self.cookies_lobby,
                hooks={'response': get_token},
                timeout=60
            )
        r = get(r.url_token,
                headers=self.headers_lobby,
                cookies=self.cookies_lobby,
                hooks={'response': get_session},
                timeout=60,
                allow_redirects=False
            )
        self.session_gameworld = r.session
        # set cookies & headers gameworld
        self.cookies_gameworld = r.cookies
        self.headers_gameworld = self.headers_lobby
        for k, v in r.cookies.items():
            if k in self.headers_gameworld['cookie']:
                continue
            self.headers_gameworld['cookie'] += f' {k}={v};'
        self.headers_gameworld['accept'] = 'application/json, text/plain, */*'
        self.headers_gameworld['content-type'] = 'application/json;charset=utf-8'


    def run(self):
        # first adjust time
        interval = intervals(10)
        logging.info(f'{threading.current_thread()} <id:{id(self)}>' + \
                     f' [sleeping:{interval//60}:{interval%60}]'
                    )
        time.sleep(interval)
        while True:
            try:
                logging.info(f'{threading.current_thread()} <id:{id(self)}>' + \
                             f' [starting]'
                            )
                for subtype, table_name in subtypes():
                    self.get_ranking(self, 'ranking_Player',
                                     subtype, table_name
                                )
            except Exception as e:
                logging.debug(f'{e}')
            finally:
                interval = intervals(10)
                logging.info(f'{threading.current_thread()} <id:{id(self)}>' + \
                             f' [sleeping:{interval//60}:{interval%60}]'
                            )
                time.sleep(interval)


def data_get_all(obj):
    url = obj.lobby_api
    session = obj.session_lobby
    headers = obj.headers_lobby
    cookies = obj.cookies_lobby
    data = {
            'action': 'getAll',
            'controller': 'player',
            'params': {},
            'session': session
        }
    r = post(url,
             headers=headers,
             json=data,
             cookies=cookies,
             timeout=60
        )
    return r.json()


def check_session(obj, state=None):
    if state == 'lobby':
        url = obj.lobby_api
        session = obj.session_lobby
        headers = obj.headers_lobby
        cookies = obj.cookies_lobby
    elif state == 'gameworld':
        url = obj.lobby_api+f'a=get&c=cache&t{(time.time()*1000):.0f}'
        session = obj.session_gameworld
        headers = obj.headers_gameworld
        cookies = obj.cookies_gameworld
    else:
        url, session, headers, cookies = None, None, None, None
    data = {
        'action': 'get',
        'controller': 'cache',
        'params': {
            'names': [
                f'Session:{session}'
            ]
        },
        'session': session
    }
    r = post(url,
             headers=headers,
             json=data,
             cookies=cookies,
             timeout=60
            )
    return r.text


def login(email, password):
    account = Account()
    # looking msid
    url = 'https://mellon-t5.traviangames.com/authentication/login/' + \
          'ajax/form-validate?'
    ua = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:63.0) Gecko/20100101' + \
         ' Firefox/63.0'
    headers = {
        'user-agent': ua,
        'accept-encoding' : 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.5'
    }
    r = get(url,
            headers=headers,
            hooks={'response': get_msid},
            timeout=60
        )
    account.msid = r.msid
    # looking session lobby
    url = 'https://mellon-t5.traviangames.com/authentication/login/ajax/' + \
          f'form-validate?msid={account.msid}&msname=msid'
    r = post(url,
             headers=headers,
             data={
                'email': email,
                'password': password
             },
             hooks={'response': get_token},
             timeout=60
        )
    headers['cookie'] = f'msid={account.msid};'
    r = get(r.url_token,
            headers=headers,
            timeout=60,
            allow_redirects=False
        )
    r = get(r.headers['location'],
            headers=headers,
            hooks={'response': get_session},
            timeout=60,
            allow_redirects=False
        )
    account.session_lobby = r.session
    # set cookies & headers lobby
    account.cookies_lobby = r.cookies
    temp_cookie = {k: v for k, v in r.cookies.items()}
    for k, v in temp_cookie.items():
        headers['cookie'] += f' {k}={v};'
    account.headers_lobby = headers
    lobby_details = data_get_all(account)
    account.details = {k: v for caches in lobby_details['cache']
                       if 'Player:' in caches['name']
                       for k, v in caches['data'].items()
                    }
    save_account(account)
    return account
