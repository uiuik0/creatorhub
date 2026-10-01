"""
批量发布管理器 - 支持并发、重试、进度追踪
"""
import asyncio
import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from loguru import logger
from rich.console import Console
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.table import Table

from extractors.package_extractor import PackageExtractor, VideoMetadata
from publishers.bilibili_publisher import BilibiliPublisher
from publishers.douyin_publisher import DouyinPublisher
from publishers.xiaohongshu_publisher import XiaohongshuPublisher


console = Console()


class BatchPublisher:
    """批量发布管理器"""

    def __init__(
        self,
        config_dir: str = "./config",
        output_dir: str = "./output",
        max_concurrent: int = 3,
        retry_times: int = 2
    ):
        """
        初始化批量发布管理器

        Args:
            config_dir: 配置文件目录
            output_dir: 输出目录
            max_concurrent: 最大并发数
            retry_times: 失败重试次数
        """
        self.config_dir = Path(config_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.max_concurrent = max_concurrent
        self.retry_times = retry_times

        # 加载配置
        self.platforms_config = self._load_config("platforms.json")

        # 统计信息
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }

    def _load_config(self, filename: str) -> dict:
        """加载配置文件"""
        config_file = self.config_dir / filename
        if not config_file.exists():
            logger.error(f"配置文件不存在: {config_file}")
            return
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def publish_batch(
        self,
        packages: List[Path],
        platforms: Optional[List[str]] = None,
        skip_existing: bool = True
    ) -> Dict:
        """
        批量发布多个交付包

        Args:
            packages: 交付包路径列表
            platforms: 要发布的平台列表
            skip_existing: 跳过已发布的包

        Returns:
            批量发布结果
        """
        self.stats["total"] = len(packages)

        console.print(f"\n[bold cyan]开始批量发布 {len(packages)} 个交付包[/bold cyan]")
        console.print(f"最大并发数: {self.max_concurrent}")
        console.print(f"重试次数: {self.retry_times}\n")

        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(self.max_concurrent)

        # 创建任务列表
        tasks = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:

            overall_task = progress.add_task(
                "[cyan]总体进度",
                total=len(packages)
            )

            for package in packages:
                task = self._publish_with_semaphore(
                    semaphore,
                    package,
                    platforms,
                    skip_existing,
                    progress,
                    overall_task
                )
                tasks.append(task)

            # 并发执行所有任务
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # 保存批量发布报告
        report = self._generate_report(packages, results)
        self._save_report(report)

        # 显示统计信息
        self._display_stats()

        return report

    async def _publish_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        package: Path,
        platforms: Optional[List[str]],
        skip_existing: bool,
        progress: Progress,
        overall_task: TaskID
    ) -> Dict:
        """使用信号量控制的发布任务"""
        async with semaphore:
            result = await self._publish_single_package(
                package,
                platforms,
                skip_existing
            )
            progress.update(overall_task, advance=1)
            return result

    async def _publish_single_package(
        self,
        package: Path,
        platforms: Optional[List[str]],
        skip_existing: bool
    ) -> Dict:
        """
        发布单个交付包（支持重试）

        Args:
            package: 交付包路径
            platforms: 平台列表
            skip_existing: 是否跳过已发布

        Returns:
            发布结果
        """
        package_name = package.name
        logger.info(f"开始处理: {package_name}")

        # 检查是否已发布
        if skip_existing and self._is_already_published(package):
            logger.info(f"跳过已发布: {package_name}")
            self.stats["skipped"] += 1
            return {
                "package": str(package),
                "status": "skipped",
                "reason": "already_published"
            }

        # 提取元数据
        try:
            extractor = PackageExtractor(str(package))
            metadata = extractor.extract()
        except Exception as e:
            logger.error(f"提取元数据失败 [{package_name}]: {e}")
            self.stats["failed"] += 1
            return {
                "package": str(package),
                "status": "error",
                "error": f"metadata_extraction_failed: {e}"
            }

        # 确定要发布的平台
        if platforms is None:
            platforms = [
                name for name, cfg in self.platforms_config.items()
                if cfg.get('enabled')
            ]

        # 发布到各平台（支持重试）
        platform_results = {}
        for platform in platforms:
            for attempt in range(self.retry_times + 1):
                try:
                    result = await self._publish_to_platform(platform, metadata)
                    platform_results[platform] = result

                    if result.get('status') == 'success':
                        break

                    if attempt < self.retry_times:
                        logger.warning(
                            f"重试 {platform} [{package_name}] "
                            f"({attempt + 1}/{self.retry_times})"
                        )
                        await asyncio.sleep(5)  # 等待5秒后重试

                except Exception as e:
                    logger.error(f"发布到 {platform} 失败: {e}")
                    platform_results[platform] = {
                        "status": "error",
                        "error": str(e)
                    }

        # 判断整体状态
        success_count = sum(
            1 for r in platform_results.values()
            if r.get('status') == 'success'
        )

        if success_count == len(platforms):
            self.stats["success"] += 1
            overall_status = "success"
        elif success_count > 0:
            self.stats["success"] += 1
            overall_status = "partial_success"
        else:
            self.stats["failed"] += 1
            overall_status = "failed"

        return {
            "package": str(package),
            "title": metadata.title,
            "status": overall_status,
            "platforms": platform_results,
            "timestamp": datetime.now().isoformat()
        }

    async def _publish_to_platform(
        self,
        platform: str,
        metadata: VideoMetadata
    ) -> Dict:
        """发布到指定平台"""
        if platform not in self.platforms_config:
            return {"status": "error", "error": "unknown_platform"}

        config = self.platforms_config[platform]

        if not config.get('enabled'):
            return {"status": "skipped", "reason": "platform_disabled"}

        try:
            if platform == "bilibili":
                publisher = BilibiliPublisher(
                    cookies=config.get('cookies'),
                    csrf=config.get('csrf')
                )
                return await publisher.publish(metadata)

            elif platform == "douyin":
                publisher = DouyinPublisher(
                    cookies=config.get('cookies')
                )
                return await publisher.publish(metadata)

            elif platform == "xiaohongshu":
                publisher = XiaohongshuPublisher(
                    cookie=config.get('cookie', ''),
                    a1=config.get('a1')
                )
                return await publisher.publish(metadata)

            else:
                return {"status": "error", "error": "unsupported_platform"}

        except Exception as e:
            logger.error(f"发布到 {platform} 失败: {e}")
            return {"status": "error", "error": str(e)}

    def _is_already_published(self, package: Path) -> bool:
        """检查包是否已发布"""
        # 检查发布记录
        records_dir = self.output_dir / "records"
        if not records_dir.exists():
            return False

        package_name = package.name
        for record_file in records_dir.glob("*.json"):
            try:
                with open(record_file, 'r', encoding='utf-8') as f:
                    record = json.load(f)
                    if record.get('package', '').endswith(package_name):
                        return True
            except Exception:
                continue

        return False

    def _generate_report(self, packages: List[Path], results: List[Dict]) -> Dict:
        """生成批量发布报告"""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_packages": len(packages),
            "statistics": self.stats.copy(),
            "results": [
                r for r in results
                if isinstance(r, dict) and not isinstance(r, Exception)
            ]
        }

    def _save_report(self, report: Dict):
        """保存发布报告"""
        reports_dir = self.output_dir / "reports"
        reports_dir.mkdir(exist_ok=True)

        report_file = reports_dir / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"批量发布报告已保存: {report_file}")

    def _display_stats(self):
        """显示统计信息"""
        table = Table(title="批量发布统计", show_header=True)
        table.add_column("项目", style="cyan")
        table.add_column("数量", style="white")

        table.add_row("总计", str(self.stats["total"]))
        table.add_row("✅ 成功", str(self.stats["success"]))
        table.add_row("❌ 失败", str(self.stats["failed"]))
        table.add_row("⏭️  跳过", str(self.stats["skipped"]))

        console.print("\n")
        console.print(table)
