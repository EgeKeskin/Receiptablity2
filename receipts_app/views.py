import os
import json
import pytesseract
from openai import OpenAI
from PIL import Image
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv

from receipts_app.models import Receipt
from receipts_app.serializers import ReceiptSerializer

# Load environment variables and create an OpenAI client.
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@login_required(login_url='/login/')
def upload_receipt_view(request):
    """
    Renders a receipt upload form (GET) and processes the uploaded image (POST).
    Calls the OCR and ChatGPT helper to extract receipt data,
    saves the Receipt via the serializer, and renders a template with receipt details.
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
        except Exception as e:
            context['error'] = "Invalid image file."
            return render(request, 'upload_receipt.html', context)
        
        # Extract text using pytesseract.
        extracted_text = pytesseract.image_to_string(image)
        print("Extracted Text:", extracted_text)  # Debug
        
        # Call the helper function to get structured JSON from ChatGPT.
        try:
            receipt_data = get_json_from_chatgpt(extracted_text)
            print("Parsed Receipt Data from ChatGPT:", receipt_data)  # Debug
        except Exception as e:
            context['error'] = f"Error processing OCR text: {str(e)}"
            return render(request, 'upload_receipt.html', context)
        
        # Validate and save the receipt data using the serializer.
        serializer = ReceiptSerializer(data=receipt_data)
        if serializer.is_valid():
            receipt = serializer.save()
            context['receipt'] = receipt
            return render(request, 'receipt_detail.html', context)
        else:
            context['error'] = serializer.errors
            return render(request, 'upload_receipt.html', context)
    
    # GET request: just render the upload form.
    return render(request, 'upload_receipt.html', context)


def get_json_from_chatgpt(ocr_text):
    """
    Calls OpenAI's ChatCompletion to convert OCR text into structured JSON.
    Expects ChatGPT to return JSON with keys like 'name', 'total_cost', 'taxes', 'tip', and 'items'.
    """
    prompt = (
        "Extract the receipt information from the following text and output valid JSON with exactly these keys: "
        "'name' (string), 'total_cost' (string or number), and 'items' (an array of objects, each having 'item_name' and 'item_cost'). "
        "Output only JSON with no extra commentary.\n\n"
        "Extract the receipt information from the following text and output valid JSON with these keys: "
        "'name' (string), 'total_cost' (string or number), "
        "'taxes' (string or number, optional), 'tip' (string or number, optional), and "
        "'items' (an array of objects, each having 'item_name' and 'item_cost'). "
        "Output only valid JSON with no extra commentary.\n\n"
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
