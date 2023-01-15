import base64

import requests



class SpotifyTrack:
    def __init__(self, raw_data):
        self.id = raw_data['id']
        self.name = raw_data['name']
        self.artist = raw_data['artists'][0]['id']
        self.popularity = raw_data['popularity']
        self.url = raw_data['external_urls']['spotify']
        self.artist_name = raw_data['artists'][0]['name']
        self.isrc = raw_data['external_ids']['isrc']

    def __repr__(self):
        return f'Id: {self.id}\n' \
               f'Name: {self.name}\n' \
               f'Artist: {self.artist_name}\n' \
               f'URL: {self.url}\n'


class SpotifyArtist:
    def __init__(self, raw_data):
        self.id = raw_data['id']
        self.name = raw_data['name']
        self.genres = raw_data['genres']
        self.url = raw_data['external_urls']['spotify']
        self.image = raw_data['images'][0]['url']

    def __repr__(self):
        return f'Id: {self.id}\n' \
               f'Name: {self.name}\n' \
               f'Genres: {self.genres}\n' \
               f'URL: {self.url}\n' \
               f'Image: {self.image}\n'


class SpotifyAPI:
    @staticmethod
    def authorization():
        url = "https://accounts.spotify.com/api/token"
        headers = {}
        data = {}
        message = f"{os.getenv('CLIENT_ID')}:{os.getenv('CLIENT_SECRET')}"
        message_bytes = message.encode('ascii')
        base64bytes = base64.b64encode(message_bytes)
        base64message = base64bytes.decode('ascii')
        headers['Authorization'] = f"Basic {base64message}"
        data['grant_type'] = "client_credentials"

        r = requests.post(url, headers=headers, data=data)

        token = r.json()['access_token']
        return token

    def get_tracks(self, query: str):
        token = self.authorization()
        query = query.replace(' ', '%20')
        headers = {"Authorization": "Bearer " + token}
        tracks = requests.get(url=f'https://api.spotify.com/v1/search?q={query}&type=track&limit=50',
                              headers=headers).json()

        return [SpotifyTrack(track) for track in tracks['tracks']['items']]

    def get_artist(self, artist_id):
        token = self.authorization()
        headers = {"Authorization": "Bearer " + token}
        artist = requests.get(url=f'https://api.spotify.com/v1/artists/{artist_id}',
                              headers=headers).json()
        return SpotifyArtist(artist)

    def get_album_tracks(self, album_id):
        token = self.authorization()
        headers = {"Authorization": "Bearer " + token}
        tracks_id = requests.get(url=f'https://api.spotify.com/v1/albums/{album_id}/tracks?limit=50',
                                 headers=headers).json()
        tracks = []
        for track_id in tracks_id['items']:
            track = requests.get(url=f'https://api.spotify.com/v1/tracks/{track_id["id"]}', headers=headers).json()
            track['id'] = track_id['id']
            tracks.append(track)
        return [SpotifyTrack(track) for track in tracks if len(track) == 17]

    def get_artist_albums(self, artist_id):
        token = self.authorization()
        headers = {"Authorization": "Bearer " + token}
        albums = requests.get(url=f'https://api.spotify.com/v1/artists/{artist_id}/albums?limit=50',
                              headers=headers).json()
        return [album['id'] for album in albums['items']]

    def get_artist_tracks(self, artist_id):
        albums = self.get_artist_albums(artist_id)
        tracks = []
        for album in albums:
            album_tracks = self.get_album_tracks(album)
            tracks += album_tracks
        return tracks
