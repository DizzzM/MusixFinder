from ytmusicapi import YTMusic


class YTMusicTrack:
    def __init__(self, raw_data):
        self.id = raw_data['videoId']
        self.name = raw_data['title']
        self.artist = raw_data['artists'][0]['id']
        self.artist_name = raw_data['artists'][0]['name']
        self.url = f'https://www.youtube.com/watch?v={self.id}'

    def __repr__(self):
        return f'Id: {self.id}\n' \
               f'Name: {self.name}\n' \
               f'Artist: {self.artist_name}\n' \
               f'URL: {self.url}\n'


class YTMusicArtist:
    def __init__(self, raw_data):
        self.id = raw_data['id']
        self.name = raw_data['name']
        self.url = f'https://www.youtube.com/channel/{raw_data["channelId"]}'

    def __repr__(self):
        return f'Id: {self.id}\n' \
               f'Name: {self.name}\n' \
               f'URL: {self.url}\n'


class YTMusicAPI:
    @staticmethod
    def get_tracks(track_name):
        yt = YTMusic()
        tracks = yt.search(query=track_name, filter='songs', limit=50)
        return [YTMusicTrack(track) for track in tracks if track['artists'][0]['id'] is not None]

    @staticmethod
    def get_artist(artist_id):
        yt = YTMusic()
        artist = yt.get_artist(artist_id)
        artist['id'] = artist_id
        return YTMusicArtist(artist)

    @staticmethod
    def get_artist_albums(artist_id):
        yt = YTMusic()
        artist = yt.get_artist(artist_id)
        albums = artist['albums']['results']
        # albums = yt.get_artist_albums(artist_id, artist['albums']['params'])
        return [album['browseId'] for album in albums]

    @staticmethod
    def get_album_tracks(album_id):
        yt = YTMusic()
        album = yt.get_album(album_id)
        return [YTMusicTrack(track) for track in album['tracks'] if track['artists'][0]['id'] is not None]

    def get_artist_tracks(self, artist_id):
        albums = self.get_artist_albums(artist_id)
        tracks = []
        for album in albums:
            album_tracks = self.get_album_tracks(album)
            tracks += album_tracks
        return tracks
