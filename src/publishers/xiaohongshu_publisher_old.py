"""
小红书发布器 - 使用 xhs 库上传
"""
import asyncio
from pathlib import Path
from typing import Optional, List
from loguru import logger
from xhs import XhsClient

from extractors.package_extractor import VideoMetadata


class XiaohongshuPublisher:
    """小红书视频发布器（使用 xhs API）"""

    def __init__(self, cookie: str, a1: Optional[str] = None):
        """
        初始化小红书发布器

        Args:
            cookie: 小红书 cookie 字符串
            a1: 可选的 a1 参数用于签名
        """
        self.client = XhsClient(cookie=cookie)
        self.a1 = a1

    async def publish(self, metadata: VideoMetadata) -> dict:
        """
        发布视频到小红书

        Args:
            metadata: 视频元数据

        Returns:
            发布结果字典
        """
        try:
            # 准备标题
            title = metadata.platform_titles.get('xiaohongshu', metadata.title)
            title = self._truncate_title(title, 20)

            # 准备描述
            desc = metadata.platform_descriptions.get('xiaohongshu', metadata.description)
            desc = self._truncate_desc(desc, 1000)

            # 准备标签（话题）
            topics = []
            if metadata.tags:
                # 搜索话题并获取话题ID
                for tag in metadata.tags[:10]:
                    try:
                        # 注意：xhs 库的方法可能不支持话题搜索
                        # 暂时跳过话题功能，直接使用标签文本
                        if hasattr(self.client, 'get_suggest_topic') and callable(self.client.get_suggest_topic):
                            topic_results = self.client.get_suggest_topic(tag)
                            if topic_results and len(topic_results) > 0:
                                # 使用第一个匹配的话题
                                topic = topic_results[0]
                                topics.append({
                                    "id": topic.get("id", ""),
                                    "name": topic.get("name", tag),
                                    "type": "topic"
                                })
                    except Exception as e:
                        logger.debug(f"跳过话题 '{tag}': {e}")

            logger.info(f"开始上传到小红书: {title}")
            logger.debug(f"视频路径: {metadata.video_path}")
            logger.debug(f"标题: {title}")
            logger.debug(f"描述: {desc}")
            logger.debug(f"话题: {topics}")

            # 在异步上下文中调用同步方法
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self._publish_video_sync,
                title,
                str(metadata.video_path),
                desc,
                str(metadata.cover_path) if metadata.cover_path else None,
                topics
            )

            logger.success(f"小红书上传成功: {title}")
            return {
                "status": "success",
                "platform": "xiaohongshu",
                "title": title,
                "note_id": result.get("note_id", ""),
            }

        except Exception as e:
            logger.error(f"小红书上传失败: {e}")
            return {
                "status": "error",
                "platform": "xiaohongshu",
                "error": str(e)
            }

    def _publish_video_sync(
        self,
        title: str,
        video_path: str,
        desc: str,
        cover_path: Optional[str],
        topics: List[dict]
    ) -> dict:
        """
        同步发布视频（在线程池中执行）

        Args:
            title: 标题
            video_path: 视频路径
            desc: 描述
            cover_path: 封面路径
            topics: 话题列表

        Returns:
            发布结果
        """
        return self.client.create_video_note(
            title=title,
            video_path=video_path,
            desc=desc,
            cover_path=cover_path,
            topics=topics,
            is_private=False
        )

    def _truncate_title(self, title: str, max_length: int) -> str:
        """截断标题"""
        if len(title) <= max_length:
            return title
        return title[:max_length-3] + "..."

    def _truncate_desc(self, desc: str, max_length: int) -> str:
        """截断描述"""
        if len(desc) <= max_length:
            return desc
        return desc[:max_length-3] + "..."
