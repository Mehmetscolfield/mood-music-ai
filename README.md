🎵 Mood Music Generator

A simple web app that analyzes your mood from a photo and suggests popular Spotify music widgets based on your detected mood and selected language/region.

The backend uses Flask + DeepFace for mood recognition, and the frontend is a clean HTML/CSS/JS interface.

🚀 Features

Upload a photo → backend detects mood (happy, sad, angry, relaxed, etc.).

Choose language/region: English (US), Turkish (TR), Korean (KR), Japanese (JP), Spanish (ES), Arabic (AE).

Returns:

Track cards with cover, artist info, and 30s preview (if available).

Spotify widgets with trending/popular tracks for that mood/language.

Works even without Spotify API keys thanks to static fallbacks.

📂 Project Structure
project/
│── app.py            # Flask backend (mood analysis + Spotify fallback)
│── index.html        # Main frontend HTML
│── styles.css        # Stylesheet
│── app.js            # Frontend logic (fetch, render, audio player)
│── README.md         # Project documentation

⚙️ Installation
1. Clone the repository
git clone https://github.com/yourusername/mood-music-generator.git
cd mood-music-generator

2. Install Python dependencies

Make sure you’re using Python 3.8+.

pip install flask flask-cors requests python-dotenv deepface opencv-python pillow numpy

3. (Optional) Add Spotify API credentials

For dynamic trending music (recommended):

Go to Spotify Developer Dashboard
.

Create an app and copy Client ID and Client Secret.

Create a .env file in your project root:

SPOTIFY_CLIENT_ID=your_id_here
SPOTIFY_CLIENT_SECRET=your_secret_here


Without credentials → static fallback track IDs are used, so widgets still appear.

▶️ Running the App
Backend (Flask)
python app.py


Server starts at http://127.0.0.1:5050.

Frontend

Simply open index.html in your browser.
If your browser blocks API calls from a local file, start a static server in the same folder:

python -m http.server 8000


Then visit http://localhost:8000/index.html.

🖼️ Usage

Open the app in your browser.

Upload a photo (face visible).

Select your language/region.

Click Analyze Mood.

Enjoy Spotify previews and widgets tailored to your mood 🎶.

💡 Notes

If DeepFace fails to detect a face, the app falls back to color analysis.

Widgets are embedded Spotify players; you need a Spotify account (free or premium) to play full tracks.

Works on desktop and mobile (camera upload supported)
