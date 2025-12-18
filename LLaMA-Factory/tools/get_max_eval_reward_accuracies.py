#!/usr/bin/env python3
"""
工具脚本：从jsonl文件中提取指定name的eval_rewards_accuracies最大值

用法:
    python get_max_eval_rewards_accuracies.py <jsonl_path> <name>

示例:
    python get_max_eval_rewards_accuracies.py trainer_log.jsonl eval_UFB_clean_val_loss
"""

import json
import sys
from typing import Optional


def get_max_eval_rewards_accuracies(jsonl_path: str, name: str) -> Optional[float]:
    """
    从jsonl文件中提取指定name的eval_rewards_accuracies最大值

    Args:
        jsonl_path: jsonl文件路径
        name: 要查找的name字段值

    Returns:
        该name对应的eval_rewards_accuracies最大值，如果未找到则返回None
    """
    max_value = None

    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    # 检查name字段是否匹配
                    if data.get("name") == name and "eval_rewards_accuracies" in data:
                        value = data["eval_rewards_accuracies"]
                        if max_value is None or value > max_value:
                            max_value = value
                except json.JSONDecodeError:
                    # 跳过无效的JSON行
                    continue

    except FileNotFoundError:
        print(f"错误: 文件 '{jsonl_path}' 不存在", file=sys.stderr)
        return None
    except Exception as e:
        print(f"错误: 读取文件时发生异常: {e}", file=sys.stderr)
        return None

    return max_value


def main():
    """主函数"""
    if len(sys.argv) != 3:
        print(
            "用法: python get_max_eval_rewards_accuracies.py <jsonl_path> <name>",
            file=sys.stderr,
        )
        print(
            "示例: python get_max_eval_rewards_accuracies.py trainer_log.jsonl eval_UFB_clean_val_loss",
            file=sys.stderr,
        )
        sys.exit(1)

    jsonl_path = sys.argv[1]
    name = sys.argv[2]

    max_value = get_max_eval_rewards_accuracies(jsonl_path, name)

    if max_value is not None:
        print(max_value)
    else:
        print(
            f"未找到name='{name}'的记录或该记录中没有eval_rewards_accuracies字段",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
