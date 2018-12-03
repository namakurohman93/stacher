import os
import pickle

SUBTYPE_and_FILENAME = (
                        ('population', 'pop_ranking'),
                        ('offPoints', 'off_ranking'),
                        ('deffPoints', 'deff_ranking')
                       )
# RANKING_TYPE = 'ranking_Player'


def subtypes():
    yield from SUBTYPE_and_FILENAME


def save_account(account):
    with open('account.py', 'wb') as f:
        pickle.dump(account, f)


def load_account():
    with open('account.py', 'rb') as f:
        account = pickle.load(f)
    return account


def check_account(login, email, password, gameworld):
    if 'account.py' not in os.listdir(os.getcwd()):
        account = login(email, password, gameworld)
        save_account(account)
    else:
        account = load_account()
    return account


def create_path(file_name):
    return os.path.join(os.path.expanduser('~/Desktop'), f'{file_name}.log')
