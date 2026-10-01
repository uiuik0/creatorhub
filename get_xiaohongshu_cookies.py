#!/usr/bin/env python3
"""
使用 Playwright 登录小红书并获取 cookies
"""
import asyncio
import json
from playwright.async_api import async_playwright
from pathlib import Path


async def get_xiaohongshu_cookies():
    """打开浏览器让用户手动登录，然后获取 cookies"""

    async with async_playwright() as p:
        print("🚀 启动浏览器...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 访问小红书创作者中心
        print("📱 打开小红书创作者中心...")
        await page.goto("https://creator.xiaohongshu.com/")

        print("\n" + "="*60)
        print("👉 请在浏览器中手动登录小红书")
        print("👉 登录成功后，等待 10 秒自动获取 cookies...")
        print("👉 如果需要更多时间，请修改脚本中的等待时间")
        print("="*60 + "\n")

        # 等待用户登录（给足够的时间）
        print("⏳ 等待登录中... (60秒)")
        await asyncio.sleep(60)

        # 获取所有 cookies
        cookies = await context.cookies()

        # 提取关键 cookies
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}

        # 查找重要的 cookie
        web_session = cookie_dict.get('web_session', '')
        a1 = cookie_dict.get('a1', '')
        webId = cookie_dict.get('webId', '')

        print("\n" + "="*60)
        print("✅ Cookie 获取成功！")
        print("="*60)
        print(f"\n📋 关键 Cookies:")
        print(f"web_session: {web_session[:50]}..." if len(web_session) > 50 else f"web_session: {web_session}")
        print(f"a1: {a1[:50]}..." if len(a1) > 50 else f"a1: {a1}")
        print(f"webId: {webId}")

        # 构建完整的 cookie 字符串
        cookie_string = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])

        # 保存到文件
        output_file = Path("xiaohongshu_cookies.json")
        cookie_data = {
            "web_session": web_session,
            "a1": a1,
            "webId": webId,
            "full_cookie_string": cookie_string,
            "all_cookies": cookies
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cookie_data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Cookies 已保存到: {output_file}")
        print("\n🎯 接下来我会自动更新 config/platforms.json")

        await browser.close()

        return cookie_data


async def update_config(cookie_data):
    """更新配置文件"""
    config_file = Path("config/platforms.json")

    if not config_file.exists():
        print(f"❌ 配置文件不存在: {config_file}")
        return

    # 读取配置
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 更新小红书配置
    if 'xiaohongshu' in config:
        config['xiaohongshu']['cookie'] = cookie_data['full_cookie_string']
        config['xiaohongshu']['a1'] = cookie_data['a1']
        config['xiaohongshu']['enabled'] = True

        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"✅ 配置已更新: {config_file}")
        print("\n🎉 现在可以发布到小红书了！")
    else:
        print("❌ 配置文件中没有 xiaohongshu 配置项")


async def main():
    try:
        cookie_data = await get_xiaohongshu_cookies()

        if cookie_data['web_session']:
            await update_config(cookie_data)
        else:
            print("\n⚠️  未获取到 web_session，请确认已成功登录")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
