import os
import base64
import tempfile
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import UploadImageForm
from gradio_client import Client, handle_file
from PIL import Image
import httpx
import logging
import threading
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# A dictionary to store task statuses
task_statuses = {}

def process_image_thread(image_file, task_id):
    temp_file_path = None
    compressed_image_path = None
    try:
        # Save the uploaded image to a temporary file
        temp_file_path = save_temp_file(image_file)
        
        # Compress the image before sending to the API
        compressed_image_path = compress_image(temp_file_path)

        # Your existing image processing code here
        client = Client("https://eswarkarthikk-object-detection.hf.space")
        
        with httpx.Client(timeout=30) as http_client:
            result = client.predict(image=handle_file(compressed_image_path))
        
        if isinstance(result, str) and os.path.isfile(result):
            with open(result, 'rb') as img_file:
                predicted_image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            task_statuses[task_id] = {
                'status': 'completed',
                'result': predicted_image_base64
            }
        else:
            raise ValueError("Unexpected response format from Gradio API")
    
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        task_statuses[task_id] = {
            'status': 'error',
            'message': str(e)
        }
    
    finally:
        # Clean up temporary files
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.error(f"Error removing temp file: {str(e)}")
        
        if compressed_image_path and os.path.exists(compressed_image_path):
            try:
                os.remove(compressed_image_path)
            except Exception as e:
                logger.error(f"Error removing compressed file: {str(e)}")

@csrf_exempt
def upload_image(request):
    if request.method == 'POST':
        form = UploadImageForm(request.POST, request.FILES)
        if form.is_valid():
            image_file = request.FILES['image']
            
            # Generate a unique task ID
            task_id = str(uuid.uuid4())
            
            # Start the processing in a separate thread
            task_statuses[task_id] = {'status': 'processing'}
            thread = threading.Thread(target=process_image_thread, args=(image_file, task_id))
            thread.start()
            
            return JsonResponse({'task_id': task_id})
    else:
        form = UploadImageForm()
    
    return render(request, 'index.html', {'form': form})

def task_status(request, task_id):
    status = task_statuses.get(task_id, {'status': 'not_found'})
    return JsonResponse(status)

# Helper functions
def save_temp_file(image_file):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        for chunk in image_file.chunks():
            temp_file.write(chunk)
        temp_file_path = temp_file.name
    return temp_file_path

def compress_image(temp_file_path):
    # Add your image compression logic here
    compressed_image_path = temp_file_path  # Placeholder, update with actual path
    return compressed_image_path


import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from gradio_client import Client

def predict_fraud(request):
    if request.method == "POST":
        data = json.loads(request.body)

        client = Client("EswarKarthikk/credit_card_fraud_detection")
        result = client.predict(
            amt_income_total=float(data['amt_income_total']),
            amt_credit=float(data['amt_credit']),
            contract_type=data['contract_type'],
            amt_annuity=float(data['amt_annuity']),
            amt_goods_price=float(data['amt_goods_price']),
            hour_appr_process_start=int(data['hour_appr_process_start']),
            name_income_type=data['name_income_type'],
            organization_type=data['organization_type'],
            api_name="/predict_fraud"
        )

        return JsonResponse({'result': result})

    return render(request, 'credit_fraud.html')
