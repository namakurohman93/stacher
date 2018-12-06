import os
import pickle

SUBTYPE_and_FILENAME = (
                        ('population', 'pop_ranking'),
                        ('offPoints', 'off_ranking'),
                        ('deffPoints', 'deff_ranking')
                       )


def subtypes():
    yield from SUBTYPE_and_FILENAME


def save_account(account):
    with open('account.py', 'wb') as f:
        pickle.dump(account, f)


def load_account():
    with open('account.py', 'rb') as f:
        account = pickle.load(f)
    return account


def create_path(gameworld, gameworld_id, file_name):
    return os.path.join(os.path.expanduser('~/Desktop'), f'{gameworld}_{gameworld_id}_{file_name}.log')
