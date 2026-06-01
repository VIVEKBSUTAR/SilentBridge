import os

BAUD_RATE = 115200
DEFAULT_COM_PORT = None  # None enables auto-detect
DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
SAMPLE_RATE = 50
MOCK_MODE = False  # Set to True to generate fake data without hardware

SUPPORTED_LABELS = [
    "HELLO",
    "HELP",
    "WATER",
    "FOOD",
    "YES",
    "NO",
    "THANK_YOU",
    "MEDICINE"
]
