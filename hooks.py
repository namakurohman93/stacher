"""
Event Hooks
Requests has a hook system that you can use to manipulate
portions of the request process, or signal event handling.

http://docs.python-requests.org/en/stable/user/advanced/#event-hooks
"""

import re

from exceptions import GetError

def get_msid(r, *args, **kwargs):
    if 'msid' not in r.text:
        error = f"msid missing from response."
        raise GetError(error)
    pattern = re.compile(r'msid=([\w]*)&msname')
    r.msid = pattern.search(r.text).group(1)

def get_token(r, *args, **kwargs):
    if r.is_redirect:
        return r
    if 'token=' not in r.text:
        error = f'token missing from response.'
        raise GetError(error)
    pattern = re.compile(r"url: '([\w\S]*msid)")
    r.url_token = pattern.search(r.text).group(1)
    pattern = re.compile(r'token=([\w]*)&msid')
    r.token = pattern.search(r.text).group(1)

def get_session(r, *args, **kwargs):
    pattern = re.compile(r'Session[\w]*=([\w]*)')
    r.session = pattern.search(r.headers['location']).group(1)
