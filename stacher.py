import os
import time
import datetime
from threading import Thread
from queue import Queue

from accounts import Account, Avatar, data_get_all
from connections import get, post
from hooks import get_msid, get_token, get_session
from utils import save_account, load_account, create_path, BASE_DIR


class Stacher:
    def __init__(self, save_path=None, email=None, password=None):
        self.email = email
        self.password = password
        self.path = save_path

        self.account = self.check_account(self.email, self.password)

        self.command_line()


    def command_line(self):
        while True:
            gameworld = input()
            avatar = Avatar(self.get_ranking, self.account,
                            self.path, gameworld
                           ).start()


    def check_account(self, email, password):
        if 'account.py' not in os.listdir(BASE_DIR):
            account = self.login(email, password)
            save_account(account)
            print(f'Welcome!!! {account.details["avatarName"]}')
        else:
            account = load_account()
            if self.test_login(account):
                account = self.login(email, password)
                save_account(account)
                print(f'Welcome!!! {account.details["avatarName"]}')
            else:
                print(f'Welcome back!! {account.details["avatarName"]}')

        return account


    @staticmethod
    def login(email, password):
        while not email:
            email = input('Email: ')
        while not password:
            password = input('Password: ')

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
        account.cookies_lobby = r.cookies

        temp_cookie = {k: v for k, v in r.cookies.items()}
        for k, v in temp_cookie.items():
            headers['cookie'] += f' {k}={v};'

        account.headers_lobby = headers

        lobby_details = data_get_all(account, state='lobby')
        account.details = {k: v for caches in lobby_details['cache']    # implicit dictionary comprehension
                           if 'Player:' in caches['name']               # for fetching account details
                           for k, v in caches['data'].items()
                          }
        del lobby_details

        return account


    @staticmethod
    def test_login(account):

        return 'error' in data_get_all(account, state='lobby')


    @staticmethod
    def stacher_thread(task, ranking_type,
                       ranking_subtype, avatar, url):
        while True:
            start, end, results = task.get()
            # print(f'{(time.time()*1000):.0f}')
            data = {
                    'controller': 'ranking',
                    'action': 'getRanking',
                    'params': {
                               'start': start,
                               'end': end,
                               'rankingType': ranking_type,
                               'rankingSubtype': ranking_subtype
                              },
                    'session': avatar.session_gameworld
                   }
            r = post(url+f'c=ranking&a=getRanking&t{(time.time()*1000):.0f}',
                     headers=avatar.headers_gameworld,
                     json=data,
                     cookies=avatar.cookies_gameworld,
                     timeout=60
                    )
            result = [f'{datetime.datetime.now().strftime("%d/%b/%Y:%H:%M:%S")} {x["name"]} {x["points"]}'
                      for x in r.json()['response']['results']
                     ]
            results.extend(result)
            task.task_done()


    @staticmethod
    def get_ranking(avatar, ranking_type,
                    ranking_subtype, file_name):
        # get total player
        url = avatar.gameworld_api
        data = {
                'controller': 'ranking',
                'action': 'getRankAndCount',
                'params': {
                           'id': avatar.details['playerId'],
                           'rankingType': ranking_type,
                           'rankingSubtype': ranking_subtype
                          },
                'session': avatar.session_gameworld
               }
        r = post(url+f'c=ranking&a=getRankAndCount&t{(time.time()*1000):.0f}',
                 headers=avatar.headers_gameworld,
                 json=data,
                 cookies=avatar.cookies_gameworld,
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
                                  ranking_subtype, avatar, url
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
        path = create_path(avatar.gameworld, avatar.gameworld_id,
                           file_name, avatar.path
                          )
        with open(path, 'a') as f:
            f.write(ranking)
            f.write('\n')
        print(f'{avatar.gameworld}_{avatar.gameworld_id}_{file_name} done.')
