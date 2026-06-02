import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "ml", "data", "processed")
SCALERS_DIR = os.path.join(BASE_DIR, "ml", "data", "scalers")

TARGET_FRAMES = 100
FEATURE_COUNT = 13

FEATURES = [
    "thumb", "index", "middle", "ring", "little",
    "ax", "ay", "az",
    "gx", "gy", "gz",
    "pitch", "roll"
]

HALL_SENSORS = ["thumb", "index", "middle", "ring", "little"]
MPU_FEATURES = ["ax", "ay", "az", "gx", "gy", "gz", "pitch", "roll"]
