#!/usr/bin/env python3
"""
抖音 Cookie 获取工具

使用 Playwright 自动打开浏览器，让用户登录抖音创作者平台，
然后自动提取并保存认证信息到配置文件。
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright


async def get_douyin_cookies():
    """获取抖音 cookies"""

    print("=" * 60)
    print("抖音 Cookie 获取工具")
    print("=" * 60)
    print()
    print("即将打开浏览器，请按以下步骤操作：")
    print("1. 在打开的浏览器中登录抖音创作者平台")
    print("2. 登录成功后，等待页面完全加载")
    print("3. 程序将自动提取 cookies 并保存")
    print()
    input("按 Enter 键继续...")

    async with async_playwright() as p:
        # 启动浏览器（非无头模式，方便用户登录）
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 访问抖音创作者平台
        print("\n正在打开抖音创作者平台...")
        await page.goto("https://creator.douyin.com/", wait_until="domcontentloaded")

        print("\n请在浏览器中完成登录...")
        print("登录成功后，请在此按 Enter 键继续...")

        # 等待用户登录
        await asyncio.sleep(2)

        # 在后台等待登录完成的信号
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, input)

        print("\n正在获取 cookies...")

        # 获取所有 cookies
        cookies = await context.cookies()

        # 提取重要的认证信息
        session_id = None
        device_id = None

        print("\n获取到的 Cookies:")
        print("-" * 60)
        for cookie in cookies:
            print(f"  {cookie['name']}: {cookie['value'][:50]}..." if len(cookie['value']) > 50 else f"  {cookie['name']}: {cookie['value']}")

            # 提取关键字段
            if cookie['name'] == 'sessionid' or cookie['name'] == 'sessionid_ss':
                session_id = cookie['value']
            elif cookie['name'] == 'device_id' or cookie['name'] == 'tt_webid':
                device_id = cookie['value']

        print("-" * 60)

        # 更新配置文件
        config_path = Path(__file__).parent / "config" / "platforms.json"

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            if 'douyin' in config:
                if session_id:
                    config['douyin']['session_id'] = session_id
                    print(f"\n✓ session_id: {session_id[:20]}...")

                if device_id:
                    config['douyin']['device_id'] = device_id
                    print(f"✓ device_id: {device_id[:20]}...")

                # 保存配置
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)

                print(f"\n✓ 配置已保存到: {config_path}")
            else:
                print("\n✗ 配置文件中没有找到 douyin 配置")
        else:
            print(f"\n✗ 配置文件不存在: {config_path}")

        await browser.close()

    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(get_douyin_cookies())
