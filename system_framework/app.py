import os
import logging
from flask import Flask, request, jsonify
from PIL import Image
import io
import torch
from diffusers import StableDiffusionPipeline
from transformers import CLIPTextModel, CLIPTokenizer

# Configure logging
logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load the pre-trained Stable Diffusion model
model_id = "CompVis/stable-diffusion-v1-4"
device = "cuda" if torch.cuda.is_available() else "cpu"

logger.info(f"Using device: {device}")

pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16 if device == "cuda" else torch.float32)
pipe = pipe.to(device)

logger.info("Stable Diffusion model loaded successfully")

def generate_image_standalone(prompt, style='default'):
    logger.info(f"Generating image with prompt: '{prompt}' and style: '{style}'")

    full_prompt = f"{prompt} in {style} style"
    logger.info(f"Full prompt: {full_prompt}")

    try:
        logger.info("Starting image generation")
        with torch.no_grad():
            image = pipe(full_prompt).images[0]
        logger.info("Image generation completed successfully")
    except Exception as e:
        logger.error(f"Error during image generation: {str(e)}")
        return None, str(e)

    try:
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        logger.info("Image converted to bytes successfully")
    except Exception as e:
        logger.error(f"Error converting image to bytes: {str(e)}")
        return None, "Error converting image"

    return img_byte_arr, None

@app.route('/generate_image', methods=['POST'])
def generate_image():
    logger.info("Received request to generate image")
    data = request.json
    prompt = data.get('prompt', '')
    style = data.get('style', 'default')

    img_byte_arr, error = generate_image_standalone(prompt, style)

    if error:
        return jsonify({'status': 'error', 'message': error}), 500

    logger.info("Returning generated image")
    return jsonify({
        'status': 'success',
        'image': img_byte_arr.decode('latin-1')
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

# For standalone testing
if __name__ == '__main__':
    test_prompt = "A beautiful sunset over the ocean"
    test_style = "watercolor"
    img_bytes, error = generate_image_standalone(test_prompt, test_style)
    if error:
        print(f"Error: {error}")
    else:
        print("Image generated successfully")
        # You can save the image or process it further here
        with open("test_image.png", "wb") as f:
            f.write(img_bytes)
        print("Test image saved as 'test_image.png'")
