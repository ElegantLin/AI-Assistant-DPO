#!/usr/bin/env python3
"""
Convert HuggingFace ultrafeedback_binarized_cleaned dataset to DPO format.
"""

import json
import argparse
from datasets import load_dataset
from tqdm import tqdm


def convert_to_dpo_format(example):
    """
    Convert a single example from ultrafeedback format to DPO format.
    
    Source format:
    {
        "prompt": "...",
        "chosen": [
            {"content": "...", "role": "user"},
            {"content": "...", "role": "assistant"}
        ],
        "rejected": [
            {"content": "...", "role": "user"},
            {"content": "...", "role": "assistant"}
        ],
        "score_chosen": 7.0,
        "score_rejected": 6.0,
        "source": "ultrachat"
    }
    
    Target format:
    {
        "conversations": [
            {"from": "human", "value": "..."}
        ],
        "chosen": {
            "from": "gpt",
            "value": "..."
        },
        "rejected": {
            "from": "gpt",
            "value": "..."
        }
    }
    """
    # Extract user messages (all messages before the final assistant response)
    # In the chosen array, the last message should be from assistant
    conversations = []
    
    # Process chosen messages to extract user turns
    for msg in example['chosen']:
        if msg['role'] == 'user':
            conversations.append({
                "from": "human",
                "value": msg['content']
            })
        elif msg['role'] == 'assistant':
            # This is the chosen response
            chosen_response = msg['content']
    
    # Process rejected messages to extract assistant response
    rejected_response = None
    for msg in example['rejected']:
        if msg['role'] == 'assistant':
            rejected_response = msg['content']
    
    # Create the target format
    result = {
        "conversations": conversations,
        "chosen": {
            "from": "gpt",
            "value": chosen_response
        },
        "rejected": {
            "from": "gpt",
            "value": rejected_response
        }
    }
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Convert ultrafeedback_binarized_cleaned to DPO format')
    parser.add_argument('--output_train', type=str, default='data/dpo_ultrafeedback_train.json',
                        help='Output path for training data')
    parser.add_argument('--output_val', type=str, default='data/dpo_ultrafeedback_val.json',
                        help='Output path for validation data')
    parser.add_argument('--output_test', type=str, default='data/dpo_ultrafeedback_test.json',
                        help='Output path for test data')
    parser.add_argument('--train_ratio', type=float, default=0.8,
                        help='Ratio of train split from train_prefs (default: 0.8)')
    parser.add_argument('--max_samples', type=int, default=None,
                        help='Maximum number of samples to convert (for testing)')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for train/val split (default: 42)')
    
    args = parser.parse_args()
    
    print("Loading dataset from HuggingFace...")
    
    # Load train_prefs split
    print("\nProcessing train_prefs split...")
    train_prefs_dataset = load_dataset('allenai/ultrafeedback_binarized_cleaned', split='train_prefs')
    
    if args.max_samples:
        train_prefs_dataset = train_prefs_dataset.select(range(min(args.max_samples, len(train_prefs_dataset))))
    
    # Split train_prefs into train (80%) and val (20%)
    print(f"\nSplitting {len(train_prefs_dataset)} examples into train ({args.train_ratio*100:.0f}%) and val ({(1-args.train_ratio)*100:.0f}%)...")
    train_prefs_dataset = train_prefs_dataset.shuffle(seed=args.seed)
    split_idx = int(len(train_prefs_dataset) * args.train_ratio)
    
    train_dataset = train_prefs_dataset.select(range(split_idx))
    val_dataset = train_prefs_dataset.select(range(split_idx, len(train_prefs_dataset)))
    
    print(f"  Train set: {len(train_dataset)} examples")
    print(f"  Val set: {len(val_dataset)} examples")
    
    # Convert training data
    print(f"\nConverting training examples...")
    train_converted = []
    for example in tqdm(train_dataset, desc="Converting train"):
        converted = convert_to_dpo_format(example)
        train_converted.append(converted)
    
    # Save training data
    print(f"\nSaving training data to {args.output_train}...")
    with open(args.output_train, 'w', encoding='utf-8') as f:
        json.dump(train_converted, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(train_converted)} training examples")
    
    # Convert validation data
    print(f"\nConverting validation examples...")
    val_converted = []
    for example in tqdm(val_dataset, desc="Converting val"):
        converted = convert_to_dpo_format(example)
        val_converted.append(converted)
    
    # Save validation data
    print(f"\nSaving validation data to {args.output_val}...")
    with open(args.output_val, 'w', encoding='utf-8') as f:
        json.dump(val_converted, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(val_converted)} validation examples")
    
    # Load test_prefs split
    print("\nProcessing test_prefs split...")
    test_dataset = load_dataset('allenai/ultrafeedback_binarized_cleaned', split='test_prefs')
    
    if args.max_samples:
        test_dataset = test_dataset.select(range(min(args.max_samples, len(test_dataset))))
    
    print(f"Converting {len(test_dataset)} test examples...")
    test_converted = []
    for example in tqdm(test_dataset, desc="Converting test"):
        converted = convert_to_dpo_format(example)
        test_converted.append(converted)
    
    # Save test data
    print(f"\nSaving test data to {args.output_test}...")
    with open(args.output_test, 'w', encoding='utf-8') as f:
        json.dump(test_converted, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(test_converted)} test examples")
    
    print("\n✓ Conversion complete!")
    print(f"  Training data: {args.output_train} ({len(train_converted)} examples)")
    print(f"  Validation data: {args.output_val} ({len(val_converted)} examples)")
    print(f"  Test data: {args.output_test} ({len(test_converted)} examples)")


if __name__ == '__main__':
    main()
