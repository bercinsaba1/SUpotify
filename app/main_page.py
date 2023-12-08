from flask import Blueprint, Flask, request, url_for, session, jsonify, redirect
from flask_cors import CORS, cross_origin
from spotipy.oauth2 import SpotifyOAuth 
from sqlalchemy import func, or_, desc
import lyricsgenius as lg
import spotipy
import requests
import time 
import json
from datetime import datetime
from . import db 
from .models import Album, Friendship, RateSong, SongPlaylist, Playlist, Artist, Song, User, RateArtist, RateAlbum
from datetime import datetime

main = Blueprint('main', __name__)

TOKEN_INFO = "token_info" 

token = ""

GENIUS_API_KEY = "ELYRzAgCM0wR2jm42T8YVN3sJZMXH4Yss-hBIERYV4xFp2RJGiRbrfnuQh5gqJfg"


def fetch_and_save_song(sp, song_id):
    
    track_info = sp.track(song_id)
    
    audio_features = sp.audio_features(song_id)[0]
    
    artist = sp.artist(track_info['artists'][0]['id'])
    
    album = sp.album(track_info['album']['id'])
    
    genres = ', '.join(artist['genres'])
    
    new_artist = None
    
    new_album = None
    
    if not Artist.query.filter_by(artist_id=artist['id']).first():
        new_artist = Artist(
            artist_id = artist['id'],
            artist_name = artist['name'],
            picture = artist['images'][0]['url'],
            popularity = artist['popularity'],
            genres = genres,
            followers = artist['followers']['total']
        )
        db.session.add(new_artist)
        
    if not Album.query.filter_by(album_id=album['id']).first():
        new_album = Album(
            album_name = album['name'],
            album_id = album['id'],
            artist_id = artist['id'],
            album_type = album['album_type'],
            image = album['images'][0]['url']
        )
        db.session.add(new_album)
    
    release_year = int(track_info['album']['release_date'][:4])
    
    new_song = Song(
                song_id = track_info['id'],
                artist_id = track_info['artists'][0]['id'],
                album_id = track_info['album']['id'],
                song_name = track_info['name'],
                picture = track_info['album']['images'][0]['url'],
                play_count = 0,
                tempo = audio_features['tempo'],  
                popularity = track_info['popularity'],
                valence = audio_features['valence'],  
                duration = track_info['duration_ms'],
                energy = audio_features['energy'],  
                danceability = audio_features['danceability'],
                genre = genres,
                release_date = release_year,
                date_added = datetime.now(),
                artist = Artist.query.filter_by(artist_id=artist['id']).first() if Artist.query.filter_by(artist_id=artist['id']).first() else new_artist,
                album = Album.query.filter_by(album_id=album['id']).first() if Album.query.filter_by(album_id=album['id']).first() else new_album
            )
    
    db.session.add(new_song)
    db.session.commit()
    

@main.route('/token_add')
@cross_origin()
def token_add():
    global token
    token = session['token_info']['access_token']
    return redirect("https://localhost:3000/main")

#WORKS
@main.route("/lyrics/<artist_name>/<song_name>")
@cross_origin()
def lyrics(artist_name, song_name):
    
    #DB check must be done here
    
    genius = lg.Genius(GENIUS_API_KEY)
    song = genius.search_song(title = song_name, artist = artist_name)
    
    return jsonify(song.lyrics)
    
#WORKS
@main.route('/save_song/<song_id>', methods=['GET', 'POST'])
@cross_origin()
def save_song(song_id):
    if request.method == 'GET':
        
        sp = spotipy.Spotify(auth=token)     
        
        fetch_and_save_song(sp, song_id)
        
        song = Song.query.filter_by(song_id=song_id).first()
        
        return jsonify({
            "name":song.song_name,
            "artist_name":song.artist.artist_name
            })

#WORKS
@main.route('/recommendations/<genre>')
@cross_origin()
def get_recommendations_by_genre(genre):

    sp = spotipy.Spotify(auth=token)
    recommendations = sp.recommendations(seed_genres=[genre], limit=10)
    result = []
    for track in recommendations['tracks']:
        curr_track = {
            'song_id': track['id'],
            'song_name': track['name'],
            'artist_name': [artist['name'] for artist in track['artists']],
            'picture': track['album']['images'][0]['url']
        }
        result.append(curr_track)

    return jsonify(result)

#WORKS
@main.route('/get_song_info/<user_id>/<song_id>') 
@cross_origin()
def get_song_info(user_id, song_id):
    song = Song.query.filter_by(song_id=song_id).first()

    if not song:
        sp = spotipy.Spotify(auth=token) 
        fetch_and_save_song(sp, song_id)
        
    song = Song.query.filter_by(song_id=song_id).first()
    prev_rate = RateSong.query.filter_by(song_id=song_id, user_id=user_id).first()
    artist = Artist.query.filter_by(artist_id=song.artist_id).first()
    
    song_info = {
        'song_id': song.song_id,
        'artists': artist.artist_name,
        'title': song.song_name,
        'thumbnail': song.picture,
        'playCount': song.play_count,
        'popularity': song.popularity,
        'valence': song.valence,
        'duration': song.duration,
        'genre': song.genre,
        'releaseYear': song.release_date,
        'dateAdded': song.date_added,
        'userPrevRating': prev_rate.rating if prev_rate else 0
    }
    return jsonify(song_info)


@main.route('/fill_db/<playlist_id>')
@cross_origin()
def fill_db(playlist_id):
    sp = spotipy.Spotify(auth=token)
    playlist_added = sp.playlist_tracks(playlist_id)
    counter = 0
    for track in playlist_added['items']:
        track_info = track['track']

        existing_track = Song.query.filter_by(song_id=track_info['id']).first()

        if not existing_track:
            fetch_and_save_song(sp, track_info['id'])

        new_rate = RateSong(
            song_id=track_info['id'],
            user_id="bercin",
            rating= counter % 5,
            timestamp = datetime(2023, counter % 12 + 1, 1)
        )
        new_rate2 = RateSong(
            song_id=track_info['id'],
            user_id="arda",
            rating= counter % 5,
            timestamp = datetime(2023, counter % 12 + 1, 1)
        )
        new_rate3 = RateSong(
            song_id=track_info['id'],
            user_id="atakan",
            rating= counter % 5,
            timestamp = datetime(2023, counter % 12 + 1, 1)
        )
        
        new_rate4 = RateSong(
            song_id=track_info['id'],
            user_id="ezgi",
            rating= counter % 5,
            timestamp = datetime(2023, counter % 12 + 1, 1)
        )
        
        db.session.add(new_rate)
        db.session.add(new_rate2)
        db.session.add(new_rate3)
        db.session.add(new_rate4)
        counter += 1
        
    db.session.commit()

    return jsonify({'message': "DB FILLED!"})

#WORKS
@main.route('/get_user_playlists')
@cross_origin()
def get_user_playlists():
    
    sp = spotipy.Spotify(auth=token)
    user_playlists = sp.current_user_playlists()

    formatted_playlists = [
        {
            "name": playlist['name'],
            "playlistPic": playlist['images'][0]['url'] if playlist['images'] else None,
            "songNumber": playlist['tracks']['total'],
            "playlistID": playlist['id']
        }
        for playlist in user_playlists['items']
    ]

    # if playlist exists, update it; else create new
    for playlist_data in formatted_playlists:
        existing_playlist = Playlist.query.filter_by(playlist_id=playlist_data['playlistID']).first()

        if not existing_playlist:
            new_playlist = Playlist(
                playlist_id=playlist_data['playlistID'],
                playlist_name=playlist_data['name'],
                picture=playlist_data["playlistPic"],
                song_number=playlist_data['songNumber']
            )
            db.session.add(new_playlist)
            
    db.session.commit()

    return jsonify(formatted_playlists) 

#WORKS
@main.route('/change_rating_song', methods=['GET', 'POST'])
@cross_origin()
def change_rating_song():
    if request.method == 'POST':
        data = request.get_json()
        prev_rate = RateSong.query.filter_by(song_id=data['song_id'], user_id=data['user_id']).first()
        if ((data['rating'] < 0) or (data['rating'] > 5)):
            return jsonify({'message': False})
        if prev_rate:
            RateSong.query.filter_by(song_id=data['song_id'], user_id=data['user_id']).update({'rating': data['rating'], 'timestamp': datetime.now()})
        else:
            new_rate = RateSong(
                song_id=data['song_id'],
                user_id=data['user_id'],
                rating=data['rating']
            )
            db.session.add(new_rate)
     
        db.session.commit()
        
        return jsonify({'message': True})
    
#WORKS
@main.route('/song_played', methods=['GET', 'POST'])
@cross_origin()
def song_played():
    if request.method == 'POST':
        data = request.get_json()
        song = Song.query.filter_by(song_id=data['song_id']).first()
        if song:
            User.query.filter_by(user_id=data['user_id']).update({'last_sid': song.song_id})
            Song.query.filter_by(song_id=data['song_id']).update({'play_count': song.play_count + 1})
            db.session.commit()
            return jsonify({'message': True})
        else:
            return jsonify({'message': False})
        
#WORKS
@main.route("/get_playlist_info/<user_id>/<playlist_id>")
@cross_origin()
def get_playlist_info(user_id,playlist_id):
    sp = spotipy.Spotify(auth=token)
    playlist_info = sp.playlist(playlist_id)
    song_list = []
 
    for i in range(len(playlist_info['tracks']['items'])):  
        
        s = RateSong.query.filter_by(song_id=playlist_info['tracks']['items'][i]['track']['id']).filter_by(user_id=user_id).first()
        
        song_1 = {
            'song_id' : playlist_info['tracks']['items'][i]['track']['id'],
            'song_name' : playlist_info['tracks']['items'][i]['track']['name'],
            'duration' : playlist_info['tracks']['items'][i]['track']['duration_ms'],
            'release_year' : playlist_info['tracks']['items'][i]['track']['album']['release_date'],
            'artist' : playlist_info['tracks']['items'][i]['track']['artists'][0]['name'],
            'song_rating' : s.rating if s else 0
        }

        song_list.append(song_1) 
    data = {
        'playlistID': playlist_id,
        'playlistName': playlist_info['name'],
        'playlistPicture': playlist_info['images'][0]['url'],
        'songs' : song_list
        }
    
    return jsonify(data)

#WORKS
@main.route("/save_song_with_form", methods=['GET', 'POST'])
@cross_origin()
def save_song_with_form():
    if request.method == 'POST':
        
        data = request.get_json()
        
        artist = Artist.query.filter_by(artist_name=data['artistName']).first()
        
        if not artist:
                
            artist = Artist(
                artist_id = data['artistName'],
                artist_name = data['artistName'],
                picture = "unknown",
                genres = data['songGenre']
            )
            db.session.add(artist)


        new_song = Song(
                song_id = f"{data['artistName']}-{data['songTitle']}",
                artist_id = artist.artist_id,
                album_id = "unknown",
                song_name = data['songTitle'],
                play_count = 0,
                duration = data['songDuration'],
                genre = data['songGenre'],
                release_date = data['songReleaseYear'],
                artist = artist
            )
        
        db.session.add(new_song)
        db.session.commit()
        
        return jsonify({'message': True})
    
#WORKS
@main.route('/<user_id>/90s', methods=['GET'])
@cross_origin()
def get_user_highly_rated_90s_songs(user_id):
    try:
        # Query to get all songs from the 90s
        songs_90s = Song.query.filter(Song.release_date >= 1990, Song.release_date < 2000).all()
        
        # Query to get the user-specific rate for each song
        user_rates = RateSong.query.filter(RateSong.user_id == user_id).all()
        user_rates_dict = {rate.song_id: rate.rating for rate in user_rates}
        
        # Filter songs with user ratings and sort them based on the rating
        sorted_songs = sorted(
            (song for song in songs_90s if song.song_id in user_rates_dict),
            key=lambda song: user_rates_dict[song.song_id],
            reverse=True
        )
        
        # Format the response
        result = {
            'user_id': user_id,
            'highly_rated_90s_songs': [
                {
                    'title': song.song_name,
                    'artist': song.artist.artist_name,
                    'releaseYear': song.release_date,
                    'rate': user_rates_dict[song.song_id]
                }
                for song in sorted_songs
            ]
        }
        return jsonify(result)
    except Exception as e:
        print(e)

#WORKS
@main.route('/<user_id>/all_songs', methods=['GET'])
@cross_origin()
def get_all_songs(user_id):
    try:
        all_songs = Song.query.all()
        
        songs_returned = []
        
        for song in all_songs:
            rate = RateSong.query.filter_by(song_id=song.song_id, user_id=user_id).first()
            
            result = {
                'song_id': song.song_id,
                'artist_name': song.artist.artist_name if song.artist else None,
                'album_name': song.album.album_name if song.album else None,
                'song_name': song.song_name,
                'picture': song.picture,
                'rate': rate.rating if rate else 0,
                'tempo': song.tempo,
                'popularity': song.popularity,
                'valence': song.valence,
                'duration': song.duration,
                'energy': song.energy,
                'danceability': song.danceability,
                'genre': song.genre,
                'release_date': song.release_date,
                'play_count': song.play_count,
                'date_added': song.date_added.isoformat()
            }
            
            songs_returned.append(result)

        return jsonify({'songs': songs_returned})

    except Exception as e:
        return jsonify({'error': str(e)})

#WORKS
@main.route('/<user_id>/new_songs', methods=['GET'])
@cross_origin()
def get_user_new_songs(user_id):
    try:
        # Query to get songs released in the current year (2023)
        current_year_songs = Song.query.filter(Song.release_date == 2023).all()

        if not current_year_songs:
            return jsonify({'error': 'No songs found for the current year.'})

        result = []
        
        for song in current_year_songs:
            rate = RateSong.query.filter_by(song_id=song.song_id, user_id=user_id).first()
            curr_song = {
                'song_id': song.song_id,
                'song_name': song.song_name,
                'artist_name': song.artist.artist_name,
                'release_date': song.release_date,
                'rate': rate.rating if rate else 0
            }
            result.append(curr_song)

        

        return jsonify(result)

    except Exception as e:
        print("DEBUG: Exception:", str(e))
        return jsonify({'error': str(e)})

#WORKS
@main.route('/<user_id>/artist_song_count', methods=['GET'])
@cross_origin()
def artist_song_count(user_id):
    try:
        # Query to get the number of songs for each artist
        artist_song_counts = (
            db.session.query(
                Artist.artist_id,
                Artist.artist_name,
                func.count(Song.song_id).label('song_count')
            )
            .join(Song, Artist.artist_id == Song.artist_id)
            .group_by(Artist.artist_name)
            .order_by(func.count(Song.song_id).desc())  # Order by song count in descending order
            .limit(10)  # Limit the result to the first 10 artists
            .all()
        )
        result = []
        
        for artist_id, artist_name, song_count in artist_song_counts:
            rate = RateArtist.query.filter_by(artist_id=artist_id, user_id=user_id).first()
            curr_artist = {
                'artist_name': artist_name,
                'song_count': song_count,
                'rate': rate.rating if rate else 0
            }
            result.append(curr_artist)
        # Format the response


        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)})

#WORKS
@main.route('/search_item/<user_id>/<search_term>', methods=['GET'])
@cross_origin()
def search_item(user_id, search_term):
    try:
        # Search for songs, albums, artists, and friends in the database based on the search term
        song_results = Song.query.filter(Song.song_name.ilike(f"%{search_term}%")).all()
        album_results = Album.query.filter(Album.album_name.ilike(f"%{search_term}%")).all()
        artist_results = Artist.query.filter(Artist.artist_name.ilike(f"%{search_term}%")).all()
        
        result = {
            'songs': [
                {
                    'song_id': song.song_id,
                    'song_name': song.song_name,
                    'artist_name': song.artist.artist_name,
                    'picture': song.picture,
                    'release_date': song.release_date,
                    'rate': RateSong.query.filter_by(song_id=song.song_id, user_id=user_id).first().rating if RateSong.query.filter_by(song_id=song.song_id, user_id=user_id).first() else 0
                }
                for song in song_results
            ],
            'albums': [
                {
                    'album_id': album.album_id,
                    'album_name': album.album_name,
                    'artist_name': Artist.query.filter_by(artist_id=album.artist_id).first().artist_name,
                    'image': album.image,
                    'rate': RateAlbum.query.filter_by(album_id=album.album_id, user_id=user_id).first().rating if RateAlbum.query.filter_by(album_id=album.album_id, user_id=user_id).first() else 0
                }
                for album in album_results
            ],
            'artists': [
                {
                    'artist_id': artist.artist_id,
                    'picture': artist.picture,
                    'artist_name': artist.artist_name,
                    'popularity': artist.popularity,
                    'rate': RateArtist.query.filter_by(artist_id=artist.artist_id, user_id=user_id).first().rating if RateArtist.query.filter_by(artist_id=artist.artist_id, user_id=user_id).first() else 0,
                }
                for artist in artist_results
            ],
     
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)})
    
@main.route('/save_song_with_json', methods=['POST'])
@cross_origin()
def save_song_with_json():
    try:
        file = request.files['songs.json']
        json_data = file.read()
        data = json.loads(json_data)
        songs = data.get('songs', [])
        
        for song in songs:
            artist = Artist.query.filter_by(artist_name=song['artistName']).first()
            
            if not artist:
                
                artist = Artist(
                    artist_id = data['artistName'],
                    artist_name = data['artistName'],
                    picture = "unknown",
                    genres = data['songGenre']
                )
                db.session.add(artist)


            new_song = Song(
                    song_id = f"{data['artistName']}-{data['songTitle']}",
                    artist_id = artist.artist_id,
                    album_id = "unknown",
                    song_name = data['songTitle'],
                    play_count = 0,
                    duration = data['songDuration'],
                    genre = data['songGenre'],
                    release_date = data['songReleaseYear'],
                    artist = artist
                )
            
            db.session.add(new_song)
            
        db.session.commit()
            
        return jsonify({'message': True})
        
    
    except Exception as e:
        return jsonify({'error': str(e)})
    
#WORKS
@main.route('/change_rating_artist', methods=['GET', 'POST'])
@cross_origin()
def change_rating_artist():
    if request.method == 'POST':
        data = request.get_json()
        prev_rate = RateArtist.query.filter_by(artist_id=data['artist_id'], user_id=data['user_id']).first()
        if ((data['rating'] < 0) or (data['rating'] > 5)):
            return jsonify({'message': False})
        if prev_rate:
            RateArtist.query.filter_by(artist_id=data['artist_id'], user_id=data['user_id']).update({'rating': data['rating'], 'timestamp': datetime.now()})
        else:
            new_rate = RateArtist(
                artist_id=data['artist_id'],
                user_id=data['user_id'],
                rating=data['rating']
            )
            db.session.add(new_rate)
        db.session.commit()
        
        return jsonify({'message': True})
    
#WORKS
@main.route('/change_rating_album', methods=['GET', 'POST'])
@cross_origin()
def change_rating_album():
    if request.method == 'POST':
        data = request.get_json()
        prev_rate = RateAlbum.query.filter_by(album_id=data['album_id'], user_id=data['user_id']).first()
        if ((data['rating'] < 0) or (data['rating'] > 5)):
            return jsonify({'message': False})
        if prev_rate:
            RateAlbum.query.filter_by(album_id=data['album_id'], user_id=data['user_id']).update({'rating': data['rating'], 'timestamp': datetime.now()})
        else:
            new_rate = RateArtist(
                album_id=data['album_id'],
                user_id=data['user_id'],
                rating=data['rating']
            )
            db.session.add(new_rate)
        db.session.commit()
        
        return jsonify({'message': True})
    
@main.route('<current_user_id>/friends_recommendations', methods=['GET'])
def friends_recommendations(current_user_id):
    # Fetch the user's friends with rate_sharing preference
    friends = Friendship.query.filter(
        (Friendship.user1_id == current_user_id) | (Friendship.user2_id == current_user_id)
    ).all()

    # Filter friends based on rate_sharing preference
    friends_allowed_to_share_rate = [friend for friend in friends if friend.rate_sharing == 'public']

    friend_ids = set()
    for friend in friends_allowed_to_share_rate:
        friend_ids.add(friend.user1_id)
        friend_ids.add(friend.user2_id)

    # Fetch the top 20 songs rated by friends who allow rate sharing
    top_rated_songs = (
        RateSong.query.filter(RateSong.user_id.in_(friend_ids))
        .order_by(desc(RateSong.rating))
        .limit(20)
        .all()
    )

    # Get the details of the top-rated songs
    recommendations = []
    for rate_song in top_rated_songs:
        song = Song.query.get(rate_song.song_id)
        recommendations.append({
            'song_name': song.song_name,
            'artist_name': song.artist.artist_name,
            'rating': rate_song.rating,
        })

    return jsonify({'recommendations': recommendations})