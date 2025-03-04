import os
import json
import pytesseract
from openai import OpenAI
from PIL import Image
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from receipts_app.models import Receipt
from receipts_app.serializers import ReceiptSerializer
from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv

# Ensure the OpenAI API key is set.
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set the Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'  # Update this path as needed

# Endpoint for image upload that converts a receipt image into JSON using ChatGPT.
class ReceiptImageUploadView(APIView):
    def post(self, request, *args, **kwargs):
        # Look for an image file in the request under the key 'receipt_image'
        image_file = request.FILES.get('receipt_image')
        if not image_file:
            return Response({'error': 'No image provided.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Open the image using Pillow.
            image = Image.open(image_file)
        except Exception as e:
            return Response({'error': 'Invalid image file.'}, status=status.HTTP_400_BAD_REQUEST)

        # Use pytesseract to extract text from the image.
        extracted_text = pytesseract.image_to_string(image)
        print("Extracted Text:", extracted_text)  # Debug log

        # Use ChatGPT API to convert the extracted text into structured JSON.
        try:
            receipt_data = self.get_json_from_chatgpt(extracted_text)
            print("Parsed Receipt Data from ChatGPT:", receipt_data)  # Debug log
        except Exception as e:
            return Response(
                {'error': f'Error processing OCR text: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Ensure receipt_items is provided
        if 'receipt_items' not in receipt_data:
            receipt_data['receipt_items'] = []

        # Validate and save the receipt data using our serializer.
        serializer = ReceiptSerializer(data=receipt_data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_json_from_chatgpt(self, ocr_text):
        """
        Calls OpenAI's ChatCompletion.create to convert the OCR text into structured JSON.
        
        The prompt instructs ChatGPT to extract the receipt name, total cost,
        and a list of items (each with item_name and item_cost) from the given text.
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
        response = client.chat.completions.create(model="gpt-3.5-turbo",
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
        temperature=0)

        # Extract and parse the message content.
        message_content = response.choices[0].message.content.strip()

        try:
            receipt_data = json.loads(message_content)
        except json.JSONDecodeError:
            raise ValueError("ChatGPT did not return valid JSON. Response was: " + message_content)
        return receipt_data