from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from . import db


class User(db.Model, UserMixin):
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)

    def __init__(self, email, password):
        self.email = email
        self.password = password

    def get_id(self):
        return self.user_id

    @staticmethod
    def validate_email(email):
        existing_user = User.query.filter_by(email=email).first()
        return existing_user is None

    @staticmethod
    def create_new_user(email, password):
        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

    @staticmethod
    def check_login(email, password):
        existing_user = User.query.filter_by(email=email).first()
        if existing_user is None:
            return False
        if check_password_hash(existing_user.password, password):
            return existing_user
        else:
            return False


class Favourite(db.Model):
    favourite_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    track_id = db.Column(db.String, nullable=False)


class History(db.Model):
    history_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    track_id = db.Column(db.String, db.ForeignKey('track.isrc'), nullable=False)


class Subscription(db.Model):
    subscription_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    artist_id = db.Column(db.String, db.ForeignKey('artist.artist_id'), nullable=False)


class Artist(db.Model):
    artist_id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    genre = db.Column(db.String)
    image = db.Column(db.String)
    spotify_id = db.Column(db.String)
    yt_id = db.Column(db.String)
    itunes_id = db.Column(db.String)
    deezer_id = db.Column(db.String)

    def __init__(self, artist_id, spotify_id, yt_id, itunes_id, deezer_id, name, image, genre):
        self.artist_id = artist_id
        self.spotify_id = spotify_id
        self.yt_id = yt_id
        self.itunes_id = itunes_id
        self.deezer_id = deezer_id
        self.name = name
        self.genre = genre
        self.image = image


class Track(db.Model):
    isrc = db.Column(db.String, primary_key=True)
    spotify_url = db.Column(db.String)
    yt_url = db.Column(db.String)
    itunes_url = db.Column(db.String)
    deezer_url = db.Column(db.String)
    name = db.Column(db.String)
    artist_id = db.Column(db.String, db.ForeignKey('artist.artist_id'))
    artist_name = db.Column(db.String)
    genre = db.Column(db.String)
    image = db.Column(db.String)
    popularity = db.Column(db.Integer)
    lyrics = db.Column(db.String)

    def __init__(self, spotify_url, yt_url, itunes_url, deezer_url, name, artist_id, genre, popularity, image,
                 lyrics, artist_name, isrc):
        self.isrc = str(isrc)
        self.spotify_url = str(spotify_url)
        self.yt_url = str(yt_url)
        self.itunes_url = str(itunes_url)
        self.deezer_url = str(deezer_url)
        self.name = str(name)
        self.artist_id = str(artist_id)
        self.artist_name = str(artist_name)
        self.genre = str(genre)
        self.image = str(image)
        self.popularity = int(popularity)
        self.lyrics = str(lyrics)


class Query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String)
    result = db.Column(db.String, db.ForeignKey('track.isrc'))
    date = db.Column(db.String)

    def __init__(self, value, result, query_date):
        self.value = value
        self.result = result
        self.date = query_date
