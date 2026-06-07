import os
import json
import sys

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    metadata_path = os.path.join(base_dir, "data", "processed", "preprocessing_metadata.json")
    report_path = os.path.join(base_dir, "data", "processed", "outlier_report.json")
    
    if not os.path.exists(metadata_path):
        print(f"Error: {metadata_path} not found.")
        sys.exit(1)
        
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
        
    outliers = []
    
    for rec in metadata.get("recordings", []):
        if rec["original_frames"] < 50:
            outliers.append({
                "sample_id": rec["sample_id"],
                "label": rec["label"],
                "frame_count": rec["original_frames"],
                "recommendation": "REMOVE"
            })
            
    print(f"Total outlier count: {len(outliers)}")
    
    with open(report_path, "w") as f:
        json.dump(outliers, f, indent=2)
        
    print(f"Outlier report generated at: {report_path}")

if __name__ == "__main__":
    main()
