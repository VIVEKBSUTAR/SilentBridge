import os
import json
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PROCESSED_DATA_DIR

class DatasetStatistics:
    @staticmethod
    def generate_and_save(metadata_list, x_shape, y_shape):
        total_samples = len(metadata_list)
        samples_per_label = {}
        frame_counts = []
        
        for m in metadata_list:
            label = m["label"]
            samples_per_label[label] = samples_per_label.get(label, 0) + 1
            frame_counts.append(m["original_frames"])
            
        avg_frames = sum(frame_counts) / len(frame_counts) if frame_counts else 0
        min_frames = min(frame_counts) if frame_counts else 0
        max_frames = max(frame_counts) if frame_counts else 0
        
        stats = {
            "total_samples": total_samples,
            "samples_per_label": samples_per_label,
            "avg_frames": round(avg_frames, 2),
            "min_frames": min_frames,
            "max_frames": max_frames,
            "x_shape": list(x_shape),
            "y_shape": list(y_shape)
        }
        
        if not os.path.exists(PROCESSED_DATA_DIR):
            os.makedirs(PROCESSED_DATA_DIR)
            
        file_path = os.path.join(PROCESSED_DATA_DIR, "dataset_statistics.json")
        with open(file_path, "w") as f:
            json.dump(stats, f, indent=2)
            
        return stats
        
    @staticmethod
    def print_stats(stats):
        print("\n=== Dataset Statistics ===")
        print(f"Total Samples: {stats['total_samples']}")
        for label, count in stats['samples_per_label'].items():
            print(f"  {label}: {count}")
        print(f"Average Frames: {stats['avg_frames']}")
        print(f"Min Frames: {stats['min_frames']}")
        print(f"Max Frames: {stats['max_frames']}")
        print(f"Output X Tensor Shape: {tuple(stats['x_shape'])}")
        print(f"Output y Tensor Shape: {tuple(stats['y_shape'])}")
        print("==========================\n")
