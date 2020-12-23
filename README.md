# Spotify Top 100 Generator 
The following scripts parses through your own playlist(s) and extracts the most popular songs based on popularity data from Spotify and Genius. This includes ranking where the most popular song will be placed on top of the playlist followed by the rest of the songs in the descending popularity. If you want to extract the 100 (or any other number) most popular tracks from your favorite playlist, this script can help you out! A few modifications are needed to make it work in your personal environment.

# Initialization 
The first step necessary is to make an account that links your Spotify account to a developer account. This can be done through the following link: https://developer.spotify.com/dashboard/. This account will provide you with a client id and a client key. Both are necessary to allow the program to run and extract data from your personal Spotify account within the limitations set by Spotify and is needed in the script: extract_and_analyze_data_from_playlist.py. In addition, we also need authorization to actually access and edit our Spotify data when we are adding a playlist and appending tracks to the playlist. To this end, we need a key dedicated to this which can be obtained here: https://developer.spotify.com/console/post-playlists/. 

# Using the program
You will need to fill out some personal Spotify data and edit some parameters to get the script to work. Everything you have to fill in manually, is indicated by double curly brackets like this: {{PARAMETER}}. 

# Help
If you need any further help or assistance while running the code, or if you have feedback, I would love to hear it. Contact me via email: aaronwenteler@gmail.com
