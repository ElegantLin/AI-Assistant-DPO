#!/usr/bin/env bash

set -euo pipefail

# Parse command line arguments
if [ "$#" -lt 1 ] || [ "$#" -gt 3 ]; then
  echo "Usage: $0 <model_size> [sft_dataset] [ropo_dataset]"
  echo ""
  echo "Arguments:"
  echo "  model_size   : Model size (required). Options: 0_5b, 3b, 7b, 14b, 32b"
  echo "  sft_dataset  : SFT dataset name (optional, default: UFB_clean_train_sft)"
  echo "  ropo_dataset : ROPO dataset name (optional, default: UFB_clean_train)"
  echo ""
  echo "Examples:"
  echo "  $0 0_5b"
  echo "  $0 3b UFB_clean_train_sft UFB_clean_train"
  echo "  $0 7b my_sft_dataset my_ropo_dataset"
  echo ""
  exit 1
fi

model_id="$1"
sft_dataset="${2:-UFB_clean_train_sft}"
ropo_dataset="${3:-UFB_clean_train}"

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
echo "Model Configuration"
echo "========================================"
echo "Model ID: $model_id"
echo "Model: $model_name_or_path"
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
    sft_batch_size=8
    ropo_batch_size=1
    ;;
  4)
    sft_batch_size=16
    ropo_batch_size=2
    ;;
  2)
    sft_batch_size=32
    ropo_batch_size=4
    ;;
  1)
    sft_batch_size=64
    ropo_batch_size=8
    ;;
  *)
    echo "Warning: Unsupported GPU count ($num_gpus), using defaults for 1 GPU"
    sft_batch_size=8
    ropo_batch_size=1
    ;;
esac

echo "========================================"
echo "System Configuration"
echo "========================================"
echo "Number of GPUs: $num_gpus"
echo "SFT per_device_train_batch_size: $sft_batch_size"
echo "ROPO per_device_train_batch_size: $ropo_batch_size"
echo ""

# SFT configurations
sft_config="examples/train_full/qwen2_5_full_sft.yaml"
sft_output_dir="saves/qwen2_5-${model_id}/full/sft/${sft_dataset}"

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
  per_device_train_batch_size="$sft_batch_size"

# ROPO configurations
ropo_config="examples/train_full/qwen2_5_full_ropo_UFB_clean.yaml"
lrs=(
  5e-7
  1e-6
  5e-6
  1e-5
)

echo ""
echo "========================================"
echo "Starting ROPO stage..."
echo "Model from SFT: $sft_output_dir"
echo "Dataset: $ropo_dataset"
echo "========================================"

export FORCE_TORCHRUN=1

for lr in "${lrs[@]}"; do
  lr_token=$(printf "%s" "$lr" | sed 's/\./p/g')
  output_dir="saves/qwen2_5-${model_id}/full/ropo/${ropo_dataset}/lr_${lr_token}"
  run_name="qwen2_5-${model_id}-full-ropo-${ropo_dataset}-lr-${lr_token}"

  echo "----------------------------------------"
  echo "ROPO iteration with learning_rate=$lr"
  echo "----------------------------------------"

  llamafactory-cli train "$ropo_config" \
    model_name_or_path="$sft_output_dir" \
    dataset="$ropo_dataset" \
    learning_rate="$lr" \
    output_dir="$output_dir" \
    run_name="$run_name" \
    per_device_train_batch_size="$ropo_batch_size"

  # Keep artifacts organized per run
  mkdir -p "$output_dir"
  mv /data2/zonglin/temp/LLaMA-Factory/*.pkl "$output_dir"/ 2>/dev/null || true
done

echo ""
echo "========================================"
echo "Training completed successfully!"
echo "========================================"
echo "Model: $model_name_or_path (${model_id})"
echo "SFT output: $sft_output_dir"
echo "ROPO outputs: saves/qwen2_5-${model_id}/full/ropo/${ropo_dataset}/"
echo "========================================"
