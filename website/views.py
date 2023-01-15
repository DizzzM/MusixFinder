from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

from .get_data import *

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
def home():
    user = current_user
    if request.method == 'POST':
        query = request.form['query']
        return redirect(url_for('views.search') + f'?query={query}')

    tracklist = get_random_tracklist()
    return render_template('playlist_of_the_day.html', user=user, tracklist=tracklist)


@views.route('/search', methods=['GET', 'POST'])
def search():
    user = current_user
    query = request.args['query']
    tracklist = get_tracks(query)
    return render_template('playlist_of_the_day.html', user=user, tracklist=tracklist)


@views.route('/random', methods=['GET'])
def random():
    user = current_user

    if request.method == 'POST':
        query = request.form['query']
        return redirect(url_for('views.search') + f'?query={query}')

    track = get_random_track()
    if user.is_authenticated:
        is_fav = f'{is_favourite(track.isrc, user.user_id)}'.lower()
    else:
        is_fav = 'false'
    return redirect(url_for('views.track_info') + f'?isrc={track.isrc}&favourite={is_fav}')


@views.route('/track', methods=['GET', 'POST'])
def track_info():
    user = current_user

    if request.method == 'POST':
        query = request.form['query']
        return redirect(url_for('views.search') + f'?query={query}')

    isrc = request.args['isrc']
    track = get_track_info(isrc)
    tracklist = get_random_tracklist()
    fav = request.args.get('favourite')
    if user.is_authenticated:
        tracklist = get_similar(track, user.user_id)

        is_fav = f'{is_favourite(isrc, user.user_id)}'.lower()

        add_to_history(isrc, user.user_id)

        if fav is None:
            fav = is_fav

        if is_fav == fav:
            return render_template('track.html', user=user, track=track, is_fav=fav, tracklist=tracklist)
        else:
            if fav == 'true':
                add_to_favourites(isrc, user.user_id)
            else:
                remove_from_favourites(isrc, user.user_id)

            return render_template('track.html', user=user, track=track, is_fav=fav, tracklist=tracklist)
    else:
        if fav is None or fav == "false":
            return render_template('track.html', user=user, track=track, is_fav='false', tracklist=tracklist)
        else:
            return redirect(url_for('auth.login'))


@views.route('/artist', methods=['GET', 'POST'])
def artist_info():
    user = current_user

    if request.method == 'POST':
        query = request.form['query']
        return redirect(url_for('views.search') + f'?query={query}')
    
    artist_id = request.args['id']
    artist = get_artist_info(artist_id)
    tracklist = get_artist_tracks(artist)

    sub = request.args.get('subscribed')

    if user.is_authenticated:
        is_sub = f'{is_subscribed(artist_id, user.user_id)}'.lower()

        if sub is None:
            sub = is_sub

        if is_sub == sub:
            return render_template('artist.html', user=user, artist=artist, is_sub=sub, tracklist=tracklist)
        else:
            if sub == 'true':
                subscribe(artist_id, user.user_id)
            else:
                unsubscribe(artist_id, user.user_id)

            return render_template('artist.html', user=user, artist=artist, is_sub=sub, tracklist=tracklist)
    else:
        if sub is None or sub == "false":
            return render_template('artist.html', user=user, artist=artist, is_sub='false', tracklist=tracklist)
        else:
            return redirect(url_for('auth.login'))


@views.route('/favourites', methods=['GET', 'POST'])
@login_required
def favourites():
    user = current_user

    if request.method == 'POST':
        query = request.form['query']
        return redirect(url_for('views.search') + f'?query={query}')

    tracklist = get_favourites(user.user_id)
    return render_template('favourites.html', user=user, tracklist=tracklist)


@views.route('/stats', methods=['GET', 'POST'])
@login_required
def stats():
    user = current_user

    if request.method == 'POST':
        query = request.form['query']
        return redirect(url_for('views.search') + f'?query={query}')

    genres_plot, artists_plot = get_stats(user.user_id)
    return render_template('stats.html', user=user, genres_plot=genres_plot, artists_plot=artists_plot)


@views.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user

    if request.method == 'POST':
        query = request.form['query']
        return redirect(url_for('views.search') + f'?query={query}')

    tracklist = get_history(user.user_id)
    subscriptions = get_subscriptions(user.user_id)

    return render_template('user.html', user=user, tracklist=tracklist, subscriptions=subscriptions)
