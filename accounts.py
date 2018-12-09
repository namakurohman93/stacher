import time
import threading

from connections import get, post
from exceptions import GetError
from hooks import get_token, get_session
from utils import subtypes, intervals


class Account:
    def __init__(self):
        self.msid = None
        self.session_lobby = None
        self.cookies_lobby = None
        self.headers_lobby = None
        self.details = None

        self.lobby_api = 'https://lobby.kingdoms.com/api/index.php'
        self.gameworld_api = 'https://%s.kingdoms.com/api/?'


class Avatar(threading.Thread):
    __attrs__ = ['msid', 'session_lobby', 'cookies_lobby',
                 'headers_lobby', 'lobby_api', 'gameworld_api'
                ]


    def __init__(self, get_ranking, account, path, gameworld):
        threading.Thread.__init__(self, name=gameworld, daemon=True)

        self.get_ranking = get_ranking
        self.path = path
        self.gameworld = gameworld.upper()

        for attr in self.__attrs__:
            setattr(self, attr, getattr(account, attr, None))

        self.gameworld_api = self.gameworld_api % (self.gameworld.lower(),)

        self.gameworld_id = None
        self.session_gameworld = None
        self.cookies_gameworld = None
        self.headers_gameworld = None
        self.details = None

        self.login()


    def login(self):
        # looking session gameworld
        lobby_details = data_get_all(self, state='lobby')
        avatar_list = [avatar for caches in lobby_details['cache']  # implicit list comprehension
                       if 'Collection:Avatar:' in caches['name']    # for fetching Collection Avatar
                       for avatar in caches['data']['cache']
                      ]
        for cache in avatar_list:
            if self.gameworld == cache['data']['worldName']:
                self.gameworld_id = cache['data']['consumersId']
                break

        if not self.gameworld_id:
            error = f'you didnt have avatar at {self.gameworld.lower()}'
            raise GetError(error)

        del lobby_details
        del avatar_list

        url = f'https://mellon-t5.traviangames.com/game-world/join/gameWorldId/{self.gameworld_id}?msname=msid&msid={self.msid}'
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

        gameworld_details = data_get_all(self, state='gameworld')
        self.details = {k: v for cache in gameworld_details['cache']  # implicit dictionary comprehension
                        if 'Player:' in cache['name']                 # for fetching avatar detail
                        for k, v in cache['data'].items()
                       }
        del gameworld_details


    def run(self):
        # first adjust time
        interval = intervals(10)
        print(f'{threading.current_thread()}' +
              f' [sleeping:{interval//60}:{interval%60}]')
        time.sleep(interval)
        while True:
            print(f'{threading.current_thread()} [starting]')
            for subtype, file_name in subtypes():
                self.get_ranking(self, 'ranking_Player',
                                 subtype, file_name
                                )
            interval = intervals(10)
            print(f'{threading.current_thread()}' +
                  f' [sleeping:{interval//60}:{interval%60}]')
            time.sleep(interval)


def data_get_all(obj, state=None):
    url = obj.lobby_api if state == 'lobby' else \
        obj.gameworld_api if state == 'gameworld' else \
        None

    session = obj.session_lobby if state == 'lobby' else \
        obj.session_gameworld if state == 'gameworld' else \
        None

    headers = obj.headers_lobby if state == 'lobby' else \
        obj.headers_gameworld if state == 'gameworld' else \
        None

    cookies = obj.cookies_lobby if state == 'lobby' else \
        obj.cookies_gameworld if state == 'gameworld' else \
        None

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
