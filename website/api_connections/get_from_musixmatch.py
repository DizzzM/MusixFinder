import requests

from parameters import *


def get_lyrics_by_isrc(isrc):
    request = requests.get(f'https://api.musixmatch.com/ws/1.1/track.get?track_isrc={isrc}&apikey={MUSIXMATCH_KEY}').json()
    values = request['message']['body']
    lyrics = values['track']['track_share_url'] if len(values) > 0 else None
    return lyrics
