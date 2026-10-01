"""
B站发布器 - 使用 bilibili-api 上传视频
"""
import asyncio
from pathlib import Path
from typing import Optional
from loguru import logger
from bilibili_api import video_uploader, Credential
from bilibili_api.video_uploader import VideoUploaderPage
from PIL import Image

from extractors.package_extractor import VideoMetadata


class BilibiliPublisher:
    """B站视频发布器"""

    def __init__(self, cookies: str, csrf: str):
        self.credential = Credential(sessdata=cookies, bili_jct=csrf)

    async def publish(self, metadata: VideoMetadata, cover_path: Optional[Path] = None) -> dict:
        """
        发布视频到B站

        Args:
            metadata: 视频元数据
            cover_path: 封面图路径（可选，会自动调整尺寸）

        Returns:
            发布结果字典
        """
        try:
            # 准备标题
            title = metadata.platform_titles.get('bilibili', metadata.title)
            title = self._truncate_title(title, 80)

            # 准备描述
            desc = metadata.platform_descriptions.get('bilibili', metadata.description)
            desc = self._truncate_desc(desc, 2000)

            # 准备标签
            tags = metadata.tags[:12]  # B站最多12个标签

            # 准备封面
            cover = cover_path or metadata.cover_path
            if cover:
                cover = self._prepare_cover(cover)

            logger.info(f"开始上传到B站: {title}")
            logger.debug(f"视频路径: {metadata.video_path}")
            logger.debug(f"封面路径: {cover}")
            logger.debug(f"标签: {tags}")

            # 创建视频分P页面
            page = VideoUploaderPage(path=str(metadata.video_path), title=title)

            # 准备上传元数据
            upload_meta = {
                "title": title,
                "desc": desc,
                "copyright": 1,  # 自制
                "tag": ",".join(tags),
                "tid": 124,  # 社科·法律·心理 分区
            }

            # 上传视频
            uploader = video_uploader.VideoUploader(
                pages=[page],
                meta=upload_meta,
                credential=self.credential,
                cover=str(cover) if cover else None,
            )

            # 开始上传
            await uploader.start()

            logger.success(f"B站上传成功: {title}")
            return {
                "status": "success",
                "platform": "bilibili",
                "title": title,
                "url": uploader.get_url() if hasattr(uploader, 'get_url') else None
            }

        except Exception as e:
            logger.error(f"B站上传失败: {e}")
            return {
                "status": "error",
                "platform": "bilibili",
                "error": str(e)
            }

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

    def _prepare_cover(self, cover_path: Path) -> Path:
        """
        准备封面图 - 调整到B站要求的尺寸
        B站封面要求: 16:9 或 4:3，推荐 1920x1080
        """
        try:
            img = Image.open(cover_path)
            width, height = img.size

            # 如果已经是合适的尺寸，直接返回
            ratio = width / height
            if 1.7 <= ratio <= 1.8:  # 接近16:9
                if width >= 1920:
                    return cover_path

            # 调整为 1920x1080
            target_size = (1920, 1080)

            # 保持比例，裁剪居中
            img_ratio = width / height
            target_ratio = target_size[0] / target_size[1]

            if img_ratio > target_ratio:
                # 图片更宽，裁剪左右
                new_width = int(height * target_ratio)
                left = (width - new_width) // 2
                img = img.crop((left, 0, left + new_width, height))
            else:
                # 图片更高，裁剪上下
                new_height = int(width / target_ratio)
                top = (height - new_height) // 2
                img = img.crop((0, top, width, top + new_height))

            # 缩放到目标尺寸
            img = img.resize(target_size, Image.Resampling.LANCZOS)

            # 保存处理后的封面
            output_path = cover_path.parent / f"cover_bilibili_{cover_path.name}"
            img.save(output_path, quality=95)

            logger.info(f"封面已调整为B站尺寸: {output_path}")
            return output_path

        except Exception as e:
            logger.warning(f"封面处理失败，使用原图: {e}")
            return cover_path
