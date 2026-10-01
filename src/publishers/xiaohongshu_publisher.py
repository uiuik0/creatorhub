"""
小红书发布器 - 使用 Playwright 自动化上传
"""
import asyncio
from pathlib import Path
from typing import Optional
from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from extractors.package_extractor import VideoMetadata


class XiaohongshuPublisher:
    """小红书视频发布器（使用浏览器自动化）"""

    def __init__(self, cookie: str = "", a1: str = ""):
        self.cookie = cookie
        self.a1 = a1
        self.upload_url = "https://creator.xiaohongshu.com/publish/publish"

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
            if metadata.tags:
                # 添加话题标签
                tags_str = ' '.join([f"#{tag}" for tag in metadata.tags[:10] if tag != '#'])
                desc = f"{title}\n\n{desc}\n\n{tags_str}"
            desc = self._truncate_desc(desc, 1000)

            logger.info(f"开始上传到小红书: {title}")

            async with async_playwright() as p:
                # 启动浏览器
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()

                # 加载 cookies
                if self.cookie:
                    cookies = self._parse_cookie_string(self.cookie)
                    await context.add_cookies(cookies)

                page = await context.new_page()

                # 访问上传页面（增加超时时间到60秒）
                try:
                    await page.goto(self.upload_url, wait_until="networkidle", timeout=60000)
                except PlaywrightTimeout:
                    # 如果 networkidle 超时，尝试用 domcontentloaded
                    logger.warning("页面加载超时，尝试使用 domcontentloaded 模式...")
                    await page.goto(self.upload_url, wait_until="domcontentloaded", timeout=60000)

                # 等待登录（如果需要）
                try:
                    await page.wait_for_selector('input[type="file"]', timeout=10000)
                except PlaywrightTimeout:
                    logger.warning("需要手动登录小红书创作者平台，等待30秒...")
                    await asyncio.sleep(30)

                # 上传视频文件
                file_input = await page.query_selector('input[type="file"][accept*="video"]')
                if not file_input:
                    # 尝试其他选择器
                    file_input = await page.query_selector('input[type="file"]')

                if file_input:
                    await file_input.set_input_files(str(metadata.video_path))
                    logger.info("视频文件已选择，等待上传...")

                # 等待上传完成
                await asyncio.sleep(10)

                # 填写标题和描述
                # 小红书可能将标题和描述放在同一个文本框
                desc_input = await page.query_selector('div[contenteditable="true"]')
                if not desc_input:
                    desc_input = await page.query_selector('textarea[placeholder*="填写"]')

                if desc_input:
                    await desc_input.fill(desc)
                    logger.info(f"标题和描述已填写")

                # 上传封面（如果有）
                if metadata.cover_path:
                    try:
                        cover_input = await page.query_selector('input[accept*="image"]')
                        if cover_input:
                            await cover_input.set_input_files(str(metadata.cover_path))
                            logger.info("封面已上传")
                    except Exception as e:
                        logger.warning(f"封面上传失败: {e}")

                # 等待视频上传完成
                logger.info("等待视频上传完成（60秒）...")
                await asyncio.sleep(60)

                # 额外等待页面渲染
                logger.info("等待页面渲染完成（10秒）...")
                await asyncio.sleep(10)

                # 关闭可能的弹窗
                logger.info("检查并关闭弹窗...")
                close_modal_selectors = [
                    'button:has-text("我知道了")',
                    'button:has-text("知道了")',
                    'button:has-text("关闭")',
                    '.close-btn',
                    'button.modal-close'
                ]

                for selector in close_modal_selectors:
                    try:
                        modal_close = await page.query_selector(selector)
                        if modal_close and await modal_close.is_visible():
                            await modal_close.click()
                            logger.info(f"已关闭弹窗: {selector}")
                            await asyncio.sleep(1)
                    except:
                        pass

                # 查找并点击发布按钮
                logger.info("查找发布按钮...")

                publish_selectors = [
                    'text=发布笔记',  # ✅ 最有效的选择器
                    'text=发布',
                    '*:has-text("发布笔记")',
                    'div:has-text("发布笔记")',
                    '//button[contains(., "发布笔记")]',
                    '//*[contains(., "发布笔记")]',
                ]

                publish_clicked = False
                for selector in publish_selectors:
                    try:
                        if selector.startswith('//'):
                            publish_btn = await page.query_selector(f'xpath={selector}')
                        else:
                            publish_btn = await page.query_selector(selector)

                        logger.info(f"选择器 {selector}: 找到={publish_btn is not None}")

                        if publish_btn:
                            visible = await publish_btn.is_visible()
                            enabled = await publish_btn.is_enabled()
                            logger.info(f"  - visible={visible}, enabled={enabled}")

                            if visible and enabled:
                                await publish_btn.click()
                                logger.success(f"已点击发布按钮: {selector}")
                                publish_clicked = True
                                break
                    except Exception as e:
                        logger.debug(f"尝试选择器 {selector} 失败: {e}")
                        continue

                if not publish_clicked:
                    logger.error("未能找到可点击的发布按钮！")
                    logger.info("等待30秒让用户手动点击...")
                    await asyncio.sleep(30)
                else:
                    # 等待发布完成（等待成功提示或页面跳转）
                    logger.info("等待发布完成，请勿关闭页面...")
                    try:
                        # 等待成功提示或页面跳转
                        await page.wait_for_selector('text=发布成功', timeout=120000)
                        logger.success("检测到发布成功提示")
                    except:
                        # 即使没有找到成功提示，也等待足够长的时间让视频上传完成
                        logger.info("未检测到成功提示，继续等待60秒...")
                        await asyncio.sleep(60)

                await browser.close()

            logger.success(f"小红书发布完成: {title}")
            return {
                "status": "success",
                "platform": "xiaohongshu",
                "title": title,
            }

        except Exception as e:
            logger.error(f"小红书上传失败: {e}")
            return {
                "status": "error",
                "platform": "xiaohongshu",
                "error": str(e)
            }

    def _parse_cookie_string(self, cookie_string: str) -> list:
        """
        解析 cookie 字符串为 Playwright 格式

        Args:
            cookie_string: Cookie 字符串，格式如 "key1=value1; key2=value2"

        Returns:
            Playwright cookies 列表
        """
        cookies = []
        for item in cookie_string.split(';'):
            item = item.strip()
            if '=' in item:
                name, value = item.split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.xiaohongshu.com',
                    'path': '/'
                })
        return cookies

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
