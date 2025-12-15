#!/usr/bin/env python3
"""
脚本用于翻转JSON文件中chosen_score低于rejected_score的数据点。
当chosen_score < rejected_score时，交换chosen_score和rejected_score的值，
同时交换chosen和rejected的内容。
"""

import json
import argparse
import sys
from pathlib import Path


def flip_data_point(data_point):
    """
    翻转单个数据点：如果chosen_score < rejected_score，
    则交换chosen_score和rejected_score，以及chosen和rejected。

    Args:
        data_point: 包含chosen_score和rejected_score的字典

    Returns:
        翻转后的数据点
    """
    if "chosen_score" not in data_point or "rejected_score" not in data_point:
        return data_point

    chosen_score = data_point["chosen_score"]
    rejected_score = data_point["rejected_score"]

    # 如果chosen_score低于rejected_score，需要翻转
    if chosen_score < rejected_score:
        # 交换分数
        data_point["chosen_score"], data_point["rejected_score"] = (
            rejected_score,
            chosen_score,
        )

        # 交换chosen和rejected的内容
        if "chosen" in data_point and "rejected" in data_point:
            data_point["chosen"], data_point["rejected"] = (
                data_point["rejected"],
                data_point["chosen"],
            )

    return data_point


def process_json_file(input_file, output_file=None):
    """
    处理JSON文件，翻转所有需要翻转的数据点。

    Args:
        input_file: 输入JSON文件路径
        output_file: 输出JSON文件路径，如果为None则使用默认命名（原文件名_all_flipped.json）
    """
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"错误: 文件 {input_file} 不存在", file=sys.stderr)
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

    # 处理每个数据点
    flipped_count = 0
    total_count = len(data)

    print(f"总共 {total_count} 个数据点")

    for i, data_point in enumerate(data):
        if not isinstance(data_point, dict):
            continue

        original_chosen_score = data_point.get("chosen_score")
        original_rejected_score = data_point.get("rejected_score")

        if original_chosen_score is None or original_rejected_score is None:
            continue

        # 如果需要翻转
        if original_chosen_score < original_rejected_score:
            flip_data_point(data_point)
            flipped_count += 1

    print(f"翻转了 {flipped_count} 个数据点")

    # 确定输出文件路径
    if output_file is None:
        # 生成默认输出文件名：原文件名 + _all_flipped + 扩展名
        stem = input_path.stem
        suffix = input_path.suffix
        output_path = input_path.parent / f"{stem}_all_flipped{suffix}"
        print(f"将保存到: {output_path}")
    else:
        output_path = Path(output_file)
        print(f"将保存到: {output_file}")

    # 写入结果
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("处理完成!")
    except Exception as e:
        print(f"错误: 写入文件失败 - {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="翻转JSON文件中chosen_score低于rejected_score的数据点",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python flip_scores.py input.json
  python flip_scores.py input.json -o output.json
  python flip_scores.py input.json --output output.json
        """,
    )

    parser.add_argument("input_file", type=str, help="输入的JSON文件路径")

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        dest="output_file",
        help="输出的JSON文件路径（如果不指定，默认在原文件名后添加_all_flipped后缀）",
    )

    args = parser.parse_args()

    process_json_file(args.input_file, args.output_file)


if __name__ == "__main__":
    main()
