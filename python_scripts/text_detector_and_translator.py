import easyocr
import google.generativeai as genai
import logging
import json
import re
import typing_extensions as typing

# ANSI color codes
# To be consistent with Rust log output
COLOR_RESET = '\033[0m'
COLOR_GREY = '\033[90m'  # Grey color for brackets
COLOR_GREEN = '\033[32m' # Green color for log level

log_format = (
    f"{COLOR_GREY}[{COLOR_RESET}"
    "%(asctime)s "
    f"{COLOR_GREEN}%(levelname)s{COLOR_RESET} "
    "%(name)s"
    f"{COLOR_GREY}]{COLOR_RESET} %(message)s"
)

logging.basicConfig(level=logging.INFO, format=log_format, datefmt="%Y-%m-%dT%H:%M:%SZ")
LOGGER = logging.getLogger(__name__)

# The structured output for Gemini
class TranslatedTextBBox(typing.TypedDict):
    text: str
    index: int

class TextDetectorAndTranslator:
    def __init__(self, lang: str, api_key: str):

        self.prev_detected_texts = None

        LOGGER.info("Initializing EasyOCR reader and GEMINI model...")

        # Initialize EasyOCR reader
        lst = lang.split("+")
        self.reader = easyocr.Reader(lst)

        # Initialize GEMINI model
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        
    def detect_text(self, image: str):
        
        LOGGER.info("Detecting text...")
        
        # Detect texts from the image
        result = self.reader.readtext(image, text_threshold=0.5)
        
        if not result:
            LOGGER.info("No text detected.")
            return []
        
        # Extract detected texts with bounding boxes
        detected_texts = []
        for detection in result:
            text = detection[1]  # Detected text
            bbox = detection[0]  # EasyOCR bounding boxes -> [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]

            # Ignore only numbers
            if text.isdigit():
                continue
            elif re.match("^[A-Za-z0-9]+$", text):  # Alphanumeric text without separators
                continue
            # Exclude strings with special characters between alphanumeric parts (e.g., "abc:123" or "abc-abc")
            elif re.search(r"[A-Za-z0-9]+[^\w\s]+[A-Za-z0-9]+", text):
                continue
            elif re.search(r"\d+[A-Za-z]+|[A-Za-z]+\d+", text):  # This matches any number followed by letters or vice versa
                continue
            
            # Extracting the top-left corner (x1, y1) and bottom-right corner (x3, y3)
            top_left = bbox[0]
            bottom_right = bbox[2]
            
            x = int(top_left[0])
            y = int(top_left[1])
            w = int(abs(bottom_right[0] - top_left[0]))  # width of the bounding box
            h = int(abs(bottom_right[1] - top_left[1]))  # height of the bounding box
            
            detected_texts.append((text, (x, y, w, h)))

        return detected_texts

    def translate(self, detected_texts, lang_to="English"):

        if not detected_texts:
            return []

        # Comparing bbox instead of text to be able to save the translated text in self.prev_detected_texts
        prev_texts = [bbox for _, bbox in self.prev_detected_texts] if self.prev_detected_texts else []
        new_texts = [bbox for _, bbox in detected_texts]
        
        if prev_texts == new_texts:
            LOGGER.info("Detected text is unchanged. No prompt sent.")
            return self.prev_detected_texts

        prompt = f"""
        You are an expert translator. 
        Translate the text below to {lang_to}, 
        return everything in the same order and do not add anything else or change the numbers:\n
        """ + "\n".join([f'{index}. "{text}")' for index, (text, bbox) in enumerate(detected_texts)])

        LOGGER.info("Sent the prompt to GEMINI. Waiting for a response...")
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", response_schema=list[TranslatedTextBBox]
            ),
        )
        LOGGER.info("Response received.")

        # Load the data in the expected format
        response_data = json.loads(response.text)
        result = []
        for item, (_, bbox) in zip(response_data, detected_texts):
            text = item["text"]
            
            result.append((text, bbox))
        
        # Update previously detected texts
        self.prev_detected_texts = result

        return result
    
    def detect_and_translate(self, image: str):
        detected_texts = self.detect_text(image)
        translated_texts = self.translate(detected_texts)
        return translated_texts