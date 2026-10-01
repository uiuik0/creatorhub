"""
定时发布调度器 - 支持定时发布、重复发布
"""
import asyncio
import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from rich.console import Console
from rich.table import Table

from extractors.package_extractor import PackageExtractor
from publishers.bilibili_publisher import BilibiliPublisher
from publishers.douyin_publisher import DouyinPublisher
from publishers.xiaohongshu_publisher import XiaohongshuPublisher


console = Console()


class ScheduledPublisher:
    """定时发布调度器"""

    def __init__(self, config_dir: str = "./config", output_dir: str = "./output"):
        """
        初始化定时发布调度器

        Args:
            config_dir: 配置文件目录
            output_dir: 输出目录
        """
        self.config_dir = Path(config_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # 创建调度器
        self.scheduler = AsyncIOScheduler()

        # 加载配置
        self.platforms_config = self._load_config("platforms.json")
        self.schedule_config_file = self.output_dir / "schedules.json"

        # 加载已有的定时任务
        self.schedules = self._load_schedules()

    def _load_config(self, filename: str) -> dict:
        """加载配置文件"""
        config_file = self.config_dir / filename
        if not config_file.exists():
            logger.error(f"配置文件不存在: {config_file}")
            return {}
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_schedules(self) -> dict:
        """加载定时任务配置"""
        if not self.schedule_config_file.exists():
            return {}
        try:
            with open(self.schedule_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载定时任务配置失败: {e}")
            return {}

    def _save_schedules(self):
        """保存定时任务配置"""
        with open(self.schedule_config_file, 'w', encoding='utf-8') as f:
            json.dump(self.schedules, f, ensure_ascii=False, indent=2)
        logger.info(f"定时任务配置已保存: {self.schedule_config_file}")

    def add_schedule(
        self,
        package_path: str,
        publish_time: datetime,
        platforms: Optional[List[str]] = None,
        repeat: Optional[str] = None,
        schedule_id: Optional[str] = None
    ) -> str:
        """
        添加定时发布任务

        Args:
            package_path: 交付包路径
            publish_time: 发布时间
            platforms: 要发布的平台列表
            repeat: 重复规则 (daily, weekly, monthly, 或 cron 表达式)
            schedule_id: 任务ID（可选，不提供则自动生成）

        Returns:
            任务ID
        """
        if schedule_id is None:
            schedule_id = f"schedule_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 保存任务配置
        self.schedules[schedule_id] = {
            "package_path": package_path,
            "publish_time": publish_time.isoformat(),
            "platforms": platforms,
            "repeat": repeat,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        self._save_schedules()

        # 添加到调度器
        if repeat:
            # 重复任务
            trigger = self._create_trigger(publish_time, repeat)
        else:
            # 一次性任务
            trigger = DateTrigger(run_date=publish_time)

        self.scheduler.add_job(
            self._execute_scheduled_publish,
            trigger=trigger,
            args=[schedule_id, package_path, platforms],
            id=schedule_id,
            replace_existing=True
        )

        logger.info(f"已添加定时任务: {schedule_id}")
        return schedule_id

    def _create_trigger(self, start_time: datetime, repeat: str):
        """创建触发器"""
        if repeat == "daily":
            # 每天同一时间
            return CronTrigger(
                hour=start_time.hour,
                minute=start_time.minute
            )
        elif repeat == "weekly":
            # 每周同一时间
            return CronTrigger(
                day_of_week=start_time.weekday(),
                hour=start_time.hour,
                minute=start_time.minute
            )
        elif repeat == "monthly":
            # 每月同一时间
            return CronTrigger(
                day=start_time.day,
                hour=start_time.hour,
                minute=start_time.minute
            )
        else:
            # 自定义 cron 表达式
            # 格式: "分 时 日 月 周"
            return CronTrigger.from_crontab(repeat)

    async def _execute_scheduled_publish(
        self,
        schedule_id: str,
        package_path: str,
        platforms: Optional[List[str]]
    ):
        """执行定时发布任务"""
        logger.info(f"开始执行定时任务: {schedule_id}")
        console.print(f"\n[bold cyan]执行定时发布任务:[/bold cyan] {schedule_id}")

        try:
            # 提取元数据
            extractor = PackageExtractor(package_path)
            metadata = extractor.extract()

            # 确定要发布的平台
            if platforms is None:
                platforms = [
                    name for name, cfg in self.platforms_config.items()
                    if cfg.get('enabled')
                ]

            # 发布到各平台
            results = {}
            for platform in platforms:
                result = await self._publish_to_platform(platform, metadata)
                results[platform] = result

            # 更新任务状态
            if schedule_id in self.schedules:
                self.schedules[schedule_id]["status"] = "completed"
                self.schedules[schedule_id]["last_run"] = datetime.now().isoformat()
                self.schedules[schedule_id]["last_result"] = results
                self._save_schedules()

            # 保存发布记录
            self._save_publish_record(schedule_id, package_path, metadata, results)

            logger.info(f"定时任务执行成功: {schedule_id}")
            console.print(f"[green]✅ 定时任务执行成功[/green]")

        except Exception as e:
            logger.error(f"定时任务执行失败 [{schedule_id}]: {e}")
            console.print(f"[red]❌ 定时任务执行失败: {e}[/red]")

            # 更新任务状态
            if schedule_id in self.schedules:
                self.schedules[schedule_id]["status"] = "failed"
                self.schedules[schedule_id]["last_run"] = datetime.now().isoformat()
                self.schedules[schedule_id]["error"] = str(e)
                self._save_schedules()

    async def _publish_to_platform(self, platform: str, metadata) -> dict:
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

    def _save_publish_record(
        self,
        schedule_id: str,
        package_path: str,
        metadata,
        results: dict
    ):
        """保存发布记录"""
        records_dir = self.output_dir / "records"
        records_dir.mkdir(exist_ok=True)

        record = {
            "schedule_id": schedule_id,
            "timestamp": datetime.now().isoformat(),
            "package": package_path,
            "title": metadata.title,
            "video": str(metadata.video_path),
            "results": results
        }

        record_file = records_dir / f"scheduled_{schedule_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        logger.info(f"发布记录已保存: {record_file}")

    def remove_schedule(self, schedule_id: str) -> bool:
        """
        移除定时任务

        Args:
            schedule_id: 任务ID

        Returns:
            是否成功移除
        """
        try:
            # 从调度器移除
            self.scheduler.remove_job(schedule_id)

            # 从配置移除
            if schedule_id in self.schedules:
                del self.schedules[schedule_id]
                self._save_schedules()

            logger.info(f"已移除定时任务: {schedule_id}")
            return True

        except Exception as e:
            logger.error(f"移除定时任务失败 [{schedule_id}]: {e}")
            return False

    def list_schedules(self) -> List[Dict]:
        """列出所有定时任务"""
        return [
            {
                "id": schedule_id,
                **schedule_info
            }
            for schedule_id, schedule_info in self.schedules.items()
        ]

    def display_schedules(self):
        """显示定时任务列表"""
        if not self.schedules:
            console.print("[yellow]暂无定时任务[/yellow]")
            return

        table = Table(title="定时发布任务", show_header=True)
        table.add_column("ID", style="cyan")
        table.add_column("交付包", style="white")
        table.add_column("发布时间", style="white")
        table.add_column("重复", style="white")
        table.add_column("状态", style="white")

        for schedule_id, info in self.schedules.items():
            publish_time = datetime.fromisoformat(info['publish_time'])
            repeat = info.get('repeat', '一次性')
            status = info.get('status', 'pending')

            status_emoji = {
                'pending': '⏳',
                'completed': '✅',
                'failed': '❌'
            }.get(status, '❓')

            table.add_row(
                schedule_id,
                Path(info['package_path']).name,
                publish_time.strftime('%Y-%m-%d %H:%M'),
                repeat,
                f"{status_emoji} {status}"
            )

        console.print("\n")
        console.print(table)

    def start(self):
        """启动调度器"""
        self.scheduler.start()
        logger.info("定时发布调度器已启动")
        console.print("[green]✅ 定时发布调度器已启动[/green]")

    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("定时发布调度器已停止")
        console.print("[yellow]定时发布调度器已停止[/yellow]")

    async def run_forever(self):
        """持续运行调度器"""
        self.start()
        try:
            # 保持运行
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            self.stop()
