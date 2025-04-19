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
from .models import Receipt, RoomParticipant
from decimal import Decimal, ROUND_HALF_UP
import random
from collections import deque

from receipts_app.models import Receipt, ReceiptItem
from receipts_app.serializers import ReceiptSerializer

if os.environ.get('USE_DOCKER') == '1':
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
else:
    pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'  # your local path


# Load environment variables and initialize OpenAI client.
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logger = logging.getLogger(__name__)

@login_required(login_url='/login/')
def upload_receipt_view(request):
    """
    Renders a receipt upload form (GET) and processes the uploaded image (POST).
    Chooses the template dynamically based on room_type.
    """
    context = {}
    room_type = request.GET.get('room_type', 'custom_split')

    if request.method == 'POST':
        receipt_image = request.FILES.get('receipt_image')
        room_type = request.POST.get('room_type', 'custom_split')
        number_of_people = request.POST.get('number_of_people')
        venmo = request.POST.get('venmo')

        # Determine which template to use
        if room_type == 'probabalistic_roulette':
            template = 'upload_receipt_probabalistic.html'
        elif room_type == 'custom_split':
            template = 'upload_custom_split.html'
        else:
            template = 'upload_receipt.html'

        if not receipt_image:
            context['error'] = "No image file provided."
            context['room_type'] = room_type
            return render(request, template, context)

        try:
            image = Image.open(receipt_image)
        except Exception:
            context['error'] = "Invalid image file."
            context['room_type'] = room_type
            return render(request, template, context)

        extracted_text = pytesseract.image_to_string(image)
        print("Extracted Text:", extracted_text)

        try:
            receipt_data = get_json_from_chatgpt(extracted_text)
            print("Parsed Receipt Data from ChatGPT:", receipt_data)
        except Exception as e:
            context['error'] = f"Error processing OCR text: {str(e)}"
            context['room_type'] = room_type
            return render(request, template, context)

        # Add additional context
        receipt_data['room_type'] = room_type
        if number_of_people and number_of_people.isdigit() and int(number_of_people) > 0:
            receipt_data['number_of_people'] = int(number_of_people)
        if venmo:
            receipt_data['venmo'] = venmo

        serializer = ReceiptSerializer(data=receipt_data, context={'request': request})
        if serializer.is_valid():
            receipt = serializer.save()
            return redirect('receipt_room', receipt_id=receipt.id)
        else:
            context['error'] = serializer.errors
            context['room_type'] = room_type
            return render(request, template, context)

    # GET
    if room_type == 'probabalistic_roulette':
        template = 'upload_receipt_ppr.html'
    elif room_type == 'custom_split':
        template = 'upload_custom_split.html'
    else:
        template = 'upload_receipt.html'

    context['room_type'] = room_type
    return render(request, template, context)



def get_json_from_chatgpt(ocr_text):
    """
    Calls OpenAI's ChatCompletion to convert OCR text into structured JSON.
    Expects ChatGPT to return JSON with keys like 'name', 'total_cost', 'taxes', 'tip', and 'items'.
    Returns a Python dictionary with the parsed receipt data.
    """
    prompt = (
        "Extract the receipt information from the following text and output valid JSON with exactly these keys: "
        "'name' (string), 'total_cost' (number, if unknown put 0.00), and 'items' (an array of objects, each having 'item_name' (string) and 'item_cost (number)'). "
        "Also include 'taxes' and 'tip' (both numbers), if you can't find them put 0.00. "
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
def receipt_room_owner_view(request, receipt_id):
    """
    Retrieves the Receipt by its UUID and renders the owner-specific page showing all receipt details and related items.
    """
    receipt = get_object_or_404(Receipt, id=receipt_id)
    if receipt.owner == request.user:
        if receipt.room_type == 'roulette':
            return render(request, 'roulette_room_owner.html', {'receipt': receipt})
        elif receipt.room_type == 'split_evenly':
            return render(request, 'receipt_room_owner_split.html', {'receipt': receipt})
        return render(request, 'receipt_room_owner.html', {'receipt': receipt})
    else:
        return redirect('receipt_room', receipt_id=receipt_id)

@login_required
def receipt_room_owner_probabalistic_view(request, receipt_id):
    """
    Retrieves the Receipt by its UUID and renders the owner-specific page for probabilistic roulette.
    """
    receipt = get_object_or_404(Receipt, id=receipt_id)
    if receipt.owner == request.user:
        return render(request, 'receipt_room_owner_probabalistic.html', {'receipt': receipt})
    else:
        return redirect('receipt_room', receipt_id=receipt_id)

def add_participant(request, receipt_id):
    receipt = get_object_or_404(Receipt, id=receipt_id)

    # Calculate the default price ceiling
    try:
        if receipt.total_cost and receipt.number_of_people:
            default_ceiling = float(receipt.total_cost) / int(receipt.number_of_people)
        else:
            default_ceiling = float(receipt.total_cost or 0)
    except (ValueError, ZeroDivisionError):
        default_ceiling = 0.0

    if request.method == 'POST':
        name = request.POST.get('name')
        wtp = request.POST.get('willingness_to_pay')
        ceiling = request.POST.get('price_ceiling')

        if name and wtp and ceiling:
            try:
                participant = RoomParticipant(
                    receipt=receipt,
                    name=name,
                    willingness_to_pay=float(wtp),
                    price_ceiling=float(ceiling),
                )
                if request.user.is_authenticated:
                    participant.user = request.user
                participant.save()
                return redirect('receipt_room', receipt_id=receipt.id)
            except Exception as e:
                print(f"Error saving participant: {e}") 

    return render(request, 'add_participant.html', {
        'receipt': receipt,
        'default_ceiling': round(default_ceiling, 2),
    })

@login_required
def run_probabilistic_split_view(request, receipt_id):
    receipt = get_object_or_404(Receipt, id=receipt_id)
    
    # Recalculate the total cost dynamically
    item_total = sum(item.item_cost or Decimal(0) for item in receipt.receipt_items.all())
    receipt.total_cost = item_total + (receipt.taxes or Decimal(0)) + (receipt.tip or Decimal(0))
    receipt.save()

    participants = list(receipt.participants.all())

    if len(participants) < (receipt.number_of_people or 0):
        return redirect('receipt_room', receipt_id=receipt_id)

    participants.sort(key=lambda p: float(p.price_ceiling)) 

    total_cost = float(receipt.total_cost or 0)
    cost_left = total_cost
    assignments = []

    for i, p in enumerate(participants):
        is_last = (i == len(participants) - 1)

        if cost_left <= 0:
            paid = 0
            rand = None
        elif is_last:
            paid = min(cost_left, float(p.price_ceiling))
            rand = None
        else:
            rand = random.random()
            paid = float(p.price_ceiling) if rand <= p.willingness_to_pay else 0

        paid_decimal = Decimal(paid).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assignments.append({
            "name": p.name,
            "paid": paid_decimal,
            "ceiling": p.price_ceiling,
            "initial_prob": p.willingness_to_pay,
            "random_roll": round(rand, 3) if rand is not None else "Forced"
        })

        cost_left -= float(paid_decimal)

        remaining = participants[i+1:]
        if cost_left > 0 and remaining:
            for r in remaining:
                new_prob = cost_left / (float(r.price_ceiling) * len(remaining))
                r.willingness_to_pay = min(round(new_prob, 3), 1.0)

    paid_total = sum(a['paid'] for a in assignments)
    overflow = Decimal(total_cost).quantize(Decimal("0.01")) - paid_total

    if abs(overflow) >= Decimal("0.01"):
        def roll_sort_key(a):
            roll = a['random_roll']
            return roll if isinstance(roll, float) else 1.0 

        sorted_candidates = sorted(assignments, key=roll_sort_key)

        for a in sorted_candidates:
            if overflow <= Decimal("0.00"):
                break
            max_addable = Decimal(a['ceiling']) - a['paid']
            if max_addable > 0:
                to_add = min(overflow, max_addable)
                a['paid'] += to_add.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                overflow -= to_add

    return render(request, 'probabilistic_result.html', {
        'receipt': receipt,
        'assignments': assignments,
        'total_cost': Decimal(total_cost).quantize(Decimal("0.01"))
    })

@login_required(login_url='/login/')
def delete_receipt_view(request, receipt_id):
    receipt = get_object_or_404(Receipt, id=receipt_id)
    if receipt.owner == request.user:
        receipt.delete()
        return redirect('homepage')
    else:
        return redirect('receipt_room', receipt_id=receipt_id)

@login_required(login_url='/login/')
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

            # Redirect back to the current page
            current_page = request.POST.get('current_page', 'receipt_room_owner')
            return redirect(current_page, receipt_id=receipt_id)
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

            # Redirect back to the current page
            current_page = request.POST.get('current_page', 'receipt_room_owner')
            return redirect(current_page, receipt_id=receipt_id)
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
