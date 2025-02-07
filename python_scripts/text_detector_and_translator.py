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
        self.prev_translated_texts = None

        LOGGER.info("Initializing EasyOCR reader and GEMINI model...")

        # Initialize EasyOCR reader
        lst = lang.split("+")
        self.reader = easyocr.Reader(lst)

        # Initialize GEMINI model
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash-002")

        # Precompile regex for better performance
        # Use regex to ignore some sentences from the OCR
        self.pattern1 = re.compile(r"^[A-Za-z\s\d\.]+$") # Matches alphanumeric text with spaces or periods
        self.pattern2 = re.compile(r"^\d") # Matches strings that start with a digit
        self.pattern3 = re.compile(r"^[A-Za-z0-9].*[A-Za-z0-9]$") # Matches strings that start and end with an alphanumeric character.
        self.pattern4 = re.compile(r"^[^\w\s]+$") # Matches strings with only special characters
        
    def detect_text(self, image: str, decoder='beamsearch'):
        
        LOGGER.info("Detecting text...")
        
        # Detect texts from the image
        result = self.reader.readtext(
            image, 
            decoder,
            paragraph=True, 
            link_threshold=0.6,
            text_threshold=0.8, 
            height_ths=1.0, 
            width_ths=1.0, 
            y_ths=0.07, 
            x_ths=0.3
        )
        
        if not result:
            LOGGER.info("No text detected.")
            return []
        
        # Extract detected texts with bounding boxes
        detected_texts = []
        for detection in result:
            text = detection[1]  # Detected text
            bbox = detection[0]  # EasyOCR bounding boxes -> [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]

            # Use regex to ignore some sentences from the OCR
            if (
                self.pattern1.match(text.strip()) or
                self.pattern2.match(text.strip()) or
                self.pattern3.match(text.strip()) or
                self.pattern4.match(text.strip())
            ):
                continue
            
            # Extracting the top-left corner (x1, y1) and bottom-right corner (x3, y3)
            top_left = bbox[0]
            bottom_right = bbox[2]
            
            top_left_x = int(top_left[0])
            top_left_y = int(top_left[1])
            bottom_right_x = int(bottom_right[0])  # width of the bounding box
            bottom_right_y = int(bottom_right[1])  # height of the bounding box
            
            detected_texts.append((text, (top_left_x, top_left_y, bottom_right_x, bottom_right_y)))

        return detected_texts

    def translate(self, detected_texts, lang_to="English"):

        if not detected_texts:
            return []

        # Comparing text to avoid sending a prompt if nothing changed on the screen
        prev_texts = [text for text, _ in self.prev_detected_texts] if self.prev_detected_texts else []
        new_texts = [text for text, _ in detected_texts]
        
        if prev_texts == new_texts:
            LOGGER.info("Detected text is unchanged. No prompt sent.")
            return self.prev_translated_texts
        
        self.prev_detected_texts = detected_texts

        prompt = f"""
        You are an expert translator. 
        Translate the text below to {lang_to}.
        Do not perform transliteration.
        Return everything in the same order and do not add anything else or change the numbers:\n
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
        result = [(item["text"], bbox) for item, (_, bbox) in zip(response_data, detected_texts)]
        
        # Update previously detected texts
        self.prev_translated_texts = result

        return result
    
    def detect_and_translate(self, image: str):
        detected_texts = self.detect_text(image)
        translated_texts = self.translate(detected_texts)
        return translated_texts