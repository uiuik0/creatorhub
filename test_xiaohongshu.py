#!/usr/bin/env python3
"""
测试小红书发布功能
"""
import asyncio
import json
from pathlib import Path
from loguru import logger

from src.publishers.xiaohongshu_publisher import XiaohongshuPublisher
from src.extractors.package_extractor import VideoMetadata


async def test_xiaohongshu():
    """测试小红书发布"""

    # 读取配置
    config_path = Path("config/platforms.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    xhs_config = config['xiaohongshu']

    print(f"小红书配置:")
    print(f"  启用: {xhs_config['enabled']}")
    print(f"  Cookie 长度: {len(xhs_config.get('cookie', ''))}")
    print(f"  a1: {xhs_config.get('a1', 'N/A')}")

    if not xhs_config['enabled']:
        print("\n❌ 小红书未启用")
        return

    if not xhs_config.get('cookie'):
        print("\n❌ 小红书 cookie 未配置")
        return

    # 创建发布器
    print("\n创建小红书发布器...")
    try:
        publisher = XiaohongshuPublisher(
            cookie=xhs_config['cookie'],
            a1=xhs_config.get('a1')
        )
        print("✅ 发布器创建成功")
        print(f"Client 类型: {type(publisher.client)}")
        print(f"Client 是否为 None: {publisher.client is None}")

        # 测试 get_suggest_topic 方法
        print("\n测试 get_suggest_topic 方法...")
        print(f"方法类型: {type(publisher.client.get_suggest_topic)}")
        print(f"是否可调用: {callable(publisher.client.get_suggest_topic)}")

        # 尝试调用一次
        print("\n尝试获取话题 'AI'...")
        result = publisher.client.get_suggest_topic("AI")
        print(f"✅ 话题获取成功，结果数量: {len(result)}")
        if result:
            print(f"第一个话题: {result[0]}")

    except Exception as e:
        print(f"❌ 发布器创建失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 准备测试数据
    package_path = Path("/Users/a123/Desktop/新时代三件套-交付包-重制版")

    if not package_path.exists():
        print(f"\n❌ 交付包不存在: {package_path}")
        return

    video_path = package_path / "成片.mp4"
    cover_path = package_path / "封面.png"

    if not video_path.exists():
        print(f"\n❌ 视频文件不存在: {video_path}")
        return

    print(f"\n准备测试发布:")
    print(f"  视频: {video_path}")
    print(f"  封面: {cover_path}")

    # 创建测试元数据
    metadata = VideoMetadata(
        title="新时代三件套，普通人怎么把机会接起来？",
        description="自媒体解决被看见，AI 解决一个人怎么做更多，金融解决赚到的钱怎么走得久。",
        video_path=video_path,
        cover_path=cover_path if cover_path.exists() else None,
        tags=["自媒体", "AI工具", "个人成长"],
        platform_descriptions={
            'xiaohongshu': "自媒体解决被看见，AI 解决一个人怎么做更多，金融解决赚到的钱怎么走得久。先做一个小问题，连续输出七天，再用 AI 复盘。金融内容仅作风险教育。"
        }
    )

    # 测试发布（注释掉实际发布，只测试到话题获取）
    print("\n开始测试发布流程...")
    try:
        result = await publisher.publish(metadata)
        print(f"\n发布结果: {json.dumps(result, indent=2, ensure_ascii=False)}")

        if result['status'] == 'success':
            print("\n✅ 发布成功!")
        else:
            print(f"\n❌ 发布失败: {result.get('error')}")

    except Exception as e:
        print(f"\n❌ 发布过程出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_xiaohongshu())
