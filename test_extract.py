#!/usr/bin/env python3
"""
测试脚本 - 验证交付包提取功能
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.extractors.package_extractor import PackageExtractor


def test_extract():
    """测试提取交付包"""

    # 使用示例交付包
    package_path = "/Users/a123/Desktop/新时代三件套-交付包-重制版"

    print(f"正在测试交付包: {package_path}\n")
    print("=" * 60)

    try:
        extractor = PackageExtractor(package_path)
        metadata = extractor.extract()

        print(f"✅ 提取成功!\n")
        print(f"📌 标题: {metadata.title}")
        print(f"🎬 视频: {metadata.video_path.name}")
        print(f"🖼️  封面: {metadata.cover_path.name if metadata.cover_path else '无'}")
        print(f"📝 字幕: {metadata.subtitle_path.name if metadata.subtitle_path else '无'}")
        print(f"🏷️  标签: {', '.join(metadata.tags[:8])}")

        print("\n平台特定配置:")
        print("-" * 60)

        if metadata.platform_titles:
            for platform, title in metadata.platform_titles.items():
                print(f"  {platform:15s} 标题: {title}")

        if metadata.platform_descriptions:
            print("\n平台描述:")
            for platform, desc in metadata.platform_descriptions.items():
                preview = desc[:60] + "..." if len(desc) > 60 else desc
                print(f"  {platform:15s}: {preview}")

        if metadata.pinned_comment:
            print(f"\n💬 置顶评论: {metadata.pinned_comment}")

        print("\n" + "=" * 60)
        print("✅ 所有字段提取正常，可以开始发布!")

    except Exception as e:
        print(f"❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_extract()
