import requests

class Account:
    def __init__(self):
        self.msid = None
        self.session_lobby = None
        self.cookies_lobby = None
        self.headers_lobby = None
        self.session_gameworld = None
        self.cookies_gameworld = None
        self.headers_gameworld = None
        self.lobby_api = 'https://lobby.kingdoms.com/api/index.php'
        self.gameworld_api = 'https://%s.kingdoms.com/api/?'

    def avatar(self, gameworld):
        gameworld_api = self.gameworld_api % (gameworld.lower(),)
        data = {
                'controller': 'player',
                'action': 'getAll',
                'params': {},
                'session': self.session_gameworld
               }
        r = requests.post(gameworld_api,
                          headers=self.headers_gameworld,
                          json=data,
                          timeout=60
                         )
        avatar_detail = {k: v for cache in r.json()['cache']  # implicit dictionary comprehension
                       if 'Player:' in cache['name']         # for fetching avatar detail
                       for k, v in cache['data'].items()
                      }

        return avatar_detail
