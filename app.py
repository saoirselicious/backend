import PIL.Image
import Pylette
import math
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from io import BytesIO
from dotenv import load_dotenv
import os


app = Flask(__name__)
CORS(app, resources={r"/*"})

@app.route('/receive-tracks', methods=['POST'])
def receive_tracks():
    print("receive_tracks")
    
    data = request.json
    table_data = []
    if not data or not isinstance(data, list):
        return jsonify({"error": "Invalid data format"}), 400
    
    for item in data:
        print("________________________________________________________________________________________________________")
        artist_name, track_name = None, None
        for artist in item.get('artists', []):
            artist_name = artist['name']
            track_name = item.get('name', 'Unknown Track')
        
        print(artist_name, " ", track_name)
        try:
            images = item.get('album', {}).get('images', [])
            if images:
                image_url = images[0].get('url')
                if not image_url:
                    print("No image URL found.")
                    continue

                response = requests.get(image_url)

                if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                    try:
                        img = PIL.Image.open(BytesIO(response.content)).convert("RGB")

                        # Extract color palette
                        palette = Pylette.extract_colors(BytesIO(response.content), resize=True,  palette_size=10)
                        print(palette.number_of_colors)
                        frequencies = palette.frequencies
                        colourCollection = []
                        palette_data=[]

                        for color in palette:
                            palette_data.append((int(color.rgb[0]), int(color.rgb[1]), int(color.rgb[2])))

                            hex_color = rgb_to_hex(*color.rgb)
                            exists, color_name = color_in_palette(hex_color, colors)

                            if exists:
                                colourCollection.append(color_name)
                            else:
                                nearest_color, nearest_name = find_nearest_color(hex_color, colors)
                                colourCollection.append(nearest_name)

                    except Exception as e:
                        print(f"Error opening image with PIL: {e}")
                else:
                    print(f"Unexpected content type: {response.headers.get('Content-Type')}")
                
            else:
                print("No images found in the item.")
            table_data.append([artist_name, track_name, palette_data, colourCollection, frequencies])        
        except KeyError as e:
            print(f"Key error: {e} in item: {item}")
        except Exception as e:
            print(f"Error processing item: {e}")
        
    headers = ["artist", "track", "palette", "group", "frequency"]
    table_json = [dict(zip(headers, row)) for row in table_data]
    
    return jsonify({"status": "success", "data": table_json}), 200

SPOTIFY_API_URL = 'https://accounts.spotify.com/api/token'

@app.route('/api/spotify/config', methods=['GET'])
def get_spotify_config():
    load_dotenv()
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')
    
    if not client_id or not redirect_uri:
        return jsonify({"error": "Environment variables are not set properly"}), 500

    return jsonify({
        'clientId': client_id,
        'redirectUri': redirect_uri
    })

@app.route('/api/recaptcha/config', methods=['GET'])
def get_recaptcha_config():
    load_dotenv()
    site_key = os.getenv('RECAPTCHA_SITE_KEY')
    secret = os.getenv('RECAPTCHA_SECRET')

    if not site_key or not secret:
        return jsonify({"error": "Environment variables are not set properly"}), 500

    return jsonify({
        'site_key': site_key,
        'secret': secret
    })
    
@app.route('/api/emailjs/config', methods=['GET'])
def get_emailjs_config():
    load_dotenv()
    service_id = os.getenv('EMAILJS_SERVICE_ID')
    public_key = os.getenv('EMAILJS_PUBLIC_KEY')
    private_key = os.getenv('EMAILJS_PRIVATE_KEY')
    template_id = os.getenv('EMAILJS_TEMPLATE_ID')

    if not service_id or not public_key or not private_key or not template_id:
        return jsonify({"error": "Environment variables are not set properly"}), 500

    return jsonify({
        'service_id': service_id,
        'public_key': public_key,
        'private_key': private_key,
        'template_id': template_id
    })

@app.route('/api/spotify/auth', methods=['POST'])
def get_spotify_token():
    load_dotenv()
    code = request.json.get('code')
    print (os.getenv('SPOTIFY_REDIRECT_URI'))
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')
    print ("Got a message")
    
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    print("---------------------")
    print(data)

    response = requests.post(SPOTIFY_API_URL, data=data)
    response_json = response.json()
    print('Spotify API response:', response_json)  # Log the full response
    return jsonify(response_json)

@app.route('/api/spotify/top-tracks', methods=['GET'])
def get_top_tracks():
    auth_header = request.headers.get('Authorization')
    refresh_token = request.headers.get('Refresh-Token')  # Add this header to handle refresh token

    print(f"Authorization header: {auth_header}")

    if not auth_header:
        return jsonify({"error": "Authorization header is missing"}), 400

    parts = auth_header.split(' ')
    print(f"Authorization header parts: {parts}")
    
    if len(parts) != 2 or parts[0] != 'Bearer':
        return jsonify({"error": "Invalid Authorization header format"}), 400
    
    token = parts[1]
    
    try:
        response = requests.get(
            'https://api.spotify.com/v1/me/top/tracks?time_range=long_term&limit=50',
            headers={'Authorization': f'Bearer {token}'}
        )
        print(f"Spotify API response status code: {response.status_code}")
        print(f"Spotify API response body: {response.text}")  # Log the response body

        # Check if token is expired (401 Unauthorized)
        if response.status_code == 401 and refresh_token:
            # Token expired, refresh it
            print("Token expired, refreshing...")
            new_token = refresh_spotify_token(refresh_token)

            if new_token:
                # Retry the request with the new token
                response = requests.get(
                    'https://api.spotify.com/v1/me/top/tracks?time_range=long_term&limit=50',
                    headers={'Authorization': f'Bearer {new_token}'}
                )
                print(f"Retry with new token response status code: {response.status_code}")
                print(f"Retry with new token response body: {response.text}")

        response.raise_for_status()
        return jsonify(response.json())

    except requests.RequestException as e:
        error_message = str(e)
        print(f"Error fetching top tracks: {error_message}")
        return jsonify({"error": error_message}), 500
    
def refresh_spotify_token(refresh_token):
    load_dotenv()
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret
    }

    response = requests.post(SPOTIFY_API_URL, data=data)
    response_json = response.json()

    if 'access_token' in response_json:
        new_token = response_json['access_token']
        return new_token
    else:
        print("Error refreshing token:", response_json)
        return None

def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    length = len(hex_color)
    return tuple(int(hex_color[i:i+length//3], 16) for i in range(0, length, length//3))

def color_in_palette(color_hex, colors_dict):
    color_hex = color_hex.upper()
    if color_hex in colors_dict.values():
        color_name = list(colors_dict.keys())[list(colors_dict.values()).index(color_hex)]
        return True, color_name
    return False, None

def euclidean_distance(rgb1, rgb2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))

def find_nearest_color(target_hex, colors_dict):
    target_rgb = hex_to_rgb(target_hex)
    closest_color = None
    closest_distance = float('inf')
    closest_name = None

    for color_name, color_value in colors_dict.items():
        color_rgb = hex_to_rgb(color_value)
        distance = euclidean_distance(target_rgb, color_rgb)
        if distance < closest_distance:
            closest_distance = distance
            closest_color = color_value
            closest_name = color_name

    return closest_color, closest_name

colors = {
    "Black": "#000000",
    "White": "#FFFFFF",
    "Red": "#FF0000",
    "Lime": "#00FF00",
    "Blue": "#0000FF",
    "Yellow": "#FFFF00",
    "Cyan/Aqua": "#00FFFF",
    "Magenta/Fuchsia": "#FF00FF",
    "Silver": "#C0C0C0",
    "Gray": "#808080",
    "Maroon": "#800000",
    "Olive": "#808000",
    "Green": "#008000",
    "Purple": "#800080",
    "Teal": "#008080",
    "Navy": "#000080"
}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
