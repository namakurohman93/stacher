import os
import time
import pickle

SUBTYPE_and_TABLENAME = (
                        ('population', 'pop_ranking'),
                        ('offPoints', 'off_ranking'),
                        ('deffPoints', 'deff_ranking')
                       )
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def subtypes():
    yield from SUBTYPE_and_TABLENAME


def save_account(account):
    path = os.path.join(BASE_DIR, 'account.py')
    with open(path, 'wb') as f:
        pickle.dump(account, f)


def load_account():
    path = os.path.join(BASE_DIR, 'account.py')
    with open(path, 'rb') as f:
        account = pickle.load(f)
    return account


def create_path(gameworld, gameworld_id, save_path):
    if save_path:
        try:
            os.mkdir(os.path.join(save_path,
                                  f'{gameworld}_{gameworld_id}'
                                 )
                    )
        finally:
            return os.path.join(save_path,
                                f'{gameworld}_{gameworld_id}',
                                'data.json'
                                )
    try:
        os.makedirs(os.path.join(BASE_DIR, 'logs',
                                 f'{gameworld}_{gameworld_id}'
                                )
                   )
    except FileExistsError:
        try:
            os.mkdir(os.path.join(BASE_DIR, 'logs',
                                  f'{gameworld}_{gameworld_id}'
                                 )
                    )
        except FileExistsError:
            pass
    finally:
        return os.path.join(BASE_DIR, 'logs',
                            f'{gameworld}_{gameworld_id}',
                            'data.json'
                           )


def intervals(interval=60): #interval in minutes
    inter = int(3600 * (interval/60))
    return inter - (int(f'{(time.time()):.0f}')%inter)
