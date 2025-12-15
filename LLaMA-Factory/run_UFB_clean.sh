#!/usr/bin/env bash

set -euo pipefail

# Config for all runs
config="examples/train_full/qwen2_5_full_dpo_UFB_clean.yaml"

# Datasets to iterate over
datasets=(
  UFB_clean_train
  UFB_clean_train_with_scores_0_3
  UFB_clean_train_with_scores_0_4
  UFB_clean_train_with_scores_0_3_all_flipped
  UFB_clean_train_with_scores_0_4_all_flipped
)

# Learning rates to iterate over
lrs=(
  5e-7
  1e-6
  5e-6
  1e-5
)

for dataset in "${datasets[@]}"; do
  for lr in "${lrs[@]}"; do
    # Replace dots so the value is safe to embed in paths
    lr_token=$(printf "%s" "$lr" | sed 's/\./p/g')
    output_dir="saves/qwen2_5-0_5b/full/${dataset}/lr_${lr_token}"
    run_name="qwen2_5-0_5b-full-${dataset}-lr-${lr_token}"

    llamafactory-cli train "$config" \
      dataset="$dataset" \
      learning_rate="$lr" \
      output_dir="$output_dir" \
      run_name="$run_name"

    # Keep artifacts organized per run
    mkdir -p "$output_dir"
    mv /data2/zonglin/temp/LLaMA-Factory/*.pkl "$output_dir"/
  done
done


