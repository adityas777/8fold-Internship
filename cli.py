import argparse
import json
import os
import sys
from typing import List

# Add the current folder to sys.path so we can import src modules easily
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pipeline import run_pipeline

def main():
    parser = argparse.ArgumentParser(
        description="Eightfold Candidate Profile Pipeline - End-to-End ingestion, merging, projection, and validation CLI."
    )
    
    parser.add_argument(
        "--sources",
        nargs="+",
        required=True,
        help="Space-separated list of candidate sources (CSV files, JSON files, Resume PDFs, free-text recruiter notes TXT, GitHub usernames/URLs)."
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Optional path to a custom runtime projection configuration JSON file."
    )
    
    parser.add_argument(
        "--out",
        type=str,
        help="Optional path to write the output JSON file. The JSON will always be printed to stdout as well."
    )

    args = parser.parse_args()

    # Load custom projection config if specified
    config_dict = None
    if args.config:
        if not os.path.exists(args.config):
            print(f"Error: Configuration file not found at: {args.config}", file=sys.stderr)
            sys.exit(1)
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
        except Exception as e:
            print(f"Error parsing configuration JSON: {e}", file=sys.stderr)
            sys.exit(1)

    # Execute Pipeline
    try:
        results = run_pipeline(args.sources, config_dict)
        
        # Serialize to formatted JSON string
        formatted_json = json.dumps(results, indent=2, ensure_ascii=False)
        
        # Output to stdout
        print(formatted_json)
        
        # Output to file if specified
        if args.out:
            out_dir = os.path.dirname(os.path.abspath(args.out))
            os.makedirs(out_dir, exist_ok=True)
            with open(args.out, 'w', encoding='utf-8') as f:
                f.write(formatted_json)
            print(f"\n[CLI Success] Output saved to: {args.out}", file=sys.stderr)
            
    except Exception as e:
        print(f"Pipeline Execution Failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
