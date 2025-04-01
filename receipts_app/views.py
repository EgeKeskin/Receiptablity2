import os
import json
import pytesseract
from openai import OpenAI
from PIL import Image
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv
import logging
from .models import Receipt, RoomParticipant
from decimal import Decimal, ROUND_HALF_UP
import random

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
    room_type = request.GET.get('room_type', 'custom_split')

    if request.method == 'POST':
        receipt_image = request.FILES.get('receipt_image')
        room_type = request.POST.get('room_type', 'custom_split')
        number_of_people = request.POST.get('number_of_people')

        if not receipt_image:
            context['error'] = "No image file provided."
            context['room_type'] = room_type
            return render(request, 'upload_receipt_probabalistic.html' if room_type == 'probabalistic_roulette' else 'upload_receipt.html', context)

        try:
            image = Image.open(receipt_image)
        except Exception:
            context['error'] = "Invalid image file."
            context['room_type'] = room_type
            return render(request, 'upload_receipt_probabalistic.html' if room_type == 'probabalistic_roulette' else 'upload_receipt.html', context)

        extracted_text = pytesseract.image_to_string(image)
        print("Extracted Text:", extracted_text)

        try:
            receipt_data = get_json_from_chatgpt(extracted_text)
            print("Parsed Receipt Data from ChatGPT:", receipt_data)
        except Exception as e:
            context['error'] = f"Error processing OCR text: {str(e)}"
            context['room_type'] = room_type
            return render(request, 'upload_receipt_probabalistic.html' if room_type == 'probabalistic_roulette' else 'upload_receipt.html', context)

        receipt_data['room_type'] = room_type

        if number_of_people and number_of_people.isdigit() and int(number_of_people) > 0:
            receipt_data['number_of_people'] = int(number_of_people)

        serializer = ReceiptSerializer(data=receipt_data, context={'request': request})
        if serializer.is_valid():
            receipt = serializer.save()
            return redirect('receipt_room', receipt_id=receipt.id)
        else:
            context['error'] = serializer.errors
            context['room_type'] = room_type
            return render(request, 'upload_receipt_probabalistic.html' if room_type == 'probabalistic_roulette' else 'upload_receipt.html', context)

    # GET: choose the right template to display
    context['room_type'] = room_type
    template = 'upload_receipt_ppr.html' if room_type == 'probabalistic_roulette' else 'upload_receipt.html'
    return render(request, template, context)



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
                print(f"Error saving participant: {e}")  # Optional: log error

    return render(request, 'add_participant.html', {
        'receipt': receipt,
        'default_ceiling': round(default_ceiling, 2),
    })

@login_required
def run_probabilistic_split_view(request, receipt_id):
    receipt = get_object_or_404(Receipt, id=receipt_id)
    participants = list(receipt.participants.all())

    if len(participants) < (receipt.number_of_people or 0):
        return redirect('receipt_room', receipt_id=receipt_id)

    total_cost = float(receipt.total_cost or 0)
    cost_left = total_cost
    assignments = []

    # Clone the list of participants to iterate through without modifying the original
    unassigned = participants[:]

    while unassigned:
        p = unassigned.pop(0)

        # If total cost has already been covered, assign $0 to remaining participants
        if cost_left <= 0:
            assignments.append({
                "name": p.name,
                "paid": Decimal(0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "ceiling": p.price_ceiling,
                "initial_prob": p.willingness_to_pay,
                "random_roll": None
            })
            continue

        # Compute remaining weighted average
        remaining_weight = sum(u.willingness_to_pay * float(u.price_ceiling) for u in unassigned)
        if remaining_weight > 0 and len(unassigned) > 0:
            weighted_avg = cost_left / remaining_weight
        else:
            weighted_avg = 0

        # Roll for payment
        rand = random.random()
        prob = p.willingness_to_pay
        pay_amount = min(float(p.price_ceiling), cost_left) if rand <= prob else 0

        assignments.append({
            "name": p.name,
            "paid": Decimal(pay_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "ceiling": p.price_ceiling,
            "initial_prob": prob,
            "random_roll": round(rand, 3)
        })

        cost_left -= pay_amount

        # Adjust willingness for remaining participants
        if cost_left > 0 and unassigned:
            for u in unassigned:
                new_prob = cost_left / (float(u.price_ceiling) * len(unassigned))
                u.willingness_to_pay = min(round(new_prob, 3), 1.0)

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
