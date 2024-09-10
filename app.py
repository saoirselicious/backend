import PIL.Image
import Pylette
import math
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from io import BytesIO

app = Flask(__name__)
CORS(app) 

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
        
    headers = ["Artist Name", "Track Name", "Color Palette", "Colour Group", "Frequency of Colour"]
    table_json = [dict(zip(headers, row)) for row in table_data]
    
    return jsonify({"status": "success", "data": table_json}), 200

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
