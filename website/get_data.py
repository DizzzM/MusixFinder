import hashlib
import json
import random
import re
from datetime import date

import plotly
import plotly.express as px
import spacy
from googletrans import Translator
from spacy.language import Language
from spacy_langdetect import LanguageDetector
from sqlalchemy.sql import desc

from website.api_connections.get_from_deezer import DeezerAPI
from website.api_connections.get_from_itunes import iTunesAPI
from website.api_connections.get_from_musixmatch import get_lyrics_by_isrc
from website.api_connections.get_from_spotify import SpotifyAPI
from website.api_connections.get_from_ytmusic import YTMusicAPI
from . import db
from .models import Artist, Track, Query, Favourite, History, Subscription


def get_lang_detector(nlp, name):
    return LanguageDetector()


def tracks_preprocessing(query, tracklist):
    if bool(re.search('[а-яА-Я]', query)):
        translator = Translator()
        model = spacy.load('en_core_web_sm')
        Language.factory('language_detector', func=get_lang_detector)
        model.add_pipe('language_detector', last=True)
        doc = model(query)
        language = doc._.language['language']

        for track_i in tracklist:
            track_i.artist_name = translator.translate(track_i.artist_name, dest=language).text

    return tracklist


def temp_relationship(tracklist):
    track_set = []
    relation = {}
    for i, track in zip(range(len(tracklist)), tracklist):
        track_set.append((track.name.lower(), track.artist_name.lower()))
        relation[track.id] = track_set[i]
    return track_set, relation


def get_id_from_relationship(index, relation):
    for value in relation:
        if relation[value] == index:
            return value
    return None


def get_track_from_api_tracklist(track_id, tracks):
    for x in tracks:
        if x.id == track_id:
            return x
    return None


def get_tracks_from_api(query):
    tracklist = []
    spotify = SpotifyAPI()
    yt = YTMusicAPI()
    itunes = iTunesAPI()
    deezer = DeezerAPI()

    # Get tracks from APIs and translate artists
    spotify_tracks = tracks_preprocessing(query, spotify.get_tracks(query))
    yt_tracks = tracks_preprocessing(query, yt.get_tracks(query))
    itunes_tracks = tracks_preprocessing(query, itunes.get_tracks(query))
    deezer_tracks = tracks_preprocessing(query, deezer.get_tracks(query))

    # find intersection of results
    spotify_set, relation_spotify = temp_relationship(spotify_tracks)
    yt_set, relation_yt = temp_relationship(yt_tracks)
    itunes_set, relation_itunes = temp_relationship(itunes_tracks)
    deezer_set, relation_deezer = temp_relationship(deezer_tracks)
    intersection = set(spotify_set).intersection(set(yt_set)).intersection(set(itunes_set)).intersection(
        set(deezer_set))

    # create tracklist
    for track_i in intersection:

        # Find id of track on platforms
        spotify_id = get_id_from_relationship(track_i, relation_spotify)
        yt_id = get_id_from_relationship(track_i, relation_yt)
        itunes_id = get_id_from_relationship(track_i, relation_itunes)
        deezer_id = get_id_from_relationship(track_i, relation_deezer)

        if spotify_id is None or yt_id is None or itunes_id is None or deezer_id is None:
            continue

        # Find track using ids
        spotify_track = get_track_from_api_tracklist(spotify_id, spotify_tracks)
        yt_track = get_track_from_api_tracklist(yt_id, yt_tracks)
        itunes_track = get_track_from_api_tracklist(itunes_id, itunes_tracks)
        deezer_track = get_track_from_api_tracklist(deezer_id, deezer_tracks)
        if spotify_track is None or yt_track is None or itunes_track is None or deezer_track is None:
            continue
        # Get artist of track
        artist = get_artist(spotify_track.artist, yt_track.artist, itunes_track.artist, deezer_track.artist)

        # Get lyrics url
        lyrics = get_lyrics_by_isrc(spotify_track.isrc)

        # Create Track object
        track = Track(spotify_url=spotify_track.url,
                      yt_url=yt_track.url,
                      itunes_url=itunes_track.url,
                      deezer_url=deezer_track.url,
                      name=spotify_track.name,
                      genre=itunes_track.genre,
                      popularity=int(spotify_track.popularity),
                      image=itunes_track.image,
                      artist_id=artist.artist_id,
                      artist_name=artist.name,
                      lyrics=lyrics,
                      isrc=spotify_track.isrc)

        # Add track to tracklist and to DB if it is not found
        in_table = len(Track.query.filter(Track.isrc == track.isrc).all()) != 0
        if not in_table:
            db.session.add(track)
        tracklist.append(track)

    return tracklist


def get_tracks(query):
    tracklist = []

    # Try to find query in DB
    results = Query.query.filter(Query.value.contains(query)).all()
    if len(results) != 0 and not any(result.date != date.today().strftime("%d/%m/%Y") for result in results):
        # Get tracks from DB by query

        for result in results:
            track = Track.query.filter(Track.isrc == result.result).all()
            tracklist += track
    # If not found, find tracks and add query to DB
    else:
        if len(results) != 0:
            for row in results:
                db.session.delete(row)
        # Try to find tracks in DB
        query_regex = '.*' + ''.join([f'[{letter.lower()}{letter.upper()}]' for letter in query]) + '.*'
        tracklist += Track.query.filter(Track.name.op('regexp')(query_regex)).filter(
            Track.artist_name.op('regexp')(query_regex)).all()

        # If track were not found, find tracks via APIs
        if len(tracklist) == 0:
            tracklist = get_tracks_from_api(query)

        # Add query to DB
        for track in tracklist:
            in_table = len(Query.query.filter(Query.result == track.isrc).all()) != 0
            if not in_table:
                db.session.add(
                    Query(value=query.lower(), result=track.isrc, query_date=date.today().strftime("%d/%m/%Y")))

    db.session.commit()
    tracklist.sort(key=lambda x: x.popularity, reverse=True)
    return tracklist


def get_artist(spotify_id, yt_id, itunes_id, deezer_id):
    hash_value = hashlib.md5()
    hash_value.update(str(spotify_id).encode('utf-8'))
    hash_value.update(str(yt_id).encode('utf-8'))
    hash_value.update(str(itunes_id).encode('utf-8'))
    hash_value.update(str(deezer_id).encode('utf-8'))
    artist_id = hash_value.hexdigest()

    result = Artist.query.filter(Artist.artist_id == artist_id).all()
    if len(result) == 0:
        spotify = SpotifyAPI()
        yt = YTMusicAPI()
        itunes = iTunesAPI()
        deezer = DeezerAPI()
        spotify_artist = spotify.get_artist(spotify_id)
        yt_artist = yt.get_artist(yt_id)
        itunes_artist = itunes.get_artist(itunes_id)
        deezer_artist = deezer.get_artist(deezer_id)

        artist = Artist(artist_id=artist_id,
                        name=deezer_artist.name,
                        image=spotify_artist.image,
                        spotify_id=spotify_artist.id,
                        yt_id=yt_artist.id,
                        itunes_id=itunes_artist.id,
                        deezer_id=deezer_artist.id,
                        genre=itunes_artist.genre)
        db.session.add(artist)
    else:
        artist = result[0]
    return artist


def get_artist_tracks_from_api(artist_id):
    tracklist = []
    spotify = SpotifyAPI()
    yt = YTMusicAPI()
    itunes = iTunesAPI()
    deezer = DeezerAPI()

    # Get artist data from DB
    artist = Artist.query.filter(Artist.artist_id == artist_id).all()[0]

    # Get tracks from APIs. They have the same artist, so no preprocessing needed
    spotify_tracks = spotify.get_artist_tracks(artist.spotify_id)
    yt_tracks = yt.get_artist_tracks(artist.yt_id)
    itunes_tracks = itunes.get_artist_tracks(artist.itunes_id)
    deezer_tracks = deezer.get_artist_tracks(artist.deezer_id)

    # Find intersection of tracks
    spotify_set, relation_spotify = temp_relationship(spotify_tracks)
    yt_set, relation_yt = temp_relationship(yt_tracks)
    itunes_set, relation_itunes = temp_relationship(itunes_tracks)
    deezer_set, relation_deezer = temp_relationship(deezer_tracks)
    intersection = set(spotify_set).intersection(set(yt_set)).intersection(set(itunes_set)).intersection(
        set(deezer_set))

    for track_i in intersection:
        # Find id of track on platforms
        spotify_id = get_id_from_relationship(track_i, relation_spotify)
        yt_id = get_id_from_relationship(track_i, relation_yt)
        itunes_id = get_id_from_relationship(track_i, relation_itunes)
        deezer_id = get_id_from_relationship(track_i, relation_deezer)

        if spotify_id is None or yt_id is None or itunes_id is None or deezer_id is None:
            continue

        # Find track using ids
        spotify_track = get_track_from_api_tracklist(spotify_id, spotify_tracks)
        yt_track = get_track_from_api_tracklist(yt_id, yt_tracks)
        itunes_track = get_track_from_api_tracklist(itunes_id, itunes_tracks)
        deezer_track = get_track_from_api_tracklist(deezer_id, deezer_tracks)
        if spotify_track is None or yt_track is None or itunes_track is None or deezer_track is None:
            continue

        # Get lyrics url
        lyrics = get_lyrics_by_isrc(spotify_track.isrc)

        # Create Track object
        track = Track(spotify_url=spotify_track.url,
                      yt_url=yt_track.url,
                      itunes_url=itunes_track.url,
                      deezer_url=deezer_track.url,
                      name=spotify_track.name,
                      genre=itunes_track.genre,
                      popularity=int(spotify_track.popularity),
                      image=itunes_track.image,
                      artist_id=artist.artist_id,
                      artist_name=artist.name,
                      lyrics=lyrics,
                      isrc=spotify_track.isrc)

        # Add track to tracklist and to DB if it is not found
        in_table = len(Track.query.filter(Track.isrc == track.isrc).all()) != 0
        if not in_table:
            db.session.add(track)
        tracklist.append(track)
    return tracklist


def get_artist_tracks(artist):
    artist_id = artist.artist_id
    # Try to find query in DB
    results = Track.query.filter_by(artist_id=artist_id).all()

    # If not found, find tracks and add to DB
    if len(results) < 10:
        tracklist = get_artist_tracks_from_api(artist_id)
    else:
        # Get tracks from DB by query
        tracklist = results
    db.session.commit()
    tracklist.sort(key=lambda x: x.name, reverse=False)
    return tracklist


def get_random_tracklist():
    tracklist = Track.query.filter(Track.popularity >= 50).order_by(desc(Track.popularity)).all()
    return random.sample(tracklist, min(len(tracklist), 15))


def get_random_track():
    tracklist = Track.query.all()
    return random.choice(tracklist) if len(tracklist) != 0 else None


def get_similar(track: Track, user_id):
    favourites = get_favourites(user_id)
    favourite_artists = set([favourite.artist_id for favourite in favourites])
    favourite_genres = set([favourite.genre for favourite in favourites])

    most_suitable = Track.query.filter(Track.artist_id.in_(list(favourite_artists))).filter(
        Track.genre.in_(list(favourite_genres))).all()
    suitable = Track.query.filter(Track.genre.in_(list(favourite_genres))).all()
    this_artist = Track.query.filter(Track.artist_id == track.artist_id).all()
    tracklist = random.sample(most_suitable, min(len(most_suitable), 5)) + random.sample(suitable, min(len(suitable), 5)) + random.sample(this_artist, min(len(this_artist), 5))
    random.shuffle(tracklist)
    return tracklist


def get_track_info(isrc):
    return Track.query.filter_by(isrc=isrc).first()


def get_artist_info(artist_id):
    return Artist.query.filter_by(artist_id=artist_id).first()


def is_favourite(track_id, user_id):
    is_fav = Favourite.query.filter_by(user_id=user_id, track_id=track_id).first()
    if is_fav is None:
        return False
    else:
        return True


def get_favourites(user_id):
    favourites = Favourite.query.filter_by(user_id=user_id).all()
    tracklist = []
    for favourite in favourites:
        track = Track.query.filter_by(isrc=favourite.track_id).first()
        tracklist.append(track)
    return tracklist


def add_to_favourites(track_id, user_id):
    is_added = Favourite.query.filter_by(user_id=user_id, track_id=track_id).first()
    if is_added is None:
        db.session.add(Favourite(user_id=user_id, track_id=track_id))
        db.session.commit()


def remove_from_favourites(track_id, user_id):
    removed = Favourite.query.filter_by(user_id=user_id, track_id=track_id).first()
    if not (removed is None):
        db.session.delete(removed)
        db.session.commit()


def add_to_history(track_id, user_id):
    in_history = History.query.filter_by(user_id=user_id, track_id=track_id).first()
    if not (in_history is None):
        db.session.delete(in_history)
    db.session.add(History(user_id=user_id, track_id=track_id))
    db.session.commit()


def get_history(user_id):
    history = History.query.filter_by(user_id=user_id).order_by(desc(History.history_id)).all()
    tracklist = []
    for item in history:
        track = Track.query.filter_by(isrc=item.track_id).first()
        tracklist.append(track)
    return tracklist


def subscribe(artist_id, user_id):
    subscribed = Subscription.query.filter_by(artist_id=artist_id, user_id=user_id).first()
    if subscribed is None:
        db.session.add(Subscription(user_id=user_id, artist_id=artist_id))
        db.session.commit()


def unsubscribe(artist_id, user_id):
    unsubscribed = Subscription.query.filter_by(artist_id=artist_id, user_id=user_id).first()
    if not (unsubscribed is None):
        db.session.delete(unsubscribed)
        db.session.commit()


def get_subscriptions(user_id):
    subscriptions = Subscription.query.filter_by(user_id=user_id).all()
    subscriptions_list = []
    for subscription in subscriptions:
        sub = Artist.query.filter_by(artist_id=subscription.artist_id).first()
        subscriptions_list.append(sub)
    return subscriptions_list


def is_subscribed(artist_id, user_id):
    is_sub = Subscription.query.filter_by(user_id=user_id, artist_id=artist_id).first()
    if is_sub is None:
        return False
    else:
        return True


def get_stats(user_id):
    favourites = get_favourites(user_id)
    favourite_artists = [favourite.artist_name for favourite in favourites]
    favourite_genres = [favourite.genre for favourite in favourites]

    genres_plot = get_plot(favourite_genres, 'Genres', 'Count')
    artist_plot = get_plot(favourite_artists, 'Artists', 'Count')
    return genres_plot, artist_plot


def get_plot(data, x, y):
    x_data = list(set(data))
    y_data = [data.count(item) for item in set(data)]
    data_dict = {x: x_data, y: y_data}
    fig = px.bar(data_dict, x=x, y=y)
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
