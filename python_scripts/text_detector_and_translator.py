import easyocr
import google.generativeai as genai
import logging
import json
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
    bbox: list[(int, int, int, int)]

class TextDetectorAndTranslator:
    def __init__(self, lang: str, api_key: str):

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
        result = self.reader.readtext(image, text_threshold=0.4)
        
        # Extract detected texts with bounding boxes
        detected_texts = []
        for detection in result:
            text = detection[1]  # Detected text
            bbox = detection[0]  # EasyOCR bounding boxes -> [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
            
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

        prompt = f"""
        You are a professional translator for video games. 
        Translate the text below to {lang_to}, 
        return everything in the same order and do not add anything else or change the numbers:\n
        """ + "\n".join([f'("{text}", {bbox})' for text, bbox in detected_texts])

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
        for item in response_data:
            text = item["text"]
            bbox = item["bbox"]
            
            bbox_int = tuple(map(int, bbox))
            result.append((text, bbox_int))
        
        return result
    
    def detect_and_translate(self, image: str):
        detected_texts = self.detect_text(image)
        translated_texts = self.translate(detected_texts)
        return translated_texts