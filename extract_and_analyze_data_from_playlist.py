import spotipy
import spotipy.oauth2 as oauth2
from pprint import pprint
import os
import pandas as pd
import re
import time
from bs4 import BeautifulSoup
from googlesearch import search
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import JavascriptException
from selenium.common.exceptions import TimeoutException
from tqdm import tqdm
from webdriver_manager.chrome import ChromeDriverManager


'''' 
MADE BY: Aaron Wenteler ( https://github.com/aaronwtr ) ranking_tracks_and_create_playlist_original.py
DATE: 23-12-2020
LICENSE: GNU General Public License. Can be commercially redistributed under explicit mention of original work and 
making public of any additions and/or modifications. Free of charge for personal use. 
'''


# client ID and secret key to authorize querying of spotify data through the API
CLI_ID = '{{CLIENT ID}}'  # Your client id
CLI_KEY = '{{CLIENT KEY}}'  # Your client key

csv_headers = ["url", "name", "artist", "track_id", "album", "popularity", "duration_ms"]

# Set this to True if you want to re-analyze previously analyzed track data. Otherwise set False.
OVERWRITE = False


def main():
    global spotify

    # Choose whether you want to export playlist to a txt file, csv file or if you just want to view the playlist
    # data structure or get a random song.
    modes = ["txt", "csv", "show_ds", "nan"]
    mode = modes[1]
    # Dictionary of playlists with their IDs and owner IDs
    playlists_info = {
        "{{PLAYLIST_NAME}}" 	: ["{{PLAYLIST_ID}}", "{{USERNAME}}"],
        }

    playlist = playlists_info['{{PLAYLIST_NAME}}']

    # step 1 - get the token to get authorized by the spotify API
    token = get_token()
    spotify = spotipy.Spotify(auth=token)

    # write playlist contents to file and other playlist-operations
    write_playlist(playlist[1], playlist[0], mode)


def get_token():
    """
    Your client ID and client secret key are used to get a token.
    If both your credentials were legitimate, you will get and return a valid token.

    :return: token
    """
    credentials = oauth2.SpotifyClientCredentials(
        client_id=CLI_ID,
        client_secret=CLI_KEY)
    token = credentials.get_access_token()
    return token


def write_playlist(username, uri, mode):
    """
    Query the spotify API and receive the playlist information. If mode is 'nan' you can view this information data structure in its raw form.
    Obtain the list of tracks from the playlist information data structure and write it to a txt or csv file.
    Select a random song from the list of tracks and print general information to the console.
    """

    playlist_info = spotify.user_playlist(username, uri)  # , fields='tracks,next,name'
    tracks = playlist_info['tracks']
    if mode == 'txt':
        filename = "{0}.txt".format(playlist_info['name'])
        write_txt(username, filename, tracks)
    elif mode == 'csv':
        filename = "{0}.csv".format(playlist_info['name'])
        views = []
        write_csv(filename, tracks, views)
    elif mode == 'show_ds':
        pprint(playlist_info)
    elif mode == 'nan':
        pass
    print("\nNumber of tracks in the selected playlist = {} ".format(tracks['total']))


def write_txt(username, filename, tracks):
    """
    ADD PLAYLIST INFP TO TXT FILE
    View the playlist information data structure if this is confusing!
    Specify the destination file path and check if the file exists already. If the file exists and you selected to not
    overwrite, the program will end here.
    Open the file and read the contents of the file to get the number of songs that are already recorded.
    Seek the file pointer back to the beginning and overwrite the file contents with the track information as required.
    Finally, truncate any extra bytes of the file, if the overwritten portion is less than the original portion.
    Return the original number of songs to the calling function.
    Exceptions handle the cases where the characters in the track info cannot be understood by the system and where
    the key is invalid (usually due to local files in the playlist).
    """

    filepath = "{{FILEPATH_TXT}}".format(filename)
    if os.path.isfile(filepath):
        ex = True
        filemode = 'r+'
        if not OVERWRITE:
            return
        else:
            print("Extracting playlist...")
    else:
        ex = False
        filemode = 'w'
    with open(filepath, filemode) as file:
        # reading number of songs from the file if it exists
        if ex:
            content = file.readlines()
            curr_tot = content[-2][14:]
            curr_tot = curr_tot.strip()     # to remove the trailing newline character
            file.seek(0)
        else:
            curr_tot = None
        # write new songs to the file
        while True:
            for item in tracks['items']:
                if 'track' in item:
                    track = item['track']
                else:
                    track = item
                try:
                    track_url = track['external_urls']['spotify']
                    file.write(
                        "{0:<60} - {1:<90} - {2} \n".format(track_url, track['name'], track['artists'][0]['name']))
                except KeyError:
                    print("Skipping track (LOCAL FILE) - {0} by {1}".format(track['name'], track['artists'][0]['name']))
                except UnicodeEncodeError:
                    print("Skipping track (UNDEFINED CHARACTERS) - {0} by {1}".format(track['name'],
                                                                                      track['artists'][0]['name']))
            # 1 page = 50 results
            # check if there are more pages
            if tracks['next']:
                tracks = spotify.next(tracks)
            else:
                break
        file.write("\n\nTotal Songs - {0}\nUser - {1}".format(tracks['total'], username))
        file.truncate()
    print("Playlist written to file.", end="\n\n")
    print("-----\t\t\t-----\t\t\t-----\n")
    return curr_tot


def write_csv(filename, tracks, views):
    """
    ADD TO CSV FILE
    View the playlist information data structure if this is confusing!
    Specify the destination file path and check if the file exists already. If the file exists and you selected to not
    overwrite, the program will end here. Traverse the tracks data structure and add whatever information you want to
    store to a python list. These are the rows for your csv file Append all of these lists to a main python list which
    will store all the rows for your csv file. Write the data to the csv file! Exceptions handle the cases where the
    characters in the track info cannot be understood by the system and where the key is invalid (usually due to local
    files in the playlist).
    Note that {{FIRST_SONG_INDEX}} and {{LAST_SONG_INDEX}} serve to extract a part of your playlist if you do not want
    to extract your entire playlist for example. If you do want to use your entire playlist, just select all rows, i.e
    just remove {{FIRST_SONG_INDEX}} and {{LAST_SONG_INDEX}} and leave only ':'. Of course selecting, tracks by index
    at which they appear in your playlist is a bit annoying. Therefore I explicitly ask you to check if all the songs
    you expect are present. Entering Y in the terminal allows the program to continue while N allows you to change
    the {{FIRST_SONG_INDEX}} and {{LAST_SONG_INDEX}}.
    """

    filepath = "{{FILEPATH_CSV}}".format(filename)
    playlist_exist = True  # Determine if you want to append data to an existing playlist or create a new one

    tracklist = []
    views = []

    if os.path.isfile(filepath):
        if not OVERWRITE:
            return
        else:
            print("Extracting playlist and finding corresponding Genius URLs...")
    while True:
        for item in tracks['items']:
            if 'track' in item:
                track = item['track']
            else:
                track = item
            if track is None:
                continue
            try:
                track_url = track['external_urls']['spotify']
                # add to list of lists
                track_info = [track_url, track['name'], track['artists'][0]['name'], track['id'], track['album']['name'],
                              track['popularity'], track['duration_ms']]
                tracklist.append(track_info)
            except KeyError:
                print("Skipping track (LOCAL ONLY) - {0} by {1}".format(track['name'], track['artists'][0]['name']))
        if tracks['next']:
            tracks = spotify.next(tracks)
        else:
            break
    unranked_playlist = pd.DataFrame(tracklist[{{'FIRST_SONG_INDEX'}}:{{'LAST_SONG_INDEX'}}], columns=csv_headers)

    print(unranked_playlist['name'])

    check = input('Are all songs accounted for? (Y/N): ')

    if check == 'Y':
        views = scrape_genius(unranked_playlist)

    else:
        print('Rerun the script and alter the playlist bounds')
        exit()

    unranked_playlist['views'] = views
    if playlist_exist:
        unranked_playlist.to_csv('unranked_playlist.csv', mode='a', header=False, sep=';')
    else:
        unranked_playlist.to_csv('unranked_playlist.csv', sep=';')

    return


def scrape_genius(playlist_dataframe):
    views_list = []
    for item in tqdm(range(len(playlist_dataframe))):
        song = playlist_dataframe['name'].iloc[item]
        performer = playlist_dataframe['artist'].iloc[item]

        google_search = str(song) + ' ' + str(performer) + ' lyrics' + ' genius'

        print('\n\nScraping ' + str(song) + ' - ' + str(performer) + '...')

        for result in search(google_search,  # The query you want to run
                        tld='com',  # The top level domain
                        lang='en',  # The language
                        num=1,  # Number of results per page
                        start=0,  # First result to retrieve
                        stop=1,  # Last result to retrieve
                        pause=0.001,  # Lapse between HTTP requests
                        ):
            link = result

            chrome_options = Options()
            chrome_options.add_experimental_option("detach", True)
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")

            driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

            driver.get(link)

            try:
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))).click()

                clickable = driver.find_element_by_xpath("//*[@id='onetrust-accept-btn-handler']")

                time.sleep(1)

                action = ActionChains(driver)

                action.double_click(clickable).perform()

            except (TimeoutError, JavascriptException, TimeoutException):
                pass

            source = driver.page_source
            soup = BeautifulSoup(source, 'lxml')

            try:
                views_temp = soup.find_all("span", class_="LabelWithIcon__Label-sc-1ri57wg-1")
                views = cleanhtml(str(views_temp[1]))
                driver.close()
            except IndexError:
                try:
                    views_temp = list(soup.find_all("span",
                                                    class_="text_label text_label--gray text_label--x_small_text_size"))
                    views = cleanhtml(str(views_temp[0]))
                    driver.close()
                except IndexError:
                    print('No data available on Genius')
                    views = 1
        driver.quit()

        print('\nNumber of views = ' + str(views))
        views_list.append(views)

    return views_list


def cleanhtml(raw_html):
    try:
        cleanr = re.sub("<[^>]*>", "", raw_html)
    except IndexError:
        cleanr = 1
    return cleanr


if __name__ == "__main__":
    main()
