#!/usr/bin/env python3
"""
Script to flip chosen/rejected pairs in DPO data and convert to SFT format.

This script:
1. Reads a DPO format JSON file (with conversations, chosen, rejected)
2. Randomly flips chosen and rejected fields based on a specified ratio
3. Outputs the flipped DPO data
4. Converts the data to SFT format (instruction, input, output)
"""

import json
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any


def load_json(file_path: str) -> List[Dict[str, Any]]:
    """Load JSON data from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: List[Dict[str, Any]], file_path: str):
    """Save data to JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def flip_chosen_rejected(data: List[Dict[str, Any]], flip_ratio: float, seed: int = None) -> List[Dict[str, Any]]:
    """
    Randomly flip chosen and rejected fields based on flip_ratio.
    
    Args:
        data: List of DPO format dictionaries
        flip_ratio: Ratio of samples to flip (0.0 to 1.0)
        seed: Random seed for reproducibility
        
    Returns:
        List of DPO format dictionaries with flipped pairs
    """
    if seed is not None:
        random.seed(seed)
    
    flipped_data = []
    flip_count = 0
    
    for item in data:
        new_item = item.copy()
        
        # Randomly decide whether to flip this item
        if random.random() < flip_ratio:
            # Swap chosen and rejected
            new_item['chosen'], new_item['rejected'] = item['rejected'], item['chosen']
            flip_count += 1
        
        flipped_data.append(new_item)
    
    print(f"Flipped {flip_count} out of {len(data)} samples ({flip_count/len(data)*100:.2f}%)")
    
    return flipped_data


def convert_to_sft(data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Convert DPO format to SFT format.
    
    Args:
        data: List of DPO format dictionaries
        
    Returns:
        List of SFT format dictionaries with instruction, input, output
    """
    sft_data = []
    
    for item in data:
        # Extract instruction from conversations (first human message)
        instruction = ""
        if 'conversations' in item and len(item['conversations']) > 0:
            for conv in item['conversations']:
                if conv.get('from') == 'human':
                    instruction = conv.get('value', '')
                    break
        
        # Extract output from chosen
        output = ""
        if 'chosen' in item:
            output = item['chosen'].get('value', '')
        
        # Create SFT format entry
        sft_entry = {
            "instruction": instruction,
            "input": "",
            "output": output
        }
        
        sft_data.append(sft_entry)
    
    return sft_data


def main():
    parser = argparse.ArgumentParser(
        description='Flip chosen/rejected in DPO data and convert to SFT format'
    )
    parser.add_argument(
        'input_file',
        type=str,
        help='Input DPO format JSON file'
    )
    parser.add_argument(
        '--flip-ratio',
        type=float,
        default=0.0,
        help='Ratio of samples to flip (0.0 to 1.0, default: 0.0)'
    )
    parser.add_argument(
        '--output-dpo',
        type=str,
        default=None,
        help='Output file for flipped DPO format (default: <input>_flipped.json)'
    )
    parser.add_argument(
        '--output-sft',
        type=str,
        default=None,
        help='Output file for SFT format (default: <input>_flipped_sft.json)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility'
    )
    
    args = parser.parse_args()
    
    # Validate flip ratio
    if not 0.0 <= args.flip_ratio <= 1.0:
        raise ValueError("flip_ratio must be between 0.0 and 1.0")
    
    # Set default output paths if not specified
    input_path = Path(args.input_file)
    if args.output_dpo is None:
        args.output_dpo = str(input_path.parent / f"{input_path.stem}_artificial_flipped_{str(args.flip_ratio).replace('.', '_')}{input_path.suffix}")
    if args.output_sft is None:
        args.output_sft = str(input_path.parent / f"{input_path.stem}_artificial_flipped_{str(args.flip_ratio).replace('.', '_')}_sft{input_path.suffix}")
    
    print(f"Loading data from {args.input_file}...")
    data = load_json(args.input_file)
    print(f"Loaded {len(data)} samples")
    
    # Flip chosen and rejected
    print(f"\nFlipping with ratio {args.flip_ratio}...")
    flipped_data = flip_chosen_rejected(data, args.flip_ratio, args.seed)
    
    # Save flipped DPO data
    print(f"\nSaving flipped DPO data to {args.output_dpo}...")
    save_json(flipped_data, args.output_dpo)
    
    # Convert to SFT format (using the flipped data)
    print(f"\nConverting flipped DPO data to SFT format...")
    print(f"(Note: SFT will contain the flipped chosen/rejected values)")
    sft_data = convert_to_sft(flipped_data)
    
    # Save SFT data
    print(f"Saving SFT data to {args.output_sft}...")
    save_json(sft_data, args.output_sft)
    
    print(f"\nDone!")
    print(f"  - Flipped DPO file: {args.output_dpo}")
    print(f"  - SFT file: {args.output_sft}")


if __name__ == "__main__":
    main()
