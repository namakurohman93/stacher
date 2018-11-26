import time
import json
import datetime

class Stacher:
    def __init__(self, account):
        api_url = f'https://{account.gameworld.lower()}.kingdoms.com/api/?'
        data_gameworld = {
                            'controller': 'player',
                            'action': 'getAll',
                            'params': {},
                            'session': account.session_gameworld
                         }
        r = account.session.post(api_url+f'c=player&a=getAll&t{(time.time()*1000):.0f}',
                                 json=data_gameworld,
                                 timeout=60
                                )
        self.avatar = {k: v for cache in r.json()['cache']  # implicit dictionary comprehension
                       if 'Player' in cache['name']         # for fetching avatar detail
                       for k, v in cache['data'].items()
                       }
        data_count_rank = {
                            'controller': 'ranking',
                            'action': 'getRankAndCount',
                            'params': {
                                        'id': self.avatar['playerId'],
                                        'rankingType': 'ranking_Player',
                                        'rankingSubtype': 'population'
                                        },
                            'session': account.session_gameworld
                          }
        r = account.session.post(api_url+f'c=ranking&a=getRankAndCount&t{(time.time()*1000):.0f}',
                                 json=data_count_rank,
                                 timeout=60
                                )
        data_pop_ranking = {
                            'controller': 'ranking',
                            'action': 'getRanking',
                            'params': {
                                        # 'start': 0,
                                        # 'end': 9,
                                        'rankingType': 'ranking_Player',
                                        'rankingSubType': 'population'
                                        },
                            'session': account.session_gameworld
                            }
        r = account.session.post(api_url+f'c=ranking&a=getRanking&t{(time.time()*1000):.0f}',
                                 json=data_pop_ranking,
                                 timeout=60
                                )
