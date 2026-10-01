#!/usr/bin/env python3
"""
完整示例 - 演示如何使用发布工具
"""
import asyncio
from pathlib import Path
from src.extractors.package_extractor import PackageExtractor
from src.publishers.bilibili_publisher import BilibiliPublisher


async def example_bilibili():
    """示例：发布到B站"""

    # 1. 提取交付包
    package_path = "/Users/a123/Desktop/新时代三件套-交付包-重制版"
    extractor = PackageExtractor(package_path)
    metadata = extractor.extract()

    print(f"标题: {metadata.title}")
    print(f"视频: {metadata.video_path}")
    print(f"标签: {metadata.tags}")

    # 2. 配置发布器
    publisher = BilibiliPublisher(
        cookies="你的_SESSDATA",
        csrf="你的_bili_jct"
    )

    # 3. 发布
    result = await publisher.publish(metadata)

    print(f"发布结果: {result}")


async def example_custom_metadata():
    """示例：自定义元数据"""
    from src.extractors.package_extractor import VideoMetadata
    from pathlib import Path

    # 手动创建元数据
    metadata = VideoMetadata(
        title="我的自定义标题",
        description="这是一个测试视频",
        video_path=Path("/path/to/video.mp4"),
        cover_path=Path("/path/to/cover.png"),
        tags=["测试", "视频", "自动化"],
        platform_titles={
            "bilibili": "B站专用标题",
            "douyin": "抖音专用标题",
        }
    )

    # 发布
    publisher = BilibiliPublisher(cookies="...", csrf="...")
    result = await publisher.publish(metadata)
    print(result)


if __name__ == '__main__':
    print("示例1: 发布到B站")
    print("-" * 60)
    # asyncio.run(example_bilibili())

    print("\n示例2: 自定义元数据")
    print("-" * 60)
    # asyncio.run(example_custom_metadata())

    print("\n提示: 取消注释上面的代码来运行示例")
