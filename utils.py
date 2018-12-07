import os
import pickle

SUBTYPE_and_FILENAME = (
                        ('population', 'pop_ranking'),
                        ('offPoints', 'off_ranking'),
                        ('deffPoints', 'deff_ranking')
                       )
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def subtypes():
    yield from SUBTYPE_and_FILENAME


def save_account(account):
    path = os.path.join(BASE_DIR, 'account.py')
    with open(path, 'wb') as f:
        pickle.dump(account, f)


def load_account():
    path = os.path.join(BASE_DIR, 'account.py')
    with open(path, 'rb') as f:
        account = pickle.load(f)
    return account


def create_path(gameworld, gameworld_id, file_name):
    return os.path.join(os.path.expanduser('~/Desktop'), f'{gameworld}_{gameworld_id}_{file_name}.log')
