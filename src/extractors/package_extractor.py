"""
交付包解析器 - 从标准视频交付包中提取所有需要的元数据
"""
import json
import re
from pathlib import Path
from typing import Optional, Dict, List
from pydantic import BaseModel


class VideoMetadata(BaseModel):
    """视频元数据"""
    title: str
    description: str
    video_path: Path
    cover_path: Optional[Path] = None
    subtitle_path: Optional[Path] = None
    tags: List[str] = []
    duration: Optional[float] = None

    # 平台特定字段
    platform_titles: Dict[str, str] = {}
    platform_descriptions: Dict[str, str] = {}
    pinned_comment: Optional[str] = None


class PackageExtractor:
    """交付包提取器"""

    def __init__(self, package_path: str):
        self.package_path = Path(package_path)
        if not self.package_path.exists():
            raise FileNotFoundError(f"交付包不存在: {package_path}")

    def extract(self) -> VideoMetadata:
        """提取交付包中的所有元数据"""
        metadata = VideoMetadata(
            title=self._extract_title(),
            description=self._extract_description(),
            video_path=self._find_video(),
            cover_path=self._find_cover(),
            subtitle_path=self._find_subtitle(),
            tags=self._extract_tags(),
        )

        # 解析发布文案
        publish_info = self._parse_publish_doc()
        if publish_info:
            metadata.platform_titles = publish_info.get('titles', {})
            metadata.platform_descriptions = publish_info.get('descriptions', {})
            metadata.pinned_comment = publish_info.get('pinned_comment')

        return metadata

    def _find_video(self) -> Path:
        """查找视频文件"""
        # 标准文件名
        standard_names = ['成片.mp4', 'final.mp4', '最终版.mp4']
        for name in standard_names:
            video = self.package_path / name
            if video.exists():
                return video

        # 搜索所有视频文件
        for ext in ['.mp4', '.mov', '.avi', '.mkv']:
            videos = list(self.package_path.glob(f'*{ext}'))
            if videos:
                return videos[0]

        raise FileNotFoundError(f"未找到视频文件: {self.package_path}")

    def _find_cover(self) -> Optional[Path]:
        """查找封面图"""
        # 优先查找标准封面
        for pattern in ['封面*.png', '封面*.jpg', 'cover*.png', 'cover*.jpg']:
            covers = list(self.package_path.glob(pattern))
            if covers:
                # 优先选择 4x3 或 16x9 比例的封面（适合B站）
                for cover in covers:
                    if '4x3' in cover.name or '16x9' in cover.name or '16-9' in cover.name:
                        return cover
                return covers[0]

        return None

    def _find_subtitle(self) -> Optional[Path]:
        """查找字幕文件"""
        for pattern in ['*.srt', '*.ass', '*.vtt']:
            subtitles = list(self.package_path.glob(pattern))
            if subtitles:
                return subtitles[0]
        return None

    def _extract_title(self) -> str:
        """提取标题"""
        # 从 发布.md 中提取
        publish_doc = self.package_path / '发布.md'
        if publish_doc.exists():
            content = publish_doc.read_text(encoding='utf-8')
            match = re.search(r'##\s*主用标题\s*\n(.+)', content)
            if match:
                return match.group(1).strip()

        # 从 README.md 提取
        readme = self.package_path / 'README.md'
        if readme.exists():
            content = readme.read_text(encoding='utf-8')
            lines = content.strip().split('\n')
            if lines and lines[0].startswith('#'):
                return lines[0].lstrip('#').strip()

        # 使用目录名
        return self.package_path.name.replace('-交付包', '').replace('-重制版', '')

    def _extract_description(self) -> str:
        """提取描述"""
        # 从旁白稿提取
        narration = self.package_path / '旁白稿.md'
        if narration.exists():
            content = narration.read_text(encoding='utf-8')
            # 提取前几段作为描述
            lines = []
            for line in content.split('\n'):
                if line.strip() and not line.startswith('#') and not line.startswith('>'):
                    if re.match(r'^\d+\.', line.strip()):
                        lines.append(line.strip())
                    if len(lines) >= 3:
                        break
            if lines:
                return '\n'.join(lines)

        # 从 README 提取
        readme = self.package_path / 'README.md'
        if readme.exists():
            content = readme.read_text(encoding='utf-8')
            lines = content.strip().split('\n')
            if len(lines) > 1:
                return lines[1].strip()

        return ""

    def _extract_tags(self) -> List[str]:
        """提取标签"""
        tags = []

        # 从发布文案中提取
        publish_doc = self.package_path / '发布.md'
        if publish_doc.exists():
            content = publish_doc.read_text(encoding='utf-8')
            # 提取 # 标签
            tag_matches = re.findall(r'#(\S+)', content)
            tags.extend(tag_matches)

        # 从标题中提取关键词
        title = self._extract_title()
        keywords = re.findall(r'[一-龥a-zA-Z]+', title)
        tags.extend([k for k in keywords if len(k) >= 2])

        # 去重并保持顺序
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        return unique_tags[:12]  # 最多12个标签

    def _parse_publish_doc(self) -> Optional[Dict]:
        """解析发布文案文档"""
        publish_doc = self.package_path / '发布.md'
        if not publish_doc.exists():
            return None

        content = publish_doc.read_text(encoding='utf-8')
        result = {
            'titles': {},
            'descriptions': {},
            'pinned_comment': None
        }

        # 提取B站标题
        match = re.search(r'##\s*B站\s*\n标题[：:]\s*(.+)', content)
        if match:
            result['titles']['bilibili'] = match.group(1).strip()

        # 提取小红书标题
        match = re.search(r'##\s*小红书\s*\n标题[：:]\s*(.+)', content)
        if match:
            result['titles']['xiaohongshu'] = match.group(1).strip()

        # 提取小红书正文
        match = re.search(r'##\s*小红书\s*\n.*?正文[：:]\s*(.+?)(?:\n#|$)', content, re.DOTALL)
        if match:
            result['descriptions']['xiaohongshu'] = match.group(1).strip()

        # 提取视频号简介
        match = re.search(r'##\s*视频号简介\s*\n(.+)', content, re.DOTALL)
        if match:
            desc = match.group(1).strip()
            # 截取到下一个 ## 之前
            desc = re.split(r'\n##', desc)[0].strip()
            result['descriptions']['douyin'] = desc

        # 提取置顶评论
        match = re.search(r'##\s*置顶评论\s*\n(.+)', content)
        if match:
            result['pinned_comment'] = match.group(1).strip()

        return result


if __name__ == '__main__':
    # 测试
    extractor = PackageExtractor('/Users/a123/Desktop/新时代三件套-交付包-重制版')
    metadata = extractor.extract()
    print(f"标题: {metadata.title}")
    print(f"视频: {metadata.video_path}")
    print(f"封面: {metadata.cover_path}")
    print(f"字幕: {metadata.subtitle_path}")
    print(f"标签: {metadata.tags}")
    print(f"平台标题: {metadata.platform_titles}")
