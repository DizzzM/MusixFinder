import requests


class iTunesTrack:
    def __init__(self, raw_data):
        self.id = raw_data['trackId']
        self.name = raw_data['trackName']
        self.artist = raw_data['artistId']
        self.artist_name = raw_data['artistName']
        self.url = raw_data['trackViewUrl']
        self.genre = raw_data['primaryGenreName']
        self.image = raw_data['artworkUrl100']

    def __repr__(self):
        return f'Id: {self.id}\n' \
               f'Name: {self.name}\n' \
               f'Artist: {self.artist_name}\n' \
               f'URL: {self.url}\n'\
               f'Genre: {self.genre}\n'


class iTunesArtist:
    def __init__(self, raw_data):
        self.id = raw_data['artistId']
        self.name = raw_data['artistName']
        self.url = raw_data['artistLinkUrl']
        self.genre = raw_data['primaryGenreName']

    def __repr__(self):
        return f'Id: {self.id}\n' \
               f'Name: {self.name}\n' \
               f'URL: {self.url}\n'


class iTunesAPI:
    @staticmethod
    def get_tracks(query: str):
        query = query.replace(' ', '+')
        tracks = requests.get(f'https://itunes.apple.com/search?term={query}&entity=musicTrack&limit=50').json()
        return [iTunesTrack(track) for track in tracks['results']]
        
    @staticmethod
    def get_artist(artist_id):
        artist = requests.get(f'https://itunes.apple.com/lookup?id={artist_id}').json()
        return iTunesArtist(artist['results'][0])

    @staticmethod
    def get_artist_albums(artist_id):
        albums = requests.get(f'https://itunes.apple.com/lookup?id={artist_id}&entity=album&attribute=albumTerm').json()
        return [item['collectionId'] for item in albums['results'] if item['wrapperType'] == 'collection']

    @staticmethod
    def get_album_tracks(album_id):
        tracks = requests.get(f'https://itunes.apple.com/lookup?id={album_id}&entity=song&attribute=albumTerm').json()
        return [iTunesTrack(track) for track in tracks['results'] if track['wrapperType'] == 'track']

    def get_artist_tracks(self, artist_id):
        albums = self.get_artist_albums(artist_id)
        tracks = []
        for album in albums:
            album_tracks = self.get_album_tracks(album)
            tracks += album_tracks
        return tracks
    