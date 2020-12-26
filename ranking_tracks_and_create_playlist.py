import pandas as pd
import numpy as np
import spotipy
import json
import requests

"""
MADE BY: Aaron Wenteler ( https://github.com/aaronwtr ) ranking_tracks_and_create_playlist_original.py
DATE: 23-12-2020
LICENSE: GNU General Public License. Can be commercially redistributed under explicit mention of original work and 
making public of any additions and/or modifications. Free of charge for personal use. 
"""

CLI_ID = '{{CLIENT ID}}'  # Your client id
CLI_KEY = '{{CLIENT KEY}}'  # Your client key
username = '{{USERNAME}}'  # Your Spotify username


def main():
    global spotify

    token = get_token()
    spotify = spotipy.Spotify(auth=token)

    unranked_playlist = pd.read_csv('unranked_playlist.csv', sep='|')
    unranked_playlist = unranked_playlist.loc[:, ~unranked_playlist.columns.str.contains('^Unnamed')]

    release_dates = []

    for i in range(len(list(unranked_playlist['album']))):
        album = list(unranked_playlist['album'])[i]
        release_dates.append(find_release_date(album))
    unranked_playlist['release_date'] = release_dates

    views = proccessing_views(unranked_playlist)
    unranked_playlist['views'] = views
    rank_factor = calculate_rank(unranked_playlist['popularity'], views, unranked_playlist['release_date'])
    unranked_playlist['rank_factor'] = rank_factor

    ranked_playlist = unranked_playlist.sort_values('rank_factor', ascending=False)
    ranked_playlist.reset_index(drop=True, inplace=True)
    
    ranked_playlist = reduce_artists(ranked_playlist)

    playlist_idd = make_playlist(username, ranked_playlist)

    add_tracks_to_playlist(username, ranked_playlist, playlist_idd)


def get_token():
    """
    Your client ID and client secret key are used to get a token.
    If both your credentials were legitimate, you will get and return a valid token.
    You can get a correct token through: https://developer.spotify.com/console/post-playlists/
    """

    token = '{{TOKEN}}'

    return token


def find_release_date(album):
    """
    This function uses the Spotify Web API in combination with spotipy to obtain the data of the input album that
    corresponds to a particular song. When the album has been found, the release date of the album will be appended to
    be added to the final dataframe.
    """

    album_name = spotify.search(q=album, limit=1, type='album')
    album_name = album_name['albums']
    album_name = album_name['items']
    if not album_name:
        release_date = np.nan
    else:
        release_date = album_name[0]['release_date']

    return release_date


def proccessing_views(playlist):
    """
    In this function, the views which is imported as a string, is converted to a float so that calculations can be
    performed based on the amount of views.
    """

    playlist_raw = playlist.loc[:, ~playlist.columns.str.contains('^Unnamed')]

    views_stripped_floats = list(playlist_raw['views'].replace(r'[KM]+$', '', regex=True).astype(float))

    if np.any(np.isnan(views_stripped_floats)):
        nan_indices = np.argwhere(np.isnan(views_stripped_floats))
        for i in range(len(nan_indices)):
            print('ERROR: Remove " " and , on index ' + str(nan_indices[i]))

    else:
        views_stripped_nonan = list(
            playlist['views'].str.extract(r'[\d\.]+([KM]+)', expand=False).fillna(1).replace(['K', 'M'],
                                                                                             [10 ** 3, 10 ** 6]).astype(
                int))

    views = [int(a * b) for a, b in zip(views_stripped_floats, views_stripped_nonan)]

    return views


def calculate_rank(popularity, views, date_data):
    rank_factor_raw = [a * b for a, b in zip(popularity, views)]

    rank_factor_tempp = []
    rank_factor = []

    for i in range(len(rank_factor_raw)):
        rank_factor_tempp.append(rank_factor_raw[i])

    for track in range(len(rank_factor_raw)):
        rank_factor.append(np.round(
            (rank_factor_tempp[track] - min(rank_factor_tempp)) / (
                    max(rank_factor_tempp) - min(rank_factor_tempp)) * 100, 3))

    return rank_factor


def reduce_artists(playlist, num_songs=6):
    """
    :param playlist: The ranked playlist
    :param artists: All the artists that appear in the playlist
    :param num_songs: The maximum number of songs per artist you want to allow to occur in your playlist
    :return: Playlist that only contains num_songs songs per artist
    """
    ranked_playlist = playlist.loc[:, ~playlist.columns.str.contains('^Unnamed')]

    artists_temp = list(ranked_playlist['artist'])
    artists = []

    for artist in artists_temp:
        if artist not in artists:
            artists.append(artist)

    indices = []

    for artist in artists:
        count = 0
        for i in range(len(artists_temp)):
            if artist == artists_temp[i]:
                count += 1
            if artist == artists_temp[i] and count >= 7:
                indices.append(i)

    indices.sort()

    ranked_playlist = ranked_playlist.drop(ranked_playlist.index[indices])
    ranked_playlist.reset_index(drop=True, inplace=True)

    return ranked_playlist


def make_playlist(user, playlist):
    playlist_name = {{'PLAYLIST_NAME'}}  # Name of your newly created playlist

    description = 'Hip-Hop Top 100 generated in Python with data from Genius and Spotify.'
    spotify.user_playlist_create(user, playlist_name, description=description)

    user_id = "{{USERNAME}}"
    endpoint_url = "https://api.spotify.com/v1/users/" + str(user_id) + "/playlists"
    request_body = json.dumps({
        "name": playlist_name,
        "description": "{{DESCRIPTION}}",
        "public": True
    })
    requests.post(url=endpoint_url, data=request_body, headers={"Content-Type": "application/json",
                                                                "Authorization": get_token()})

    pl = spotify.user_playlists(user)
    pll = dict((k, pl[k]) for k in ['items'] if k in pl)

    playlist_id = pll['items'][0]['id']

    return playlist_id


def add_tracks_to_playlist(playlist, playlist_id):
    track_ids = list(playlist['track_id'])[:100]

    spotify.playlist_add_items(playlist_id, track_ids)

    return print("Check your Spotify app!")


if __name__ == "__main__":
    main()
