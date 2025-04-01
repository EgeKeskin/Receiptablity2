import os
import json
import pytesseract
from openai import OpenAI
from PIL import Image
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv
import logging

from receipts_app.models import Receipt, ReceiptItem
from receipts_app.serializers import ReceiptSerializer

# Load environment variables and initialize OpenAI client.
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logger = logging.getLogger(__name__)

@login_required(login_url='/login/')
def upload_receipt_view(request):
    """
    Renders a receipt upload form (GET) and processes the uploaded image (POST).
    Accepts room_type from query string or form input.
    """
    context = {}

    if request.method == 'POST':
        receipt_image = request.FILES.get('receipt_image')
        room_type = request.POST.get('room_type', 'custom_split')

        if not receipt_image:
            context['error'] = "No image file provided."
            context['room_type'] = room_type  # preserve value on error
            return render(request, 'upload_receipt.html', context)

        try:
            image = Image.open(receipt_image)
        except Exception:
            context['error'] = "Invalid image file."
            context['room_type'] = room_type
            return render(request, 'upload_receipt.html', context)

        extracted_text = pytesseract.image_to_string(image)
        print("Extracted Text:", extracted_text)

        try:
            receipt_data = get_json_from_chatgpt(extracted_text)
            print("Parsed Receipt Data from ChatGPT:", receipt_data)
        except Exception as e:
            context['error'] = f"Error processing OCR text: {str(e)}"
            context['room_type'] = room_type
            return render(request, 'upload_receipt.html', context)

        # Inject room_type manually
        receipt_data['room_type'] = room_type

        serializer = ReceiptSerializer(data=receipt_data, context={'request': request})
        if serializer.is_valid():
            receipt = serializer.save()
            return redirect('receipt_room', receipt_id=receipt.id)
        else:
            context['error'] = serializer.errors
            context['room_type'] = room_type
            return render(request, 'upload_receipt.html', context)

    # GET: populate room_type from query string
    room_type = request.GET.get('room_type', 'custom_split')
    context['room_type'] = room_type
    return render(request, 'upload_receipt.html', context)


def get_json_from_chatgpt(ocr_text):
    """
    Calls OpenAI's ChatCompletion to convert OCR text into structured JSON.
    Expects ChatGPT to return JSON with keys like 'name', 'total_cost', 'taxes', 'tip', and 'items'.
    Returns a Python dictionary with the parsed receipt data.
    """
    prompt = (
        "Extract the receipt information from the following text and output valid JSON with exactly these keys: "
        "'name' (string), 'total_cost' (number), and 'items' (an array of objects, each having 'item_name' (string) and 'item_cost (number)'). "
        "Also include 'taxes' and 'tip' (both numbers) as optional keys if available. "
        "Output only JSON with no extra commentary. If you aren't confident about a value leave it null.\n\n"
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
    logger.info(receipt)
    
    if request.user.is_authenticated and receipt.owner == request.user:
        return render(request, 'receipt_room_owner.html', {'receipt': receipt})
    else:
        return render(request, 'receipt_room.html', {'receipt': receipt})
    
def receipt_room_view(request, receipt_id):
    """
    Retrieves the Receipt by its UUID and renders a page showing all receipt details and related items.
    The template varies depending on ownership and room_type field on the Receipt.
    """
    receipt = get_object_or_404(Receipt, id=receipt_id)
    room_type = receipt.room_type
    is_owner = request.user.is_authenticated and receipt.owner == request.user
    template_map = {
        'roulette': {
            'owner': 'roulette_room_owner.html',
            'guest': 'roulette_room.html',
        },
        'split_evenly': {
            'owner': 'receipt_room_owner_split.html',
            'guest': 'receipt_room_split.html',
        },
        'custom_split': {
            'owner': 'receipt_room_owner.html',
            'guest': 'receipt_room.html',
        },
        'probabalistic_roulette': {
            'owner': 'receipt_room_owner_probabalistic.html',
            'guest': 'receipt_room_probabalistic.html',
        },
        'default': {
            'owner': 'receipt_room_owner.html',
            'guest': 'receipt_room.html',
        }
    }

    template = template_map.get(room_type, template_map['default'])
    template_name = template['owner'] if is_owner else template['guest']

    return render(request, template_name, {
        'receipt': receipt
    })

@login_required
def delete_receipt_view(request, receipt_id):
    receipt = get_object_or_404(Receipt, id=receipt_id)
    if receipt.owner == request.user:
        receipt.delete()
        return redirect('homepage')
    else:
        return redirect('receipt_room', receipt_id=receipt_id)

@login_required
def delete_receipt_item_view(request, receipt_id, item_id):
    receipt = get_object_or_404(Receipt, id=receipt_id)
    if receipt.owner == request.user:
        item = get_object_or_404(ReceiptItem, id=item_id, receipt=receipt)
        item.delete()
        return redirect('receipt_room_owner', receipt_id=receipt_id)
    else:
        return redirect('receipt_room', receipt_id=receipt_id)
