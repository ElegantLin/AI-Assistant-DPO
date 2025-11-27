conda init
conda activate llama-slow
for lr in 2e-6 3e-6 4e-6; do
    lr_token=$(printf "%s" "$lr" | sed 's/\./p/g')
    output_dir="saves/qwen2_5-0_5b/full/ropo_train_ai_flipped_20K_200_steps_lr_${lr_token}_new_results"
    run_name="qwen2_5-0_5b-full-ropo-train-ai-flipped-20K-200-steps-lr-${lr_token}-new-results"

    llamafactory-cli train examples/train_full/qwen2_5_full_ropo_new_results.yaml \
        learning_rate="$lr" \
        output_dir="$output_dir" \
        run_name="$run_name"

    mkdir -p "$output_dir"
    mv /data2/zonglin/temp/LLaMA-Factory/*.pkl "$output_dir"/
done

# for lr in 1e-6 5e-7 1e-7; do
#     lr_token=$(printf "%s" "$lr" | sed 's/\./p/g')
#     output_dir="saves/qwen2_5-0_5b/full/dpo_train_28K_lr_${lr_token}"
#     run_name="qwen2_5-0_5b-full-dpo-train-28K-lr_${lr_token}"

#     llamafactory-cli train examples/train_full/qwen2_5_full_dpo_20K.yaml \
#         dataset="dpo_train_data_28K" \
#         learning_rate="$lr" \
#         output_dir="$output_dir" \
#         run_name="$run_name"

#     mkdir -p "$output_dir"
#     mv /data2/zonglin/temp/LLaMA-Factory/*.pkl "$output_dir"/
# done