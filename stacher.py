import time
import json
import logging
import threading
from queue import Queue

from accounts import data_get_all, check_session, login
from connections import get, post
from utils import load_account, create_path, intervals

logging.basicConfig(
    format='[%(asctime)s][%(levelname)s]: %(message)s',
    level=logging.DEBUG, datefmt='%d/%b/%Y:%H:%M:%S'
)
# Logging logging.INFO only so it doesnt floaded with logging.DEBUG
for logs in logging.Logger.manager.loggerDict:
    logging.getLogger(logs).setLevel(logging.INFO)


class Stacher:
    def __init__(self, email, password, save_path=None):
        self.email = email
        self.password = password
        self.path = save_path

        self.account = self.check_account()

        self.start()


    def start(self):
        avatar_pool = {}
        while True:
            logging.info('check avatar.')
            lobby_details = data_get_all(self.account)
            avatars = [avatar for caches in lobby_details['cache']
                       if 'Collection:Avatar:' in caches['name']
                       for avatar in caches['data']['cache']
                    ]
            for avatar in avatars:
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
                if avatar_pool[gi].is_alive():
                    continue
                avatar_pool[gi].start()
            # sleeping
            interval = intervals(10)
            logging.info(f'Stacher sleeping:{interval//60}:{interval%60}')
            time.sleep(interval)


    def check_account(self):
        try:
            account = load_account()
            if self.test_login(account):
                account = login(self.email, self.password)
                logging.info(f'Welcome!!! {account.details["avatarName"]}')
            else:
                logging.info(f'Welcome back!! {account.details["avatarName"]}')
        except FileNotFoundError:
            account = login(self.email, self.password)
            logging.info(f'Welcome!!! {account.details["avatarName"]}')
        finally:
            return account


    @staticmethod
    def test_login(account):
        return 'error' in check_session(account, state='lobby')


    @staticmethod
    def stacher_thread(task, ranking_type,
                       ranking_subtype, avatar, url):
        while True:
            start, end, results = task.get()
            if start is None:
                break
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
        url = avatar.lobby_api
        data = {
                'controller': 'cache',
                'action': 'get',
                'params': {
                           'names': [f'GameWorld:{avatar.gameworld_id}']
                        },
                'session': avatar.session_lobby
            }
        r = post(url,
                 headers=avatar.headers_lobby,
                 json=data,
                 cookies=avatar.cookies_lobby,
                 timeout=60
            )
        total_player = r.json()['cache'][0]['data']['playersRegistered']
        # prepare thread
        url = avatar.gameworld_api
        start, end = 0, 9
        results = []
        threads = []
        task = Queue()

        for _ in range(2):
            worker = threading.Thread(target=Stacher.stacher_thread,
                                      args=(task, ranking_type,
                                      ranking_subtype, avatar, url
                                    )
                                )
            worker.start()
            threads.append(worker)
        # dispatch thread
        for _ in range((total_player//10)+1):
            task.put((start, end, results))
            time.sleep(0.1)
            start, end = start+10, end+10
        # threading done
        task.join()
        for _ in range(2):
            task.put((None, None, None))
        for t in threads:
            t.join()
        # save results
        path = create_path(avatar.gameworld.lower(),
                           avatar.gameworld_id,
                           avatar.path
                          )
        try:
            cache = open(path, 'r')
            cache = json.load(cache)
            try:
                cache[table_name]
            except KeyError:
                cache[table_name] = {}
        except FileNotFoundError:
            cache = {}
            cache[table_name] = {}
        result = (line for line in results)
        data = (
            {
                x['playerId']: {
                    'name': x['name'],
                    'data': [{
                        'timestamp': time.time(),
                        'points': x['points']
                    }]
                }
            } for x in result
        )
        for x in data:
            for pid in x:
                if pid in cache[table_name]:
                    cache[table_name][pid]['data'].extend(x[pid]['data'])
                else:
                    cache[table_name][pid] = x[pid]
        with open(path, 'w') as f:
            f.write(json.dumps(cache, indent=4))
        logging.info(f'{table_name} on {avatar.gameworld} done.')
