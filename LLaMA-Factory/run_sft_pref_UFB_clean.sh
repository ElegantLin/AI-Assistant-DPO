#!/usr/bin/env bash

set -euo pipefail

export FORCE_TORCHRUN=1

# Parse command line arguments
if [ "$#" -lt 2 ] || [ "$#" -gt 5 ]; then
  echo "Usage: $0 <model_size> <method> [sft_dataset] [pref_dataset] [skip_sft]"
  echo ""
  echo "Arguments:"
  echo "  model_size   : Model size (required). Options: 0_5b, 3b, 7b, 14b, 32b"
  echo "  method       : Preference optimization method (required). Options: dpo, ropo, both"
  echo "  sft_dataset  : SFT dataset name (optional, default: UFB_clean_train_sft)"
  echo "  pref_dataset : Preference dataset name (optional, default: UFB_clean_train)"
  echo "  skip_sft     : Skip SFT stage if set to 'skip' (optional, useful if SFT already done)"
  echo ""
  echo "Examples:"
  echo "  $0 0_5b dpo"
  echo "  $0 3b ropo"
  echo "  $0 7b both"
  echo "  $0 3b both UFB_clean_train_sft UFB_clean_train"
  echo "  $0 3b dpo UFB_clean_train_sft UFB_clean_train skip"
  echo ""
  exit 1
fi

model_id="$1"
method="$2"
sft_dataset="${3:-UFB_clean_train_sft}"
pref_dataset="${4:-UFB_clean_train}"
skip_sft="${5:-}"

# Validate method parameter
case "$method" in
  dpo|ropo|both)
    ;;
  *)
    echo "Error: Invalid method '$method'"
    echo "Supported methods: dpo, ropo, both"
    exit 1
    ;;
esac

# Convert model_id to model size for Hugging Face path
case "$model_id" in
  0_5b)
    model_size="0.5B"
    ;;
  3b)
    model_size="3B"
    ;;
  7b)
    model_size="7B"
    ;;
  14b)
    model_size="14B"
    ;;
  32b)
    model_size="32B"
    ;;
  *)
    echo "Error: Unsupported model size '$model_id'"
    echo "Supported sizes: 0_5b, 3b, 7b, 14b, 32b"
    exit 1
    ;;
esac

model_name_or_path="Qwen/Qwen2.5-${model_size}-Instruct"

echo "========================================"
echo "Configuration Summary"
echo "========================================"
echo "Model ID: $model_id"
echo "Model: $model_name_or_path"
echo "Method: $method"
echo "SFT Dataset: $sft_dataset"
echo "Preference Dataset: $pref_dataset"
echo ""

# Detect number of GPUs
if command -v nvidia-smi &> /dev/null; then
  num_gpus=$(nvidia-smi --list-gpus | wc -l)
else
  num_gpus=1
  echo "Warning: nvidia-smi not found, defaulting to 1 GPU"
fi

# Set batch sizes based on GPU count
case $num_gpus in
  8)
    sft_batch_size=4
    sft_gradient_accumulation_steps=8
    pref_batch_size=1
    ;;
  4)
    sft_batch_size=8
    sft_gradient_accumulation_steps=8
    pref_batch_size=2
    ;;
  2)
    sft_batch_size=8
    sft_gradient_accumulation_steps=16
    pref_batch_size=4
    ;;
  1)
    sft_batch_size=8
    sft_gradient_accumulation_steps=32
    pref_batch_size=8
    ;;
  *)
    echo "Warning: Unsupported GPU count ($num_gpus), using defaults for 1 GPU"
    sft_batch_size=4
    pref_batch_size=1
    ;;
esac

echo "========================================"
echo "System Configuration"
echo "========================================"
echo "Number of GPUs: $num_gpus"
echo "SFT per_device_train_batch_size: $sft_batch_size"
echo "Preference per_device_train_batch_size: $pref_batch_size"
echo ""

# SFT configurations
sft_config="examples/train_full/qwen2_5_full_sft.yaml"
sft_output_dir="saves/qwen2_5-${model_id}/full/sft/${sft_dataset}"

# Run SFT stage (unless skipped)
if [ "$skip_sft" != "skip" ]; then
  echo "========================================"
  echo "Starting SFT stage..."
  echo "Model: $model_name_or_path"
  echo "Dataset: $sft_dataset"
  echo "Output: $sft_output_dir"
  echo "========================================"

  llamafactory-cli train "$sft_config" \
    model_name_or_path="$model_name_or_path" \
    dataset="$sft_dataset" \
    output_dir="$sft_output_dir" \
    run_name="qwen2_5-${model_id}-full-sft-${sft_dataset}" \
    per_device_train_batch_size="$sft_batch_size" \
    gradient_accumulation_steps="$sft_gradient_accumulation_steps"
else
  echo "========================================"
  echo "Skipping SFT stage (as requested)"
  echo "Using existing model: $sft_output_dir"
  echo "========================================"
  
  # Check if SFT model exists
  if [ ! -d "$sft_output_dir" ]; then
    echo "Error: SFT output directory not found: $sft_output_dir"
    echo "Please run SFT first or remove the 'skip' parameter."
    exit 1
  fi
fi

# Learning rates to test
lrs=(
  5e-7
  1e-6
  5e-6
  1e-5
)

export FORCE_TORCHRUN=1

# Function to run preference optimization
run_preference_optimization() {
  local opt_method="$1"
  local config_file="examples/train_full/qwen2_5_full_${opt_method}_UFB_clean.yaml"
  
  echo ""
  echo "========================================"
  echo "Starting ${opt_method^^} stage..."
  echo "Model from SFT: $sft_output_dir"
  echo "Dataset: $pref_dataset"
  echo "========================================"
  
  for lr in "${lrs[@]}"; do
    lr_token=$(printf "%s" "$lr" | sed 's/\./p/g')
    output_dir="saves/qwen2_5-${model_id}/full/${opt_method}/${pref_dataset}/lr_${lr_token}"
    run_name="qwen2_5-${model_id}-full-${opt_method}-${pref_dataset}-lr-${lr_token}"
    
    echo "----------------------------------------"
    echo "${opt_method^^} iteration with learning_rate=$lr"
    echo "----------------------------------------"
    
    llamafactory-cli train "$config_file" \
      model_name_or_path="$sft_output_dir" \
      dataset="$pref_dataset" \
      learning_rate="$lr" \
      output_dir="$output_dir" \
      run_name="$run_name" \
      per_device_train_batch_size="$pref_batch_size"
    
    # Keep artifacts organized per run
    mkdir -p "$output_dir"
    mv /data2/zonglin/temp/LLaMA-Factory/*.pkl "$output_dir"/ 2>/dev/null || true
  done
  
  echo ""
  echo "========================================"
  echo "${opt_method^^} stage completed!"
  echo "Output directory: saves/qwen2_5-${model_id}/full/${opt_method}/${pref_dataset}/"
  echo "========================================"
}

# Run preference optimization based on method parameter
case "$method" in
  dpo)
    run_preference_optimization "dpo"
    ;;
  ropo)
    run_preference_optimization "ropo"
    ;;
  both)
    run_preference_optimization "dpo"
    run_preference_optimization "ropo"
    ;;
esac

echo ""
echo "========================================"
echo "Training completed successfully!"
echo "========================================"
echo "Model: $model_name_or_path (${model_id})"
echo "SFT output: $sft_output_dir"

if [ "$method" = "dpo" ] || [ "$method" = "both" ]; then
  echo "DPO outputs: saves/qwen2_5-${model_id}/full/dpo/${pref_dataset}/"
fi

if [ "$method" = "ropo" ] || [ "$method" = "both" ]; then
  echo "ROPO outputs: saves/qwen2_5-${model_id}/full/ropo/${pref_dataset}/"
fi

echo "========================================"
