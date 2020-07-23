import urllib
import base64
import itertools
import time

from requests import get, post
from flask import Flask, redirect, request

from secrets import SECRET, CLIENT_ID, REDIRECT_URI


SCOPE = 'playlist-modify-private'

AUTHORIZE_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
PROFILE_URL = 'https://api.spotify.com/v1/me'
PLAYLIST_URL = 'https://api.spotify.com/v1/users/{user_id}/playlists'
SEARCH_URL = 'https://api.spotify.com/v1/search?q=artist:{artist}+track:{track}&type=track'
ADD_TRACKS_URL = 'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'

PATH = 'tracks'


def user_headers(token):
    return {'Authorization': f'Bearer {token}'}


def access_token(code):
    auth = base64.b64encode(bytes(f'{CLIENT_ID}:{SECRET}', 'utf8')).decode('utf8')

    data = dict(
        code=code,
        redirect_uri=REDIRECT_URI,
        grant_type='authorization_code'
    )

    headers = {'Authorization': f'Basic {auth}'}

    return post(TOKEN_URL, data=data, headers=headers).json()['access_token']


def user_profile(token):
    return get(PROFILE_URL, headers={'Authorization': f'Bearer {token}'}).json()


def create_playlist(user_id, token):
    data = dict(
        name='vk',
        public=False,
        description='from vk'
    )

    return post(PLAYLIST_URL.format(user_id=user_id), json=data, headers=user_headers(token)).json()


def find_tracks(token):
    with open(PATH) as f:
        for _, line in enumerate(f):
            try:
                artist, track = line.strip().split(' ||| ')

                res = get(SEARCH_URL.format(artist=artist, track=track), headers=user_headers(token)).json()
                tracks = res.get('tracks')

                if tracks:
                    if tracks['total']:
                        yield tracks['items'][0]['uri']
                    else:
                        print(f'{artist} – {track} not found')
                else:
                    print(res)
                    time.sleep(5)
            except Exception as e:
                print(f'error: {e}')


def grouper(n, iterable):
    it = iter(iterable)
    while True:
       chunk = tuple(itertools.islice(it, n))
       if not chunk:
           return
       yield chunk


def add_tracks(token, playlist_id, uris):
    for uris_group in grouper(10, uris):
        post(ADD_TRACKS_URL.format(playlist_id=playlist_id),
             json=dict(uris=uris_group), headers=user_headers(token))


if __name__ == '__main__':
    app = Flask(__name__)

    @app.route('/')
    def index():
        data = dict(
            response_type='code',
            client_id=CLIENT_ID,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
        )

        return redirect(f'{AUTHORIZE_URL}?{urllib.parse.urlencode(data)}')


    @app.route('/callback/')
    def callback():
        code = request.args.get('code')

        try:
            if code:
                token = access_token(code)

                if token:
                    profile = user_profile(token)

                    if profile['id']:
                        playlist = create_playlist(profile['id'], token)

                        if playlist:
                           add_tracks(token, playlist['id'], find_tracks(token))
                           return 'success!'

        except Exception as e:
            f'error: {e}'

        return '¯\_(ツ)_/¯'


    app.run(port=8888, debug=True)
