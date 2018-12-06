import time
import datetime
from threading import Thread
from queue import Queue

from accounts import Account, Avatar, lobby_get_all
from connections import get, post
from hooks import get_msid, get_token, get_session
from utils import subtypes, check_account, create_path


class Stacher:
    def __init__(self, email=None, password=None):
        self.email = email
        self.password = password

        self.account = check_account(self.login, self.email,
                                     self.password, self.test_login
                                    )
        self.command_line()
        # gameworld = input('Gameworld: ')
        # self.avatar = self.account.build_avatar(gameworld)
        # avatar_detail = self.avatar.avatar()

        # for subtype, file_name in subtypes():
        #     self.get_ranking(self.avatar, 'ranking_Player',
        #                      subtype, file_name
        #                     )


    def command_line(self):
        while True:
            gameworld = input()
            avatar = Avatar(self.get_ranking, self.account,
                            gameworld
                           ).start()
            # avatar.join()


    @staticmethod
    def login(email, password):
        while not email:
            email = input('Email: ')
        while not password:
            password = input('Password: ')

        account = Account()
        account.email = email

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

        lobby_details = lobby_get_all(account)
        account.details = {k: v for caches in lobby_details['cache']    # implicit dictionary comprehension
                           if 'Player:' in caches['name']               # for fetching account details
                           for k, v in caches['data'].items()
                          }
        del lobby_details

        return account


    @staticmethod
    def test_login(account):
        data = {
                'action': 'getPossibleNewGameworlds',
                'controller': 'gameworld',
                'params': {},
                'session': account.session_lobby
               }
        r = post(account.lobby_api,
                 headers=account.headers_lobby,
                 json=data,
                 cookies=account.cookies_lobby,
                 timeout=60
                )

        return 'error' in r.json()


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
        url = avatar.gameworld_api % (avatar.gameworld.lower(),)
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
        path = create_path(avatar.gameworld,
                           avatar.gameworld_id, file_name
                          )
        with open(path, 'a') as f:
            f.write(ranking)
            f.write('\n')
        print(f'{avatar.gameworld}_{avatar.gameworld_id}_{file_name} done.')
