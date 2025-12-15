#!/usr/bin/env python3
"""
脚本用于分析JSON文件中的chosen_score和rejected_score
统计分数信息并计算chosen_score > rejected_score的比例
"""

import json
import sys
from typing import Dict, List, Any
import statistics


def analyze_scores(json_file: str) -> Dict[str, Any]:
    """
    分析JSON文件中的chosen_score和rejected_score
    
    Args:
        json_file: JSON文件路径
        
    Returns:
        包含统计信息的字典
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 统计变量
    total_points = len(data)
    points_with_scores = 0
    chosen_scores = []
    rejected_scores = []
    chosen_greater_count = 0
    chosen_equal_count = 0
    chosen_less_count = 0
    
    # 遍历每个数据点
    for item in data:
        if 'chosen_score' in item and 'rejected_score' in item:
            points_with_scores += 1
            chosen_score = item['chosen_score']
            rejected_score = item['rejected_score']
            
            chosen_scores.append(chosen_score)
            rejected_scores.append(rejected_score)
            
            # 统计比较结果
            if chosen_score > rejected_score:
                chosen_greater_count += 1
            elif chosen_score == rejected_score:
                chosen_equal_count += 1
            else:
                chosen_less_count += 1
    
    # 计算统计信息
    results = {
        'total_points': total_points,
        'points_with_scores': points_with_scores,
        'points_without_scores': total_points - points_with_scores,
        'chosen_greater_ratio': chosen_greater_count / points_with_scores if points_with_scores > 0 else 0,
        'chosen_equal_ratio': chosen_equal_count / points_with_scores if points_with_scores > 0 else 0,
        'chosen_less_ratio': chosen_less_count / points_with_scores if points_with_scores > 0 else 0,
        'chosen_greater_count': chosen_greater_count,
        'chosen_equal_count': chosen_equal_count,
        'chosen_less_count': chosen_less_count,
    }
    
    # 如果有分数数据，计算统计量
    if chosen_scores:
        results['chosen_score_stats'] = {
            'count': len(chosen_scores),
            'mean': statistics.mean(chosen_scores),
            'median': statistics.median(chosen_scores),
            'min': min(chosen_scores),
            'max': max(chosen_scores),
            'stdev': statistics.stdev(chosen_scores) if len(chosen_scores) > 1 else 0
        }
        
        results['rejected_score_stats'] = {
            'count': len(rejected_scores),
            'mean': statistics.mean(rejected_scores),
            'median': statistics.median(rejected_scores),
            'min': min(rejected_scores),
            'max': max(rejected_scores),
            'stdev': statistics.stdev(rejected_scores) if len(rejected_scores) > 1 else 0
        }
    
    return results


def print_results(results: Dict[str, Any], json_file: str):
    """
    打印统计结果
    
    Args:
        results: 统计结果字典
        json_file: 输入文件路径
    """
    print(f"=" * 60)
    print(f"分析文件: {json_file}")
    print(f"=" * 60)
    print()
    
    print(f"总数据点数: {results['total_points']}")
    print(f"包含分数的数据点数: {results['points_with_scores']}")
    print(f"不包含分数的数据点数: {results['points_without_scores']}")
    print()
    
    if results['points_with_scores'] > 0:
        print(f"比较结果统计:")
        print(f"  chosen_score > rejected_score: {results['chosen_greater_count']} ({results['chosen_greater_ratio']*100:.2f}%)")
        print(f"  chosen_score = rejected_score: {results['chosen_equal_count']} ({results['chosen_equal_ratio']*100:.2f}%)")
        print(f"  chosen_score < rejected_score: {results['chosen_less_count']} ({results['chosen_less_ratio']*100:.2f}%)")
        print()
        
        if 'chosen_score_stats' in results:
            print(f"chosen_score 统计:")
            stats = results['chosen_score_stats']
            print(f"  数量: {stats['count']}")
            print(f"  平均值: {stats['mean']:.4f}")
            print(f"  中位数: {stats['median']:.4f}")
            print(f"  最小值: {stats['min']:.4f}")
            print(f"  最大值: {stats['max']:.4f}")
            print(f"  标准差: {stats['stdev']:.4f}")
            print()
            
            print(f"rejected_score 统计:")
            stats = results['rejected_score_stats']
            print(f"  数量: {stats['count']}")
            print(f"  平均值: {stats['mean']:.4f}")
            print(f"  中位数: {stats['median']:.4f}")
            print(f"  最小值: {stats['min']:.4f}")
            print(f"  最大值: {stats['max']:.4f}")
            print(f"  标准差: {stats['stdev']:.4f}")
            print()
        
        print(f"=" * 60)
        print(f"关键指标: chosen_score > rejected_score 的比例 = {results['chosen_greater_ratio']*100:.2f}%")
        print(f"=" * 60)
    else:
        print("警告: 没有找到包含chosen_score和rejected_score的数据点")


def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python analyze_scores.py <json_file>")
        print("示例: python analyze_scores.py my_test_with_scores.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    try:
        results = analyze_scores(json_file)
        print_results(results, json_file)
    except FileNotFoundError:
        print(f"错误: 文件 '{json_file}' 不存在")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"错误: JSON解析失败 - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

