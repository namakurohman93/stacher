import time
import json
from threading import Thread
from tinydb import TinyDB, Query
from queue import Queue

from accounts import data_get_all, login
from connections import get, post
from utils import load_account, create_path, intervals


class Stacher:
    def __init__(self, email, password, save_path=None):
        self.email = email
        self.password = password
        self.path = save_path

        self.account = self.check_account()

        self.start()


    def start(self):
        # first adjust time
        interval = intervals(10)
        print(f'{self} [sleeping:{interval//60}:{interval%60}]')
        time.sleep(interval)
        avatar_pool = {}
        while True:
            print(f'{self} [check avatar...]')
            lobby_details = data_get_all(self.account, state='lobby')
            avatar_list = [avatar for caches in lobby_details['cache']
                           if 'Collection:Avatar:' in caches['name']
                           for avatar in caches['data']['cache']
                        ]
            for avatar in avatar_list:
                if avatar['data']['consumersId'] not in avatar_pool:
                    av = self.account.build_avatar(
                                avatar['data']['worldName'],
                                avatar['data']['consumersId'],
                                self.get_ranking,
                                self.path
                            )
                    avatar_pool[avatar['data']['consumersId']] = av
            # starting avatar
            for gi in avatar_pool:
                avatar_pool[gi].start()
            # sleeping
            interval = intervals(10)
            print(f'{self} [sleeping:{interval//60}:{interval%60}]')
            time.sleep(interval)


    def check_account(self):
        try:
            account = load_account()
            if self.test_login(account):
                account = login(self.email, self.password)
                print(f'Welcome!!! {account.details["avatarName"]}')
            else:
                print(f'Welcome back!! {account.details["avatarName"]}')
        except FileNotFoundError:
            account = login(self.email, self.password)
            print(f'Welcome!!! {account.details["avatarName"]}')
        finally:
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
            results.extend(r.json()['response']['results'])
            task.task_done()


    @staticmethod
    def get_ranking(avatar, ranking_type,
                    ranking_subtype, table_name):
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
        # save results
        path = create_path(avatar.gameworld.lower(),
                           avatar.gameworld_id,
                           avatar.path
                          )
        # db = TinyDB(path)
        # table = db.table(table_name)
        # user = Query()
        try:
            cache = open(path, 'r')
            cache = json.load(cache)
        except FileNotFoundError:
            cache = {}
            cache[table_name] = []
        # for result in results:
        #     if table.search(user.name == result['name']):
        #         table.update(
        #             append(
        #                 'data',
        #                 {
        #                     'epoch': time.time(),
        #                     'datetime': time.strftime("%d/%b/%Y:%H:%M:%S"),
        #                     'points': result['points']
        #                 }
        #             ),
        #             user.name == result['name']
        #         )
        #     else:
        #         table.insert(
        #             {
        #                 'name': result['name'],
        #                 'data': [{
        #                     'epoch': time.time(),
        #                     'datetime': time.strftime("%d/%b/%Y:%H:%M:%S"),
        #                     'points': result['points']
        #                 }]
        #             }
        #         )
        try:
            cache[table_name].extend(results)
        except KeyError:
            cache[table_name] = results
        with open(path, 'w') as f:
            f.write(json.dumps(cache, indent=4))
        print(f'{table_name} on {avatar.gameworld} done.')


# def append(field, n):
#     def transform(doc):
#         if not isinstance(doc[field], list):
#             doc[field] = [doc[field]]
#         doc[field].append(n)
#     return transform
