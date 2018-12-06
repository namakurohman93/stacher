import time
import threading

from connections import get, post
from hooks import get_token, get_session
from utils import subtypes


class Account:
    def __init__(self):
        self.email = None
        self.msid = None
        self.session_lobby = None
        self.cookies_lobby = None
        self.headers_lobby = None
        self.details = None

        self.lobby_api = 'https://lobby.kingdoms.com/api/index.php'
        self.gameworld_api = 'https://%s.kingdoms.com/api/?'


class Avatar(threading.Thread):
    __attrs__ = ['email', 'msid', 'session_lobby', 'cookies_lobby',
                 'headers_lobby', 'lobby_api', 'gameworld_api'
                ]


    def __init__(self, get_ranking, account, gameworld):
        threading.Thread.__init__(self, name=gameworld, daemon=True)
        self.get_ranking = get_ranking
        self.gameworld = gameworld.upper()
        for attr in self.__attrs__:
            setattr(self, attr, getattr(account, attr, None))

        self.login()


    def login(self):
        # looking session gameworld
        lobby_details = lobby_get_all(self)
        avatar_list = [avatar for caches in lobby_details['cache']  # implicit list comprehension
                       if 'Collection:Avatar:' in caches['name']    # for fetching Collection Avatar
                       for avatar in caches['data']['cache']
                      ]
        for cache in avatar_list:
            if self.gameworld == cache['data']['worldName']:
                self.gameworld_id = cache['data']['consumersId']
                break

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

        url = self.gameworld_api % (self.gameworld.lower(),)
        data = {
                'controller': 'player',
                'action': 'getAll',
                'params': {},
                'session': self.session_gameworld
               }
        r = post(url,
                 headers=self.headers_gameworld,
                 json=data,
                 cookies=self.cookies_gameworld,
                 timeout=60
                )
        self.details = {k: v for cache in r.json()['cache']  # implicit dictionary comprehension
                        if 'Player:' in cache['name']       # for fetching avatar detail
                        for k, v in cache['data'].items()
                       }


    def run(self):
        # first adjust time
        interval = 3600 - (int(f'{(time.time()):.0f}')%3600)
        time.sleep(interval)
        print(threading.current_thread())
        while True:
            for subtype, file_name in subtypes():
                self.get_ranking(self, 'ranking_Player',
                                 subtype, file_name
                                )
            time.sleep(3600)


def lobby_get_all(obj):
    data = {
            'action': 'getAll',
            'controller': 'player',
            'params': {},
            'session': obj.session_lobby
           }

    r = post(obj.lobby_api,
             headers=obj.headers_lobby,
             json=data,
             cookies=obj.cookies_lobby,
             timeout=60
            )

    return r.json()
