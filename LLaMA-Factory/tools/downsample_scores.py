#!/usr/bin/env python3
"""
脚本用于下采样JSON文件，使得chosen_score < rejected_score的数据点
达到整个数据集的比例为x。
"""

import json
import argparse
import sys
import random
from pathlib import Path


def downsample_dataset(data, target_ratio):
    """
    下采样数据集，使得chosen_score < rejected_score的数据点占比为target_ratio。
    
    Args:
        data: 数据列表，每个元素包含chosen_score和rejected_score
        target_ratio: 目标比例（0-1之间的浮点数）
    
    Returns:
        下采样后的数据列表
    """
    # 分离两类数据点
    less_than = []  # chosen_score < rejected_score
    greater_equal = []  # chosen_score >= rejected_score
    
    for item in data:
        if not isinstance(item, dict):
            continue
        
        if "chosen_score" not in item or "rejected_score" not in item:
            # 如果没有分数，保留这些数据点
            greater_equal.append(item)
            continue
        
        chosen_score = item["chosen_score"]
        rejected_score = item["rejected_score"]
        
        if chosen_score < rejected_score:
            less_than.append(item)
        else:
            greater_equal.append(item)
    
    total_less = len(less_than)
    total_greater_equal = len(greater_equal)
    
    print(f"原始数据统计:")
    print(f"  chosen_score < rejected_score: {total_less} 个")
    print(f"  chosen_score >= rejected_score: {total_greater_equal} 个")
    print(f"  总计: {len(data)} 个")
    
    if total_less == 0:
        print("警告: 没有找到 chosen_score < rejected_score 的数据点")
        return data
    
    # 计算下采样后的数据点数量
    # 设下采样后总数为N，其中less_than的数量为L，则L/N = target_ratio
    # 所以 N = L / target_ratio
    # 但我们需要同时考虑两类数据点的数量限制
    
    # 策略：先确定less_than需要保留的数量，然后根据比例计算greater_equal需要保留的数量
    # 如果less_than的数量不足以达到目标比例，则保留所有less_than
    
    # 计算需要的less_than数量（基于greater_equal的数量）
    # 如果保留所有greater_equal，需要的less_than数量为：
    # target_ratio = less_count / (less_count + greater_equal_count)
    # less_count = target_ratio * (less_count + greater_equal_count)
    # less_count = target_ratio * less_count + target_ratio * greater_equal_count
    # less_count * (1 - target_ratio) = target_ratio * greater_equal_count
    # less_count = target_ratio * greater_equal_count / (1 - target_ratio)
    
    if target_ratio >= 1.0:
        # 如果目标比例是1.0，只保留less_than的数据点
        print(f"目标比例为1.0，只保留 chosen_score < rejected_score 的数据点")
        return less_than
    
    if target_ratio <= 0.0:
        # 如果目标比例是0.0，只保留greater_equal的数据点
        print(f"目标比例为0.0，只保留 chosen_score >= rejected_score 的数据点")
        return greater_equal
    
    # 计算需要的less_than数量
    # 基于公式：target_ratio = less_count / (less_count + greater_equal_count)
    # 如果保留所有greater_equal，需要的less_than数量：
    required_less = int(target_ratio * total_greater_equal / (1 - target_ratio))
    
    # 如果需要的数量超过实际数量，则保留所有less_than，并相应减少greater_equal
    if required_less > total_less:
        # 保留所有less_than，计算需要的greater_equal数量
        # target_ratio = total_less / (total_less + greater_count)
        # greater_count = total_less * (1 - target_ratio) / target_ratio
        required_greater_equal = int(total_less * (1 - target_ratio) / target_ratio)
        required_less = total_less
    else:
        required_greater_equal = total_greater_equal
    
    # 确保不超过实际数量
    required_less = min(required_less, total_less)
    required_greater_equal = min(required_greater_equal, total_greater_equal)
    
    print(f"\n下采样策略:")
    print(f"  目标比例: {target_ratio:.4f} ({target_ratio*100:.2f}%)")
    print(f"  保留 chosen_score < rejected_score: {required_less} / {total_less}")
    print(f"  保留 chosen_score >= rejected_score: {required_greater_equal} / {total_greater_equal}")
    
    # 随机下采样
    random.shuffle(less_than)
    random.shuffle(greater_equal)
    
    sampled_less = less_than[:required_less]
    sampled_greater_equal = greater_equal[:required_greater_equal]
    
    # 合并结果
    result = sampled_less + sampled_greater_equal
    
    # 随机打乱最终结果
    random.shuffle(result)
    
    # 验证最终比例
    final_less = sum(1 for item in result 
                     if isinstance(item, dict) 
                     and "chosen_score" in item 
                     and "rejected_score" in item
                     and item["chosen_score"] < item["rejected_score"])
    final_ratio = final_less / len(result) if len(result) > 0 else 0
    
    print(f"\n下采样后统计:")
    print(f"  总数据点数: {len(result)}")
    print(f"  chosen_score < rejected_score: {final_less} 个")
    print(f"  实际比例: {final_ratio:.4f} ({final_ratio*100:.2f}%)")
    
    return result


def process_json_file(input_file, target_ratio, output_file=None):
    """
    处理JSON文件，进行下采样。
    
    Args:
        input_file: 输入JSON文件路径
        target_ratio: 目标比例（0-1之间的浮点数）
        output_file: 输出JSON文件路径，如果为None则使用默认命名
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"错误: 文件 {input_file} 不存在", file=sys.stderr)
        sys.exit(1)
    
    # 验证目标比例
    if target_ratio < 0.0 or target_ratio > 1.0:
        print(f"错误: 目标比例必须在0.0到1.0之间，当前值: {target_ratio}", file=sys.stderr)
        sys.exit(1)
    
    # 读取JSON文件
    print(f"正在读取文件: {input_file}")
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误: JSON解析失败 - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误: 读取文件失败 - {e}", file=sys.stderr)
        sys.exit(1)
    
    # 确保数据是列表格式
    if not isinstance(data, list):
        print("错误: JSON文件应该包含一个数组", file=sys.stderr)
        sys.exit(1)
    
    # 下采样
    sampled_data = downsample_dataset(data, target_ratio)
    
    # 确定输出文件路径
    if output_file is None:
        # 生成默认输出文件名：原文件名 + _x + 扩展名
        stem = input_path.stem
        suffix = input_path.suffix
        # 将比例转换为字符串，去掉小数点（例如0.3 -> 0_3，0.15 -> 0_15）
        ratio_str = str(target_ratio).replace(".", "_")
        output_path = input_path.parent / f"{stem}_{ratio_str}{suffix}"
        print(f"\n将保存到: {output_path}")
    else:
        output_path = Path(output_file)
        print(f"\n将保存到: {output_file}")
    
    # 写入结果
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sampled_data, f, ensure_ascii=False, indent=2)
        print("处理完成!")
    except Exception as e:
        print(f"错误: 写入文件失败 - {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="下采样JSON文件，使得chosen_score < rejected_score的数据点占比为目标比例",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python downsample_scores.py input.json 0.3
  python downsample_scores.py input.json 0.3 -o output.json
  python downsample_scores.py input.json 0.3 --output output.json
        """,
    )
    
    parser.add_argument("input_file", type=str, help="输入的JSON文件路径")
    parser.add_argument(
        "target_ratio",
        type=float,
        help="目标比例（0.0-1.0之间的浮点数），表示chosen_score < rejected_score的数据点占比",
    )
    
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        dest="output_file",
        help="输出的JSON文件路径（如果不指定，默认在原文件名后添加_比例后缀）",
    )
    
    args = parser.parse_args()
    
    process_json_file(args.input_file, args.target_ratio, args.output_file)


if __name__ == "__main__":
    main()


