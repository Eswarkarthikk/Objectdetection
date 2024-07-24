import os
import shutil
import base64
import tempfile
from django.shortcuts import render
from django.http import HttpResponseServerError
from .forms import UploadImageForm
from gradio_client import Client, handle_file
from PIL import Image
import httpx

# Initialize the Gradio client with the correct endpoint URL


def compress_image(image_file, max_size_bytes=2 * 1024 * 1024):
    """Compress image to fit within the specified byte size."""
    img = Image.open(image_file)
    
    # Calculate the current file size
    original_size = os.path.getsize(image_file)
    
    # If already within the limit, return the original file
    if original_size <= max_size_bytes:
        return image_file
    
    # Calculate the compression ratio
    ratio = (max_size_bytes / float(original_size)) ** 0.5
    
    # Resize the image
    img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
    
    # Save the image to a temporary buffer
    buffer = tempfile.NamedTemporaryFile(delete=False)
    img.save(buffer, format='JPEG', quality=85)
    buffer.close()
    
    return buffer.name

def upload_image(request):
    if request.method == 'POST':
        form = UploadImageForm(request.POST, request.FILES)
        client = Client("https://eswarkarthikk-object-detection.hf.space")
        if form.is_valid():
            try:
                # Get the uploaded image file
                image_file = request.FILES['image']

                # Save the uploaded image to a temporary file
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    for chunk in image_file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name

                # Compress the image before sending to the API
                compressed_image_path = compress_image(temp_file_path)

                # Convert the original image to base64
                with open(temp_file_path, 'rb') as img_file:
                    original_image_base64 = base64.b64encode(img_file.read()).decode('utf-8')

                # Example using gradio_client to predict with local file
                with httpx.Client(timeout=50) as http_client:  # Set a longer timeout if needed
                    result = client.predict(image=handle_file(compressed_image_path))

                # Check if the result is a file path
                if isinstance(result, str) and os.path.isfile(result):
                    # Read the predicted image and convert to base64
                    with open(result, 'rb') as img_file:
                        predicted_image_base64 = base64.b64encode(img_file.read()).decode('utf-8')

                    # Pass the base64 encoded images to the template
                    return render(request, 'index.html', {
                        'original_image_base64': f"data:image/jpeg;base64,{original_image_base64}",
                        'predicted_image_base64': f"data:image/jpeg;base64,{predicted_image_base64}"
                    })
                else:
                    raise ValueError("Unexpected response format from Gradio API")

            except Exception as e:
                return HttpResponseServerError(f"Error: {str(e)}")

            finally:
                # Clean up the temporary files
                if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                if 'compressed_image_path' in locals() and os.path.exists(compressed_image_path):
                    os.remove(compressed_image_path)

    else:
        form = UploadImageForm()

    return render(request, 'index.html', {'form': form})