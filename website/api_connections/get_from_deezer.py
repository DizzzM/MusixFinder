import json

import requests


class DeezerTrack:
    def __init__(self, raw_data):
        self.id = raw_data['id']
        self.name = raw_data['title_short']
        self.artist = raw_data['artist']['id']
        self.artist_name = raw_data['artist']['name']
        self.url = raw_data['link']

    def __repr__(self):
        return f'Id: {self.id}\n' \
               f'Name: {self.name}\n' \
               f'Artist: {self.artist_name}\n' \
               f'URL: {self.url}\n'


class DeezerArtist:
    def __init__(self, raw_data):
        self.id = raw_data['id']
        self.name = raw_data['name']
        self.url = raw_data['link']

    def __repr__(self):
        return f'Id: {self.id}\n' \
               f'Name: {self.name}\n' \
               f'URL: {self.url}\n'


class DeezerAlbum:
    def __init__(self, raw_data):
        self.id = raw_data['id']
        self.name = raw_data['title']
        self.artist = raw_data['artist']
        self.url = raw_data['link']

    def __repr__(self):
        return f'Id: {self.id}\n' \
               f'Name: {self.name}\n' \
               f'Artist: {self.artist}\n' \
               f'URL: {self.url}\n'


class DeezerAPI:
    @staticmethod
    def get_tracks(query: str):
        query = query.replace(' ', '+')
        response = requests.get(f'https://api.deezer.com/search?q={query}&limit=50').content
        result = json.loads(response)
        return [DeezerTrack(track) for track in result['data']]

    @staticmethod
    def get_artist(artist_id):
        response = requests.get(f'https://api.deezer.com/artist/{artist_id}').content
        result = json.loads(response)
        return DeezerArtist(result)

    @staticmethod
    def get_album(album_id):
        response = requests.get(f'https://api.deezer.com/album/{album_id}').content
        result = json.loads(response)
        return DeezerAlbum(result)

    @staticmethod
    def get_artist_albums(artist_id):
        response = requests.get(f'https://api.deezer.com/artist/{artist_id}/albums').content
        result = json.loads(response)
        for album in result['data']:
            album['artist'] = artist_id
        return [DeezerAlbum(album) for album in result['data']]

    @staticmethod
    def get_album_tracks(album_id):
        response = requests.get(f'https://api.deezer.com/album/{album_id}/tracks').content
        result = json.loads(response)
        for track in result['data']:
            track['album'] = {'id': album_id}
        return [DeezerTrack(track) for track in result['data']]

    def get_artist_tracks(self, artist_id):
        albums = self.get_artist_albums(artist_id)
        tracks = []
        for album in albums:
            album_tracks = self.get_album_tracks(album.id)
            tracks += album_tracks
        return tracks
