import io
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from PIL import Image

app = Flask(__name__)
CORS(app) 

GEMINI_API_KEY = "AIzaSyCnZDrpo9WNYCBwaIERVVtrSgDfwx15Vo8"
MAX_IMAGE_UPLOAD_SIZE = 1080

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    print("Gemini AI Ready! Waiting for the website to send images...")
except Exception as e:
    print(f"[ERROR] Failed to set up Gemini: {e}")

@app.route('/process_image', methods=['POST'])
def process_image():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Extract image or list of images from the request
        image_list = data.get('images', [])
        if not image_list and 'image' in data:
            image_list = [data['image']]

        if not image_list:
            return jsonify({'error': 'No images provided'}), 400

        # Enforce the limit to take only 2 images
        images_to_process = image_list[:2]
        processed_pil_images = []

        for image_data in images_to_process:
            if ',' in image_data:
                image_data = image_data.split(',')[1]
                
            image_bytes = base64.b64decode(image_data)
            pil_image = Image.open(io.BytesIO(image_bytes))

            img_w, img_h = pil_image.size
            largest_dim = max(img_w, img_h)
            if largest_dim > MAX_IMAGE_UPLOAD_SIZE:
                scale = MAX_IMAGE_UPLOAD_SIZE / largest_dim
                new_w = int(img_w * scale)
                new_h = int(img_h * scale)
                pil_image = pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            processed_pil_images.append(pil_image)

        prompt = "Extract all readable text from these images. Output ONLY the exact text. If no text, output nothing."
        response = model.generate_content([prompt] + processed_pil_images)
        
        response_text = ""
        try:
            if response.text:
                response_text = " ".join(response.text.split()).strip()
        except ValueError:
            pass 

        print(f"[Sent to Website]: {response_text if response_text else '(No text found)'}")
        return jsonify({'text': response_text})

    except Exception as e:
        print(f"[ERROR] processing image: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Vision Reader Backend...")
    print("Running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)