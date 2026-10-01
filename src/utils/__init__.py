"""工具函数"""
from pathlib import Path


def find_files_by_pattern(directory: Path, patterns: list) -> list:
    """
    根据模式列表查找文件

    Args:
        directory: 搜索目录
        patterns: glob 模式列表

    Returns:
        匹配的文件路径列表
    """
    results = []
    for pattern in patterns:
        results.extend(directory.glob(pattern))
    return results


def format_duration(seconds: float) -> str:
    """
    格式化时长

    Args:
        seconds: 秒数

    Returns:
        格式化的时长字符串 (MM:SS)
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"
