"""
主程序 - 视频自动发布工具
"""
import asyncio
import json
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from loguru import logger
from datetime import datetime, timedelta

from extractors.package_extractor import PackageExtractor
from publishers.bilibili_publisher import BilibiliPublisher
from publishers.douyin_publisher import DouyinPublisher
from publishers.xiaohongshu_publisher import XiaohongshuPublisher
from batch_publisher import BatchPublisher
from scheduler import ScheduledPublisher


console = Console()


class VideoPublisher:
    """视频发布管理器"""

    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)
        self.platforms_config = self._load_config("platforms.json")
        self.output_dir = Path("./output")
        self.output_dir.mkdir(exist_ok=True)

        # 配置日志
        log_file = self.output_dir / f"publish_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logger.add(log_file, rotation="10 MB")

    def _load_config(self, filename: str) -> dict:
        """加载配置文件"""
        config_file = self.config_dir / filename
        if not config_file.exists():
            logger.error(f"配置文件不存在: {config_file}")
            return {}
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def publish_package(
        self,
        package_path: str,
        platforms: Optional[List[str]] = None,
        skip_published: bool = True
    ) -> dict:
        """
        发布单个交付包

        Args:
            package_path: 交付包路径
            platforms: 要发布的平台列表，None 表示全部
            skip_published: 是否跳过已成功发布的平台

        Returns:
            发布结果
        """
        console.print(f"\n[bold cyan]正在处理交付包:[/bold cyan] {package_path}")

        # 提取元数据
        try:
            extractor = PackageExtractor(package_path)
            metadata = extractor.extract()
        except Exception as e:
            logger.error(f"提取元数据失败: {e}")
            return {"status": "error", "error": str(e)}

        # 显示提取的信息
        self._display_metadata(metadata)

        # 确定要发布的平台
        if platforms is None:
            platforms = [name for name, cfg in self.platforms_config.items() if cfg.get('enabled')]

        # 检查历史发布记录
        published_platforms = {}
        if skip_published:
            published_platforms = self._get_published_platforms(package_path)
            if published_platforms:
                console.print("\n[yellow]检测到历史发布记录:[/yellow]")
                for platform, status in published_platforms.items():
                    if status == "success":
                        console.print(f"  ✅ {platform} - 已成功发布，将跳过")
                    else:
                        console.print(f"  ❌ {platform} - 之前失败，将重试")

        # 发布到各平台
        results = {}
        for platform in platforms:
            if platform not in self.platforms_config:
                logger.warning(f"未知平台: {platform}")
                continue

            if not self.platforms_config[platform].get('enabled'):
                logger.info(f"平台 {platform} 未启用，跳过")
                continue

            # 跳过已成功发布的平台
            if skip_published and published_platforms.get(platform) == "success":
                logger.info(f"平台 {platform} 已成功发布，跳过")
                results[platform] = {"status": "skipped", "reason": "already published"}
                continue

            with console.status(f"[bold green]正在发布到 {platform}..."):
                result = await self._publish_to_platform(platform, metadata)
                results[platform] = result

        # 保存发布记录
        self._save_publish_record(package_path, metadata, results)

        # 显示结果
        self._display_results(results)

        return results

    async def _publish_to_platform(self, platform: str, metadata) -> dict:
        """发布到指定平台"""
        try:
            if platform == "bilibili":
                config = self.platforms_config['bilibili']
                publisher = BilibiliPublisher(
                    cookies=config.get('cookies'),
                    csrf=config.get('csrf')
                )
                return await publisher.publish(metadata)

            elif platform == "douyin":
                config = self.platforms_config['douyin']
                publisher = DouyinPublisher(
                    cookies=config.get('cookies')
                )
                return await publisher.publish(metadata)

            elif platform == "xiaohongshu":
                config = self.platforms_config['xiaohongshu']
                publisher = XiaohongshuPublisher(
                    cookie=config.get('cookie', ''),
                    a1=config.get('a1')
                )
                return await publisher.publish(metadata)

            else:
                return {"status": "error", "error": f"不支持的平台: {platform}"}

        except Exception as e:
            logger.error(f"发布到 {platform} 失败: {e}")
            return {"status": "error", "error": str(e)}

    def _display_metadata(self, metadata):
        """显示提取的元数据"""
        table = Table(title="提取的元数据", show_header=True)
        table.add_column("字段", style="cyan")
        table.add_column("内容", style="white")

        table.add_row("标题", metadata.title)
        table.add_row("视频", str(metadata.video_path.name))
        table.add_row("封面", str(metadata.cover_path.name) if metadata.cover_path else "无")
        table.add_row("字幕", str(metadata.subtitle_path.name) if metadata.subtitle_path else "无")
        table.add_row("标签", ", ".join(metadata.tags[:5]))

        if metadata.platform_titles:
            for platform, title in metadata.platform_titles.items():
                table.add_row(f"{platform} 标题", title)

        console.print(table)

    def _display_results(self, results: dict):
        """显示发布结果"""
        table = Table(title="发布结果", show_header=True)
        table.add_column("平台", style="cyan")
        table.add_column("状态", style="white")
        table.add_column("详情", style="white")

        for platform, result in results.items():
            status = result.get('status', 'unknown')

            if status == "success":
                status_emoji = "✅"
            elif status == "skipped":
                status_emoji = "⏭️"
            else:
                status_emoji = "❌"

            details = result.get('url') or result.get('reason') or result.get('error', '-')

            table.add_row(
                platform,
                f"{status_emoji} {status}",
                details
            )

        console.print("\n")
        console.print(table)

    def _get_published_platforms(self, package_path: str) -> dict:
        """获取已发布的平台记录"""
        published = {}

        # 查找该包的所有发布记录
        for record_file in self.output_dir.glob("record_*.json"):
            try:
                with open(record_file, 'r', encoding='utf-8') as f:
                    record = json.load(f)

                # 检查是否是同一个包（通过路径匹配）
                if record.get('package') == package_path:
                    results = record.get('results', {})
                    for platform, result in results.items():
                        # 只记录成功的平台
                        if result.get('status') == 'success':
                            published[platform] = 'success'
                        # 如果还没有成功记录，则记录失败
                        elif platform not in published:
                            published[platform] = result.get('status', 'error')
            except Exception as e:
                logger.warning(f"读取发布记录失败 {record_file}: {e}")
                continue

        return published

    def _save_publish_record(self, package_path: str, metadata, results: dict):
        """保存发布记录"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "package": package_path,
            "title": metadata.title,
            "video": str(metadata.video_path),
            "results": results
        }

        record_file = self.output_dir / f"record_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        logger.info(f"发布记录已保存: {record_file}")


@click.group()
def cli():
    """视频自动发布工具"""
    pass


@cli.command()
@click.option('--package', '-p', help='交付包路径')
@click.option('--platforms', '-t', multiple=True, help='指定平台 (bilibili, douyin, xiaohongshu)')
@click.option('--skip-published/--no-skip-published', default=True, help='跳过已成功发布的平台（默认开启）')
def publish(package, platforms, skip_published):
    """立即发布单个交付包"""
    console.print("[bold green]视频自动发布工具[/bold green]\n")

    if not package:
        console.print("[red]请指定交付包路径[/red]")
        console.print("示例: python src/main.py publish --package '/path/to/package'")
        return

    publisher = VideoPublisher()
    asyncio.run(publisher.publish_package(
        package,
        platforms=list(platforms) if platforms else None,
        skip_published=skip_published
    ))


@cli.command()
@click.option('--platforms', '-t', multiple=True, help='指定平台 (bilibili, douyin, xiaohongshu)')
@click.option('--concurrent', '-c', default=3, help='最大并发数（默认3）')
@click.option('--retry', '-r', default=2, help='失败重试次数（默认2）')
@click.option('--skip-existing', is_flag=True, default=True, help='跳过已发布的包')
def batch(platforms, concurrent, retry, skip_existing):
    """批量处理 packages/ 目录下的所有包"""
    console.print("[bold green]批量发布模式[/bold green]\n")

    packages_dir = Path("./packages")
    if not packages_dir.exists():
        console.print("[red]packages/ 目录不存在[/red]")
        return

    packages = [p for p in packages_dir.iterdir() if p.is_dir()]
    if not packages:
        console.print("[yellow]packages/ 目录为空[/yellow]")
        return

    console.print(f"找到 {len(packages)} 个交付包\n")

    batch_publisher = BatchPublisher(
        max_concurrent=concurrent,
        retry_times=retry
    )

    asyncio.run(batch_publisher.publish_batch(
        packages=packages,
        platforms=list(platforms) if platforms else None,
        skip_existing=skip_existing
    ))


@cli.command()
@click.option('--package', '-p', required=True, help='交付包路径')
@click.option('--time', '-t', required=True, help='发布时间 (格式: YYYY-MM-DD HH:MM 或 +Xm/+Xh，如 +30m 表示30分钟后)')
@click.option('--platforms', '-pf', multiple=True, help='指定平台 (bilibili, douyin, xiaohongshu)')
@click.option('--repeat', help='重复规则 (daily, weekly, monthly, 或 cron 表达式)')
def schedule(package, time, platforms, repeat):
    """添加定时发布任务"""
    console.print("[bold green]定时发布[/bold green]\n")

    # 解析发布时间
    try:
        if time.startswith('+'):
            # 相对时间，如 +30m, +2h
            unit = time[-1]
            value = int(time[1:-1])

            if unit == 'm':
                publish_time = datetime.now() + timedelta(minutes=value)
            elif unit == 'h':
                publish_time = datetime.now() + timedelta(hours=value)
            elif unit == 'd':
                publish_time = datetime.now() + timedelta(days=value)
            else:
                console.print(f"[red]不支持的时间单位: {unit}[/red]")
                console.print("支持的单位: m (分钟), h (小时), d (天)")
                return
        else:
            # 绝对时间
            publish_time = datetime.strptime(time, '%Y-%m-%d %H:%M')
    except ValueError as e:
        console.print(f"[red]时间格式错误: {e}[/red]")
        console.print("格式示例: 2024-03-20 14:30 或 +30m")
        return

    # 检查时间是否在未来
    if publish_time <= datetime.now():
        console.print("[red]发布时间必须在未来[/red]")
        return

    # 创建调度器
    scheduler = ScheduledPublisher()

    # 添加任务
    schedule_id = scheduler.add_schedule(
        package_path=package,
        publish_time=publish_time,
        platforms=list(platforms) if platforms else None,
        repeat=repeat
    )

    console.print(f"[green]✅ 已添加定时任务: {schedule_id}[/green]")
    console.print(f"发布时间: {publish_time.strftime('%Y-%m-%d %H:%M')}")
    if repeat:
        console.print(f"重复规则: {repeat}")

    console.print("\n[cyan]启动调度器以执行定时任务...[/cyan]")
    asyncio.run(scheduler.run_forever())


@cli.command()
def list_schedules():
    """列出所有定时任务"""
    console.print("[bold green]定时任务列表[/bold green]\n")

    scheduler = ScheduledPublisher()
    scheduler.display_schedules()


@cli.command()
@click.argument('schedule_id')
def remove_schedule(schedule_id):
    """移除定时任务"""
    scheduler = ScheduledPublisher()

    if scheduler.remove_schedule(schedule_id):
        console.print(f"[green]✅ 已移除定时任务: {schedule_id}[/green]")
    else:
        console.print(f"[red]❌ 移除任务失败: {schedule_id}[/red]")


@cli.command()
def run_scheduler():
    """启动调度器（执行所有定时任务）"""
    console.print("[bold green]启动定时发布调度器[/bold green]\n")

    scheduler = ScheduledPublisher()
    scheduler.display_schedules()

    console.print("\n[cyan]调度器运行中... (按 Ctrl+C 停止)[/cyan]\n")
    asyncio.run(scheduler.run_forever())


@cli.command()
def main_legacy():
    """显示帮助信息（兼容旧版命令）"""
    console.print("[yellow]请使用以下命令:[/yellow]")
    console.print("  python src/main.py publish --package '/path/to/package'")
    console.print("  python src/main.py batch")
    console.print("  python src/main.py schedule --package '/path/to/package' --time '+30m'")
    console.print("  python src/main.py list-schedules")
    console.print("  python src/main.py run-scheduler")


if __name__ == '__main__':
    cli()
