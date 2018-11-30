import json
import time
import datetime
from threading import Thread
from queue import Queue

from accounts import Account
from connections import get, post
from hooks import get_msid, get_token, get_session

class Stacher:
    def __init__(self, email, password, gameworld):
        self.email = email
        self.password = password
        self.gameworld = gameworld.upper()

        self.account = self.login(self.email, self.password, self.gameworld)

        self.get_pop_ranking()

    def login(self, email, password, gameworld):

        account = Account()

        # looking msid
        url = 'https://mellon-t5.traviangames.com/authentication/login/ajax/form-validate?'
        headers = {
            'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0',
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
        url = f'https://mellon-t5.traviangames.com/authentication/login/ajax/form-validate?msid={account.msid}&msname=msid'
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
        cookies = r.cookies
        account.cookies_lobby = r.cookies

        temp_cookie = {k: v for k, v in r.cookies.items()}
        for k, v in temp_cookie.items():
            headers['cookie'] += f' {k}={v};'

        account.headers_lobby = headers

        # looking session gameworld
        lobby_url = 'https://lobby.kingdoms.com/api/index.php'
        data = {
                'action': 'getAll',
                'controller': 'player',
                'params': {},
                'session': account.session_lobby
        }

        r = post(lobby_url,
                 headers=headers,
                 json=data,
                 cookies=cookies,
                 timeout=60
                )

        avatar_list = [avatar for caches in r.json()['cache']       # implicit list comprehension
                       if 'Collection:Avatar:' in caches['name']    # for fetching Collection Avatar
                       for avatar in caches['data']['cache']
                      ]
        for cache in avatar_list:
            if gameworld == cache['data']['worldName']:
                gameworld_id = cache['data']['consumersId']
                break

        url = f'https://mellon-t5.traviangames.com/game-world/join/gameWorldId/{gameworld_id}?msname=msid&msid={account.msid}'
        r = get(url,
                headers=headers,
                cookies=cookies,
                hooks={'response': get_token},
                timeout=60
               )
        r = get(r.url_token,
                headers=headers,
                cookies=cookies,
                hooks={'response': get_session},
                timeout=60,
                allow_redirects=False
               )

        account.session_gameworld = r.session

        # set cookies & headers gameworld
        account.cookies_gameworld = r.cookies

        for k, v in r.cookies.items():
            if k in headers['cookie']:
                continue
            headers['cookie'] += f' {k}={v};'
        headers['accept'] = 'application/json, text/plain, */*'
        headers['content-type'] = 'application/json;charset=utf-8'

        account.headers_gameworld = headers

        return account

    @staticmethod
    def _stacher_thread(task, ranking_type, ranking_subtype, account, url):
        while True:
            start, end, results = task.get()
            print(f'{(time.time()*1000):.0f}')
            data = {
                    'controller': 'ranking',
                    'action': 'getRanking',
                    'params': {
                               'start': start,
                               'end': end,
                               'rankingType': ranking_type,
                               'rankingSubType': ranking_subtype
                              },
                    'session': account.session_gameworld
                   }
            r = post(url+f'c=ranking&a=getRanking&t{(time.time()*1000):.0f}',
                     headers=account.headers_gameworld,
                     json=data,
                     cookies=account.cookies_gameworld,
                     timeout=60
                    )
            results.extend(r.json()['response']['results'])
            task.task_done()

    def get_pop_ranking(self):
        account = self.account
        url = f'https://{self.gameworld.lower()}.kingdoms.com/api/?'
        avatar = account.avatar(self.gameworld)
        ranking_type = 'ranking_Player'
        ranking_subtype = 'population'
        data = {
                'controller': 'ranking',
                'action': 'getRankAndCount',
                'params': {
                           'id': avatar['playerId'],
                           'rankingType': ranking_type,
                           'rankingSubtype': ranking_subtype
                          },
                'session': account.session_gameworld
               }
        r = post(url+f'c=ranking&a=getRankAndCount&t{(time.time()*1000):.0f}',
                 headers=account.headers_gameworld,
                 json=data,
                 cookies=account.cookies_gameworld,
                 timeout=60
                )

        max_player = r.json()['response']['numberOfItems']
        start, end = 0, 9
        results = []

        task = Queue(maxsize=(max_player//10)+2)

        for _ in range(5):
            worker = Thread(target=self._stacher_thread,
                            args=(task, ranking_type,
                                  ranking_subtype, account, url
                                 )
                           )
            worker.setDaemon(True)
            worker.start()

        for _ in range((max_player//10)+1):
            task.put((start, end, results))
            time.sleep(0.1)
            start, end = start+10, end+10

        task.join()

        pop_ranking = {'date': datetime.datetime.now().strftime("%Y-%m-%d"),
                       'time': datetime.datetime.now().strftime("%H:%M:%S"),
                       'results': results
                      }

        with open(r'/home/didadadida93/Desktop/pop_ranking.json', 'w') as f:
            f.write(json.dumps(pop_ranking, indent=4))
