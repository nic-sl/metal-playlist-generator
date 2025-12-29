# Metal Playlist Generator 🤘

A FastAPI-powered web application that helps you discover new metal music and automatically generate Spotify playlists.

![](https://i.imgur.com/4KqIWEF.png)

## Features

- **Genre-Based Discovery**: Filter the playlist creation with your preferred metal subgenres (or none at all).
- **Random Band Discovery**: Uses the [Metal Map API](https://api.metal-map.com/) to find bands matching your criteria.
- **Spotify Integration**: Verifies artist availability on Spotify and fetches their top tracks.
- **Automated Playlist Creation**: Automatically creates a new playlist in your Spotify account with the discovered tracks.
- **Real-time Progress**: Watch the generation process in real-time through an integrated log viewer.

## Prerequisites

- Python 3.12 or higher.
- A [Spotify Developer Account](https://developer.spotify.com/dashboard/) to create an application and get API credentials.
- uv for dependency management.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/metal-playlist-generator.git
   cd metal-playlist-generator
   ```

2. **Install dependencies**:
   Using `uv`:
   ```bash
   uv sync
   ```

## Spotify App Setup
1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
2. Create a new App.
3. In the App settings, add `http://127.0.0.1:8000/callback` to the **Redirect URIs** list.
4. Copy the Client ID and Client Secret from the App's settings.

## Configuration

Create a `.env` file in the root directory with the following variables:

```env
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

## Running the Application

Start the server using `uvicorn`:

```bash
uv run uvicorn main:app --reload
```

The application will be available at `http://127.0.0.1:8000`.

## Usage

1. Open your browser and navigate to `http://127.0.0.1:8000`.
2. Click **Login with Spotify** to authorize the application.
3. Once redirected back to the generator page:
   - Select the **genres** you want to include.
   - Set the **number of artists** to discover.
   - Set the **number of tracks** to pick from each artist.
4. Click **Generate Playlist**.
5. Check out your new playlist in Spotify!

## Notes

- Spotify's search API is based on a weighted ranking system that may not always return the best results. I tried to overcome this by exactly matching the artist's name, but it's not perfect.