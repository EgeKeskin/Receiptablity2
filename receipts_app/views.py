import os
import json
import pytesseract
from openai import OpenAI
from PIL import Image
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv
import logging
from decimal import Decimal  # Import Decimal for precise calculations
from django.http import JsonResponse

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
        serializer = ReceiptSerializer(data=receipt_data, context={'request': request})
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

@login_required
def receipt_room_owner_view(request, receipt_id):
    """
    Retrieves the Receipt by its UUID and renders the owner-specific page showing all receipt details and related items.
    """
    receipt = get_object_or_404(Receipt, id=receipt_id)
    if receipt.owner == request.user:
        return render(request, 'receipt_room_owner.html', {'receipt': receipt})
    else:
        return redirect('receipt_room', receipt_id=receipt_id)

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

@login_required
def edit_receipt_item_view(request, receipt_id, item_id):
    receipt = get_object_or_404(Receipt, id=receipt_id)
    if receipt.owner == request.user:
        item = get_object_or_404(ReceiptItem, id=item_id, receipt=receipt)
        if request.method == 'POST':
            item_name = request.POST.get('item_name')
            item_cost = request.POST.get('item_cost')  # Get the updated cost from the form
            if item_name:
                item.item_name = item_name
            if item_cost:
                try:
                    item.item_cost = Decimal(item_cost)  # Convert to Decimal for consistency
                except:
                    pass  # Ignore invalid input for item_cost
            item.save()

            # Recalculate the total cost of the receipt
            item_total = sum(i.item_cost or Decimal(0) for i in receipt.receipt_items.all())
            receipt.total_cost = item_total + (receipt.taxes or Decimal(0)) + (receipt.tip or Decimal(0))
            receipt.save()

            return redirect('receipt_room_owner', receipt_id=receipt_id)
        return render(request, 'edit_receipt_item.html', {'item': item})
    else:
        return redirect('receipt_room', receipt_id=receipt_id)

@login_required
def edit_receipt_details_view(request, receipt_id):
    receipt = get_object_or_404(Receipt, id=receipt_id)
    if receipt.owner == request.user:
        if request.method == 'POST':
            # Update receipt details
            receipt.name = request.POST.get('receipt_name', receipt.name)
            receipt.taxes = Decimal(request.POST.get('taxes', receipt.taxes or 0))  # Convert to Decimal
            receipt.tip = Decimal(request.POST.get('tip', receipt.tip or 0))  # Convert to Decimal
            
            # Recalculate total cost
            item_total = sum(item.item_cost or Decimal(0) for item in receipt.receipt_items.all())  # Ensure Decimal
            receipt.total_cost = item_total + receipt.taxes + receipt.tip
            
            receipt.save()
            return redirect('receipt_room_owner', receipt_id=receipt_id)
    return redirect('receipt_room', receipt_id=receipt_id)

@login_required
def add_receipt_item_view(request, receipt_id):
    if request.method == "POST":
        receipt = get_object_or_404(Receipt, id=receipt_id)
        if receipt.owner == request.user:
            data = json.loads(request.body)  # Parse JSON data from the request
            item_name = data.get("item_name", "New Item")
            item_cost = data.get("item_cost", 0)  # Default to 0 if not provided
            new_item = ReceiptItem.objects.create(
                receipt=receipt,
                item_name=item_name,
                item_cost=Decimal(item_cost)  # Convert to Decimal
            )
            return JsonResponse({
                "success": True,
                "item": {
                    "id": str(new_item.id),
                    "item_name": new_item.item_name,
                    "item_cost": float(new_item.item_cost)
                }
            })
    return JsonResponse({"success": False}, status=400)
