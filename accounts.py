import requests

from hooks import get_msid, get_token, get_session

class Accounts:
    def __init__(self, email=None, password=None, gameworld=None):
        self.session = requests.Session()
        self.session.headers = {
            'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:63.0) Gecko/20100101 Firefox/63.0',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.5'
        }
        self.msid = None
        self.session_lobby = None
        self.session_gameworld = None
        if email and password and gameworld:
            self.login(email, password, gameworld)

    def login(self, email=None, password=None, gameworld=None):
        self.email = email
        self.password = password
        self.gameworld = gameworld
        while not self.email:
            self.email = input('>> Email: ')
        while not self.password:
            self.password = input('>> Password: ')
        while not self.gameworld:
            self.gameworld = input('>> Gameworld: ')
        # looking msid
        url = 'https://mellon-t5.traviangames.com/authentication/login/ajax/form-validate?'
        r = self.session.get(url,
                            timeout=60,
                            hooks={'response': get_msid}
                            )
        self.msid = r.msid
        # looking session lobby
        url = f'https://mellon-t5.traviangames.com/authentication/login/ajax/form-validate?msid={self.msid}&msname=msid'
        r = self.session.post(url,
                              data={
                                    'email':self.email,
                                    'password':self.password
                                },
                              timeout=60,
                              hooks={'response': get_token}
                              )
        r = self.session.get(r.url_token,
                             timeout=60,
                             allow_redirects=False
                            )
        r = self.session.get(r.headers['location'],
                             timeout=60,
                             hooks={'response': get_session},
                             allow_redirects=False
                            )
        self.session_lobby = r.session
        # test connection to lobby
        lobby_url = 'https://lobby.kingdoms.com/api/index.php' # api endpoint for lobby
        data = {
            'action': 'get',
            'controller': 'cache',
            'params': {'names':['Collection:Avatar:']},
            'session': self.session_lobby}
        r = self.session.post(lobby_url,
                              json=data,
                              timeout=60)
        print(r.text)

if __name__ == '__main__':
    accounts = Accounts()
