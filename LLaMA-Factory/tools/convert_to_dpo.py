import json
import random
import argparse

def convert_to_dpo_format(input_file, train_output_file, test_output_file, train_ratio=0.8):
    """
    Convert comparison data to DPO format and split into train/test sets.
    
    Args:
        input_file: Path to comparison_data_v2.json
        train_output_file: Path to output training DPO format file
        test_output_file: Path to output test DPO format file
        train_ratio: Ratio of training data (default: 0.8 for 80:20 split)
    """
    # Read the comparison data
    with open(input_file, 'r', encoding='utf-8') as f:
        comparison_data = json.load(f)
    
    dpo_data = []
    
    # Process each entry
    for entry in comparison_data:
        user_input = entry['user_input']
        responses_and_scores = entry['responses_and_scores']
        
        # Create pairs: compare each response with lower-scored responses
        for i in range(len(responses_and_scores)):
            for j in range(i + 1, len(responses_and_scores)):
                response_1 = responses_and_scores[i]
                response_2 = responses_and_scores[j]
                
                # Determine which is chosen (higher score) and which is rejected (lower score)
                if response_1['score'] > response_2['score']:
                    chosen = response_1
                    rejected = response_2
                elif response_2['score'] > response_1['score']:
                    chosen = response_2
                    rejected = response_1
                else:
                    # If scores are equal, skip this pair
                    continue
                
                # Create DPO entry
                dpo_entry = {
                    'conversation': [
                        {
                            'from': 'human',
                            'value': user_input
                        }
                    ],
                    'chosen': {
                        'from': 'gpt',
                        'value': chosen['response']
                    },
                    'rejected': {
                        'from': 'gpt',
                        'value': rejected['response']
                    },
                    'chosen_score': chosen['score'],
                    'rejected_score': rejected['score'],
                    'chosen_source': chosen['source'],
                    'rejected_source': rejected['source']
                }
                
                dpo_data.append(dpo_entry)
    
    # Shuffle the data for random split
    random.seed(42)  # Set seed for reproducibility
    random.shuffle(dpo_data)
    
    # Split into train and test sets
    split_idx = int(len(dpo_data) * train_ratio)
    train_data = dpo_data[:split_idx]
    test_data = dpo_data[split_idx:]
    
    # Write train data to file
    with open(train_output_file, 'w', encoding='utf-8') as f:
        json.dump(train_data, f, indent=2, ensure_ascii=False)
    
    # Write test data to file
    with open(test_output_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    print(f"Conversion complete!")
    print(f"Input entries: {len(comparison_data)}")
    print(f"Output DPO pairs: {len(dpo_data)}")
    print(f"Train set: {len(train_data)} pairs ({train_ratio*100:.0f}%)")
    print(f"Test set: {len(test_data)} pairs ({(1-train_ratio)*100:.0f}%)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert comparison data to DPO format')
    parser.add_argument('--input', '-i', type=str, 
                        default='/data2/zonglin/temp/LLaMA-Factory/data/comparison_data_v2.json',
                        help='Path to input comparison data file (default: data/comparison_data_v2.json)')
    parser.add_argument('--train_output', '-t', type=str,
                        default='/data2/zonglin/temp/LLaMA-Factory/data/dpo_converted_train.json',
                        help='Path to output training DPO file (default: data/dpo_converted_train.json)')
    parser.add_argument('--test_output', '-e', type=str,
                        default='/data2/zonglin/temp/LLaMA-Factory/data/dpo_converted_test.json',
                        help='Path to output test DPO file (default: data/dpo_converted_test.json)')
    parser.add_argument('--train_ratio', '-r', type=float, default=0.8,
                        help='Train/test split ratio (default: 0.8)')
    
    args = parser.parse_args()
    
    convert_to_dpo_format(args.input, args.train_output, args.test_output, args.train_ratio)

