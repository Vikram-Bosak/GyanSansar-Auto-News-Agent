import os
from src.image_editor.image_processor import create_facebook_post
import logging

logging.basicConfig(level=logging.INFO)

test_image_url = "https://picsum.photos/1080/1350"
headline = "INDIA BEATS AUSTRALIA IN WORLD CUP FINALS"
hook_text = "Watch the highlights now!"

os.makedirs("output/test", exist_ok=True)

for i in range(1, 16):
    logging.info(f"Generating style {i}...")
    create_facebook_post(
        image_url=test_image_url,
        headline=headline,
        hook_text=hook_text,
        output_path=f"output/test/style_{i}.jpg",
        style_id=i
    )
logging.info("Done generating 10 styles.")
