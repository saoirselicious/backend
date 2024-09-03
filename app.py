import PIL.Image
import Pylette
import math
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from io import BytesIO
from fastai.vision.all import *

app = Flask(__name__)
CORS(app) 

@app.route('/receive-tracks', methods=['POST'])
def receive_tracks():
    print("receive_tracks")
    
    data = request.json
    table_data = []
    #print(data)
    if not data or not isinstance(data, list):
        return jsonify({"error": "Invalid data format"}), 400
    
    for item in data:
        print("________________________________________________________________________________________________________")
        for artist in item['artists']:
          artist_name = artist['name']
        track_name = item['name']
        try:
            images = item.get('album', {}).get('images', [])
            if images:
                image_url = images[0].get('url')
                if not image_url:
                    print("No image URL found.")
                    continue

                response = requests.get(image_url)

                if response.status_code == 200 and response.headers.get('Content-Type') == 'image/jpeg':
                    try:
                        img = PIL.Image.open(BytesIO(response.content)).convert("RGB")

                        # Extract color palette
                        palette = Pylette.extract_colors(BytesIO(response.content), resize=True)
                        colourPercent = 0
                        for color in palette:
                          palette_data = (int(color.rgb[0]), int(color.rgb[1]), int(color.rgb[2]), ) 
                        
                        colourCollection = []
                        
                        for colour in palette:
                            demo = rgb_to_hex(colour.rgb[0], colour.rgb[1], colour.rgb[2])
                            exists, color_name, category = color_in_palette(demo, colours)
                            nearest_color, nearest_name, nearest_category = find_nearest_color(demo, colours)
                            
                            print(colour.rgb)
                            if exists:
                                print(f"Color category: {category}")
                                colourCollection.append(category)
                            else:
                                print(f"Nearest color category: {nearest_category}")
                                colourCollection.append(nearest_category)
                                
                            table_data.append([artist_name, track_name, palette_data, colourCollection])


                    except Exception as e:
                        print(f"Error opening image with PIL: {e}")
                        #print("Image content (truncated):", response.content[:1000])  # Print a snippet of the content for debugging
                else:
                    print(f"Unexpected content type: {response.headers.get('Content-Type')}")
                
            else:
                print("No images found in the item.")
                
        except KeyError as e:
            print(f"Key error: {e} in item: {item}")
        except Exception as e:
            print(f"Error processing item: {e}")
            
    headers = ["Artist Name", "Track Name", "Color Palette", "Colour Group"]
    table_json = [dict(zip(headers, row)) for row in table_data]
    
    # Return the JSON response
    return jsonify({"status": "success", "data": table_json}), 200

def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    length = len(hex_color)
    return tuple(int(hex_color[i:i+length//3], 16) for i in range(0, length, length//3))

def color_in_palette(color_hex, colors_dict):
    # Normalize the color_hex to uppercase to match the dictionary format
    color_hex = color_hex.upper()

    # Check each color category in the dictionary
    for category, color_set in colors_dict.items():
        for color_name, color_value in color_set.items():
            if color_value == color_hex:
                return True, color_name, category

    return False, None, None

def euclidean_distance(rgb1, rgb2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))

def find_nearest_color(target_hex, colors_dict):
    target_rgb = hex_to_rgb(target_hex)
    closest_color = None
    closest_distance = float('inf')
    closest_name = None
    closest_category = None

    for category, color_set in colors_dict.items():
        for color_name, color_value in color_set.items():
            color_rgb = hex_to_rgb(color_value)
            distance = euclidean_distance(target_rgb, color_rgb)
            if distance < closest_distance:
                closest_distance = distance
                closest_color = color_value
                closest_name = color_name
                closest_category = category

    return closest_color, closest_name, closest_category

colours = {
  "Red": {
    "maroon": "#800000",
    "dark red": "#8B0000",
    "brown": "#A52A2A",
    "firebrick": "#B22222",
    "crimson": "#DC143C",
    "red": "#FF0000",
    "tomato": "#FF6347",
    "coral": "#FF7F50",
    "indian red": "#CD5C5C",
    "light coral": "#F08080",
    "dark salmon": "#E9967A",
    "salmon": "#FA8072",
    "light salmon": "#FFA07A",
    "orange red": "#FF4500",
    "dark orange": "#FF8C00",
    "orange": "#FFA500"
  },
  "Yellow": {
    "gold": "#FFD700",
    "dark golden rod": "#B8860B",
    "golden rod": "#DAA520",
    "pale golden rod": "#EEE8AA",
    "dark khaki": "#BDB76B",
    "khaki": "#F0E68C",
    "yellow": "#FFFF00",
    "yellow green": "#9ACD32"
  },
  "Green": {
    "dark olive green": "#556B2F",
    "olive drab": "#6B8E23",
    "lawn green": "#7CFC00",
    "chartreuse": "#7FFF00",
    "green yellow": "#ADFF2F",
    "dark green": "#006400",
    "green": "#008000",
    "forest green": "#228B22",
    "lime": "#00FF00",
    "lime green": "#32CD32",
    "light green": "#90EE90",
    "pale green": "#98FB98",
    "dark sea green": "#8FBC8F",
    "medium spring green": "#00FA9A",
    "spring green": "#00FF7F",
    "sea green": "#2E8B57",
    "medium aqua marine": "#66CDAA",
    "medium sea green": "#3CB371",
    "light sea green": "#20B2AA"
  },
  "Cyan/Aqua": {
    "dark slate gray": "#2F4F4F",
    "teal": "#008080",
    "dark cyan": "#008B8B",
    "aqua": "#00FFFF",
    "cyan": "#00FFFF",
    "light cyan": "#E0FFFF",
    "dark turquoise": "#00CED1",
    "turquoise": "#40E0D0",
    "medium turquoise": "#48D1CC",
    "pale turquoise": "#AFEEEE",
    "aqua marine": "#7FFFD4"
  },
  "Blue": {
    "powder blue": "#B0E0E6",
    "cadet blue": "#5F9EA0",
    "steel blue": "#4682B4",
    "corn flower blue": "#6495ED",
    "deep sky blue": "#00BFFF",
    "dodger blue": "#1E90FF",
    "light blue": "#ADD8E6",
    "sky blue": "#87CEEB",
    "light sky blue": "#87CEFA",
    "midnight blue": "#191970",
    "navy": "#000080",
    "dark blue": "#00008B",
    "medium blue": "#0000CD",
    "blue": "#0000FF",
    "royal blue": "#4169E1",
    "blue violet": "#8A2BE2",
    "indigo": "#4B0082",
    "dark slate blue": "#483D8B",
    "slate blue": "#6A5ACD",
    "medium slate blue": "#7B68EE",
    "medium purple": "#9370DB",
    "dark magenta": "#8B008B",
    "dark violet": "#9400D3",
    "dark orchid": "#9932CC",
    "medium orchid": "#BA55D3",
    "purple": "#800080"
  },
  "Pink": {
    "thistle": "#D8BFD8",
    "plum": "#DDA0DD",
    "violet": "#EE82EE",
    "magenta": "#FF00FF",
    "orchid": "#DA70D6",
    "medium violet red": "#C71585",
    "pale violet red": "#DB7093",
    "deep pink": "#FF1493",
    "hot pink": "#FF69B4",
    "light pink": "#FFB6C1",
    "pink": "#FFC0CB"
  },
  "Brown": {
    "saddle brown": "#8B4513",
    "sienna": "#A0522D",
    "chocolate": "#D2691E",
    "peru": "#CD853F",
    "sandy brown": "#F4A460",
    "burly wood": "#DEB887",
    "tan": "#D2B48C",
    "rosy brown": "#BC8F8F",
    "moccasin": "#FFE4B5",
    "navajo white": "#FFDEAD",
    "peach puff": "#FFDAB9",
    "misty rose": "#FFE4E1",
    "lavender blush": "#FFF0F5",
    "linen": "#FAF0E6",
    "old lace": "#FDF5E6",
    "papaya whip": "#FFEFD5",
    "sea shell": "#FFF5EE",
    "mint cream": "#F5FFFA"
  },
  "Gray": {
    "slate gray": "#708090",
    "light slate gray": "#778899",
    "light steel blue": "#B0C4DE",
    "lavender": "#E6E6FA",
    "floral white": "#FFFAF0",
    "alice blue": "#F0F8FF",
    "ghost white": "#F8F8FF",
    "honeydew": "#F0FFF0",
    "ivory": "#FFFFF0",
    "azure": "#F0FFFF",
    "snow": "#FFFAFA",
    "black": "#000000",
    "dim gray": "#696969",
    "gray": "#808080",
    "dark gray": "#A9A9A9",
    "silver": "#C0C0C0",
    "light gray": "#D3D3D3",
    "gainsboro": "#DCDCDC",
    "white smoke": "#F5F5F5",
    "white": "#FFFFFF"
  }
}

if __name__ == '__main__':
    app.run(debug=True)