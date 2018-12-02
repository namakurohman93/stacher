import json
import time
import datetime
from threading import Thread
from queue import Queue

from accounts import Account
from connections import get, post
from hooks import get_msid, get_token, get_session
from utils import subtypes


class Stacher:
    def __init__(self, email, password, gameworld):
        self.email = email
        self.password = password
        self.gameworld = gameworld.upper()

        self.account = self.login(self.email, self.password, self.gameworld)
        self.avatar = self.account.avatar(self.gameworld)

        for subtype, file_name in subtypes():
            self.get_ranking(self.account, self.avatar,
                             'ranking_Player', subtype,
                             file_name, self.gameworld
                            )


    @staticmethod
    def login(email, password, gameworld):

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
        data = {
                'action': 'getAll',
                'controller': 'player',
                'params': {},
                'session': account.session_lobby
        }

        r = post(account.lobby_api,
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
    def stacher_thread(task, ranking_type, ranking_subtype, account, url):
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
                               'rankingSubtype': ranking_subtype
                              },
                    'session': account.session_gameworld
                   }
            r = post(url+f'c=ranking&a=getRanking&t{(time.time()*1000):.0f}',
                     headers=account.headers_gameworld,
                     json=data,
                     cookies=account.cookies_gameworld,
                     timeout=60
                    )
            result = [f'{datetime.datetime.now().strftime("%d/%b/%Y:%H:%M:%S")} {x["name"]} {x["points"]}'
                      for x in r.json()['response']['results']
                     ]
            results.extend(result)
            task.task_done()


    @staticmethod
    def get_ranking(account, avatar, ranking_type,
                    ranking_subtype, file_name, gameworld):
        # get total player
        url = account.gameworld_api % (gameworld.lower(),)
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
        total_player = r.json()['response']['numberOfItems']

        # prepare thread
        start, end = 0, 9
        results = []
        task = Queue(maxsize=(total_player//10)+2)

        for _ in range(8):  # if need more fast, increase range number
            worker = Thread(target=Stacher.stacher_thread,
                            args=(task, ranking_type,
                                  ranking_subtype, account, url
                                 )
                           )
            worker.setDaemon(True)
            worker.start()

        # dispatch thread
        for _ in range((total_player//10)+1):
            task.put((start, end, results))
            time.sleep(0.1)
            start, end = start+10, end+10

        # threading done
        task.join()

        ranking = '\n'.join(results)

        with open(f'/home/didadadida93/Desktop/{file_name}.log', 'a') as f:
            f.write(ranking)
