#!/usr/bin/env python3
"""
快速配置脚本 - 帮助用户配置平台账号
"""
import json
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()


def setup_bilibili():
    """配置 B站"""
    console.print("\n[bold cyan]配置 B站账号[/bold cyan]")
    console.print("\n请按照以下步骤获取凭证：")
    console.print("1. 打开浏览器，登录 https://member.bilibili.com/")
    console.print("2. 按 F12 打开开发者工具")
    console.print("3. 切换到 [yellow]Application[/yellow] > [yellow]Cookies[/yellow] > [yellow]bilibili.com[/yellow]")
    console.print("4. 找到 [green]SESSDATA[/green] 和 [green]bili_jct[/green] 的值\n")

    enabled = Confirm.ask("是否启用 B站 发布？", default=True)

    if enabled:
        sessdata = Prompt.ask("请输入 SESSDATA")
        csrf = Prompt.ask("请输入 bili_jct (csrf token)")
        return {
            "enabled": True,
            "cookies": sessdata,
            "csrf": csrf
        }
    else:
        return {"enabled": False}


def setup_douyin():
    """配置抖音"""
    console.print("\n[bold cyan]配置抖音[/bold cyan]")
    console.print("抖音使用浏览器自动化，首次运行时需要手动登录")

    enabled = Confirm.ask("是否启用 抖音 发布？", default=True)
    return {"enabled": enabled}


def setup_xiaohongshu():
    """配置小红书"""
    console.print("\n[bold cyan]配置小红书[/bold cyan]")
    console.print("小红书使用浏览器自动化，首次运行时需要手动登录")

    enabled = Confirm.ask("是否启用 小红书 发布？", default=True)
    return {"enabled": enabled}


def main():
    console.print("[bold green]========================================[/bold green]")
    console.print("[bold green]  视频自动发布工具 - 快速配置向导[/bold green]")
    console.print("[bold green]========================================[/bold green]")

    config_dir = Path("./config")
    config_dir.mkdir(exist_ok=True)

    config_file = config_dir / "platforms.json"

    # 加载现有配置或使用默认配置
    if config_file.exists():
        console.print(f"\n[yellow]发现现有配置文件，将进行更新[/yellow]")
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        # 加载模板
        template_file = config_dir / "platforms.json.template"
        if template_file.exists():
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 移除注释行
                lines = [line for line in content.split('\n') if not line.strip().startswith('#')]
                config = json.loads('\n'.join(lines))
        else:
            config = {}

    # 配置各平台
    if 'bilibili' not in config:
        config['bilibili'] = {}

    bilibili_config = setup_bilibili()
    config['bilibili'].update(bilibili_config)

    if 'douyin' not in config:
        config['douyin'] = {}
    douyin_config = setup_douyin()
    config['douyin']['enabled'] = douyin_config['enabled']

    if 'xiaohongshu' not in config:
        config['xiaohongshu'] = {}
    xiaohongshu_config = setup_xiaohongshu()
    config['xiaohongshu']['enabled'] = xiaohongshu_config['enabled']

    # 保存配置
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    console.print("\n[bold green]✓ 配置已保存到 config/platforms.json[/bold green]")

    # 显示配置摘要
    console.print("\n[bold cyan]配置摘要：[/bold cyan]")
    console.print(f"  B站: {'✓ 已启用' if config['bilibili'].get('enabled') else '✗ 未启用'}")
    console.print(f"  抖音: {'✓ 已启用' if config['douyin'].get('enabled') else '✗ 未启用'}")
    console.print(f"  小红书: {'✓ 已启用' if config['xiaohongshu'].get('enabled') else '✗ 未启用'}")

    console.print("\n[bold green]========================================[/bold green]")
    console.print("[bold green]  配置完成！现在可以开始发布视频了[/bold green]")
    console.print("[bold green]========================================[/bold green]")
    console.print("\n运行以下命令测试：")
    console.print("[yellow]python test_extract.py[/yellow]")


if __name__ == '__main__':
    main()
