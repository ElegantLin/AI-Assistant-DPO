import json
import argparse
import os

def convert_dpo_to_sft(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Failed to decode JSON from {input_path}: {e}")
            return

    sft_data = []
    for item in data:
        # Get instruction from conversations
        # Typically conversations is a list of dicts: [{"from": "human", "value": "..."}]
        conversations = item.get("conversations", [])
        if not conversations:
            continue
        
        # Taking the first conversation value as instruction
        instruction = conversations[0].get("value", "")
        
        # Get output from chosen
        chosen = item.get("chosen", {})
        if isinstance(chosen, dict):
            output = chosen.get("value", "")
        else:
            # Handle cases where chosen might be a string if the format varies
            output = str(chosen)

        sft_item = {
            "instruction": instruction,
            "input": "",
            "output": output
        }
        sft_data.append(sft_item)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sft_data, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully converted {len(sft_data)} items.")
    print(f"Output saved to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert DPO format dataset to SFT format.")
    parser.add_argument("--input", type=str, required=True, help="Path to the DPO input JSON file.")
    parser.add_argument("--output", type=str, help="Path to the SFT output JSON file. Defaults to input_sft.json")

    args = parser.parse_args()
    
    if args.output is None:
        base, ext = os.path.splitext(args.input)
        args.output = f"{base}_sft{ext}"

    convert_dpo_to_sft(args.input, args.output)
