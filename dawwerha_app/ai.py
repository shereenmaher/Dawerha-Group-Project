import json
import time
from django.conf import settings
from google import genai
from google.genai import types
from .models import Material


# Send the photo to Gemini and get the item details back
def analyze_image(image_file):
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    materials = ", ".join(Material.objects.values_list('name', flat=True))
    image_data = image_file.read()

    prompt = f"""
    Look at the item in this photo and answer in JSON only, like this:
    {{"item_name": "Water bottle", "material": "PET plastic", "recyclable": true, "weight_kg": 0.03, "tip": "Rinse it and remove the cap"}}

    Rules:
    - material must be one of: {materials}
    - weight_kg is the weight of one item in kilograms
    - tip is one short sentence about how to prepare it for recycling
    """

    # Try 3 times if the AI is busy
    for attempt in range(3):
        try:
            start = time.time()

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=[
                    types.Part.from_bytes(
                        data=image_data,
                        mime_type=image_file.content_type
                    ),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )

            print("AI took", round(time.time() - start, 1), "seconds")
            return json.loads(response.text)

        except Exception as e:
            print("Try", attempt + 1, "failed:", e)

            # Stop now if the daily limit is finished
            if attempt == 2 or "RESOURCE_EXHAUSTED" in str(e):
                raise

            time.sleep(1)