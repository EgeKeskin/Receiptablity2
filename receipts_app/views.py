import os
import json
import pytesseract
from openai import OpenAI
from PIL import Image
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv

from receipts_app.models import Receipt
from receipts_app.serializers import ReceiptSerializer

# Load environment variables and initialize OpenAI client.
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@login_required(login_url='/login/')
def upload_receipt_view(request):
    """
    Renders a receipt upload form (GET) and processes the uploaded image (POST).
    Calls the OCR and ChatGPT helper to extract receipt data,
    saves the Receipt via the serializer, and then redirects to the corresponding receipt room.
    """
    context = {}
    
    if request.method == 'POST':
        receipt_image = request.FILES.get('receipt_image')
        if not receipt_image:
            context['error'] = "No image file provided."
            return render(request, 'upload_receipt.html', context)
        
        try:
            # Open the image using Pillow.
            image = Image.open(receipt_image)
        except Exception:
            context['error'] = "Invalid image file."
            return render(request, 'upload_receipt.html', context)
        
        # Extract text using pytesseract.
        extracted_text = pytesseract.image_to_string(image)
        print("Extracted Text:", extracted_text)  # Debug log
        
        # Call helper function to get structured JSON from ChatGPT.
        try:
            receipt_data = get_json_from_chatgpt(extracted_text)
            print("Parsed Receipt Data from ChatGPT:", receipt_data)  # Debug log
        except Exception as e:
            context['error'] = f"Error processing OCR text: {str(e)}"
            return render(request, 'upload_receipt.html', context)
        
        # Validate and save the receipt data using the serializer.
        serializer = ReceiptSerializer(data=receipt_data)
        if serializer.is_valid():
            receipt = serializer.save()
            # Redirect to the receipt room page for the created receipt.
            return redirect('receipt_room', receipt_id=receipt.id)
        else:
            context['error'] = serializer.errors
            return render(request, 'upload_receipt.html', context)
    
    # GET request: render the upload form.
    return render(request, 'upload_receipt.html', context)


def get_json_from_chatgpt(ocr_text):
    """
    Calls OpenAI's ChatCompletion to convert OCR text into structured JSON.
    Expects ChatGPT to return JSON with keys like 'name', 'total_cost', 'taxes', 'tip', and 'items'.
    Returns a Python dictionary with the parsed receipt data.
    """
    prompt = (
        "Extract the receipt information from the following text and output valid JSON with exactly these keys: "
        "'name' (string), 'total_cost' (string or number), and 'items' (an array of objects, each having 'item_name' and 'item_cost'). "
        "Also include 'taxes' and 'tip' as optional keys if available. "
        "Output only JSON with no extra commentary.\n\n"
        f"Text:\n{ocr_text}"
    )
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that converts OCR text into structured JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
    )
    
    message_content = response.choices[0].message.content.strip()
    try:
        receipt_data = json.loads(message_content)
    except json.JSONDecodeError:
        raise ValueError("ChatGPT did not return valid JSON. Response was: " + message_content)
    
    return receipt_data


def receipt_room_view(request, receipt_id):
    """
    Retrieves the Receipt by its UUID and renders a page showing all receipt details and related items.
    This page is accessible to anyone with the correct URL.
    """
    receipt = get_object_or_404(Receipt, id=receipt_id)
    return render(request, 'receipt_room.html', {'receipt': receipt})
