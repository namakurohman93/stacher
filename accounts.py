import time
import requests

from hooks import get_msid, get_token, get_session

class Accounts:
    def __init__(self, email=None, password=None, gameworld=None):
        self.session = requests.Session()
        self.session.headers = {
            'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.5'
        }
        self.player = None
        self.avatar_list = None
        self.msid = None
        self.session_lobby = None
        self.session_gameworld = None
        if email and password and gameworld:
            self.login(email, password, gameworld)

    def login(self, email=None, password=None, gameworld=None):
        self.email = email
        self.password = password
        self.gameworld = gameworld
        while not self.email:
            self.email = input('>> Email: ')
        while not self.password:
            self.password = input('>> Password: ')
        while not self.gameworld:
            self.gameworld = input('>> Gameworld: ')
        # looking msid
        url = 'https://mellon-t5.traviangames.com/authentication/login/ajax/form-validate?'
        r = self.session.get(url,
                             timeout=60,
                             hooks={'response': get_msid}
                            )
        self.msid = r.msid
        # looking session lobby
        url = f'https://mellon-t5.traviangames.com/authentication/login/ajax/form-validate?msid={self.msid}&msname=msid'
        r = self.session.post(url,
                              data={
                                    'email':self.email,
                                    'password':self.password
                                },
                              timeout=60,
                              hooks={'response': get_token}
                             )
        r = self.session.get(r.url_token,
                             timeout=60,
                             allow_redirects=False
                            )
        r = self.session.get(r.headers['location'],
                             timeout=60,
                             hooks={'response': get_session},
                             allow_redirects=False
                            )
        self.session_lobby = r.session
        # set cookie to session headers
        self.session.headers['cookie'] = f'msid={self.msid};'
        temp_cookie = {k: v for k, v in r.cookies.items()}
        for k, v in temp_cookie.items():
            self.session.headers['cookie'] += f' {k}={v};'
        # api endpoint for lobby
        lobby_url = 'https://lobby.kingdoms.com/api/index.php'
        # looking session gameworld
        data = {
            'action': 'getAll',
            'controller': 'player',
            'params': {},
            'session': self.session_lobby
        }
        r = self.session.post(lobby_url,
                              json=data,
                              timeout=60
                             )
        self.avatar_list = [avatar for caches in r.json()['cache']       # implicit list comprehension
                            if 'Collection:Avatar:' in caches['name']    # for fetching Collection Avatar
                            for avatar in caches['data']['cache']
                           ]
        self.player = {k: v for x in r.json()['cache']      # implicit dictionary comprehension
                       if 'Player:' in x['name']            # for fetching Player detail
                       for k, v in x['data'].items()
                      }
        for cache in self.avatar_list:
            if self.gameworld == cache['data']['worldName']:
                gameworld_id = cache['data']['consumersId']
                break
        url = f'https://mellon-t5.traviangames.com/game-world/join/gameWorldId/{gameworld_id}?msname=msid&msid={self.msid}'
        r = self.session.get(url,
                             timeout=60,
                             hooks={'response': get_token}
                            )
        r = self.session.get(r.url_token,
                             timeout=60,
                             hooks={'response': get_session},
                             allow_redirects=False
                            )
        self.session_gameworld = r.session
        # update session headers
        for k, v in r.cookies.items():
            if k in self.session.headers['cookie']:
                continue
            self.session.headers['cookie'] += f' {k}={v};'
        self.session.headers['accept'] = 'application/json, text/plain, */*'
        self.session.headers['content-type'] = 'application/json;charset=utf-8'
