import os
import shutil
import base64
import tempfile
from django.shortcuts import render
from django.http import HttpResponseServerError
from .forms import UploadImageForm
from gradio_client import Client, handle_file
from PIL import Image

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
    
    # Save the image to a temporary file
    buffer = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    img.save(buffer, format='JPEG', quality=85)
    buffer.close()
    
    return buffer.name

def upload_image(request):
    if request.method == 'POST':
        client = Client("https://eswarkarthikk-object-detection.hf.space")
        form = UploadImageForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Create a temporary directory
                temp_dir = tempfile.mkdtemp()

                # Clear any existing files in the temporary directory
                for filename in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print(f"Failed to delete {file_path}. Reason: {e}")

                # Get the uploaded image file
                image_file = request.FILES['image']

                # Save the uploaded image to a temporary file
                temp_file_path = os.path.join(temp_dir, 'uploaded_image.jpg')
                with open(temp_file_path, 'wb') as temp_file:
                    for chunk in image_file.chunks():
                        temp_file.write(chunk)

                # Compress the image before sending to the API
                compressed_image_path = compress_image(temp_file_path)

                # Convert the original image to base64
                with open(temp_file_path, 'rb') as img_file:
                    original_image_base64 = base64.b64encode(img_file.read()).decode('utf-8')

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
                # Clean up the temporary directory
                shutil.rmtree(temp_dir, ignore_errors=True)

    else:
        form = UploadImageForm()

    return render(request, 'index.html', {'form': form})