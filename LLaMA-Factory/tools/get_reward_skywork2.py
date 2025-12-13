import argparse
import json
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from tqdm import tqdm

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Add reward scores to preference data using Skywork Reward Model")
parser.add_argument("--input", type=str, default="../data/trl_test.json", 
                    help="Path to input JSON file (default: ../data/trl_test.json)")
parser.add_argument("--output", type=str, default=None,
                    help="Path to output JSON file (default: input file with '_with_scores' suffix)")
args = parser.parse_args()

# Configuration
INPUT_FILE = args.input
OUTPUT_FILE = args.output if args.output else INPUT_FILE.replace(".json", "_with_scores.json")

# Load model and tokenizer
print("Loading model and tokenizer...")
device = "cuda:0"
model_name = "Skywork/Skywork-Reward-V2-Llama-3.1-8B"
rm = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map=device,
    attn_implementation="flash_attention_2",
    num_labels=1,
)
tokenizer = AutoTokenizer.from_pretrained(model_name)
print("Model loaded successfully!")

# Load input data
print(f"\nLoading data from {INPUT_FILE}...")
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)
print(f"Loaded {len(data)} data points")

def get_reward_score(prompt, response):
    """Compute reward score for a given prompt-response pair."""
    conv = [{"role": "user", "content": prompt}, {"role": "assistant", "content": response}]
    
    # Format and tokenize the conversation
    conv_formatted = tokenizer.apply_chat_template(conv, tokenize=False)
    
    # Remove potential duplicate bos token
    if tokenizer.bos_token is not None and conv_formatted.startswith(tokenizer.bos_token):
        conv_formatted = conv_formatted[len(tokenizer.bos_token):]
    
    conv_tokenized = tokenizer(conv_formatted, return_tensors="pt").to(device)
    
    # Get the reward score
    with torch.no_grad():
        score = rm(**conv_tokenized).logits[0][0].item()
    
    return score

# Process each data point
print("\nProcessing data points...")
chosen_scores = []
rejected_scores = []

for idx, item in enumerate(tqdm(data[:100], desc="Computing scores")):
    # Extract prompt from conversations
    # The prompt is typically in the first conversation with "from": "human"
    prompt = ""
    for conv in item["conversations"]:
        if conv["from"] == "human":
            prompt = conv["value"]
            break
    
    # Extract chosen and rejected responses
    chosen_response = item["chosen"]["value"]
    rejected_response = item["rejected"]["value"]
    
    # Compute scores
    chosen_score = get_reward_score(prompt, chosen_response)
    rejected_score = get_reward_score(prompt, rejected_response)
    
    # Add scores to the data point
    item["chosen_score"] = chosen_score
    item["rejected_score"] = rejected_score
    
    chosen_scores.append(chosen_score)
    rejected_scores.append(rejected_score)

# Save enriched data
print(f"\nSaving enriched data to {OUTPUT_FILE}...")
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# Print statistics
print("\n" + "="*50)
print("STATISTICS")
print("="*50)
print(f"Total data points processed: {len(data)}")
print(f"Average chosen score: {sum(chosen_scores)/len(chosen_scores):.4f}")
print(f"Average rejected score: {sum(rejected_scores)/len(rejected_scores):.4f}")
print(f"Average score difference (chosen - rejected): {sum(c-r for c,r in zip(chosen_scores, rejected_scores))/len(chosen_scores):.4f}")
print(f"Chosen > Rejected in {sum(1 for c,r in zip(chosen_scores, rejected_scores) if c > r)} cases ({100*sum(1 for c,r in zip(chosen_scores, rejected_scores) if c > r)/len(chosen_scores):.1f}%)")
print("\nDone!")
