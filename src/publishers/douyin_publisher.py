"""
抖音发布器 - 使用 Playwright 自动化上传
"""
import asyncio
from pathlib import Path
from typing import Optional
from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from extractors.package_extractor import VideoMetadata


class DouyinPublisher:
    """抖音视频发布器（使用浏览器自动化）"""

    def __init__(self, cookies: Optional[dict] = None):
        self.cookies = cookies or {}
        self.upload_url = "https://creator.douyin.com/creator-micro/content/upload"

    async def publish(self, metadata: VideoMetadata) -> dict:
        """
        发布视频到抖音

        Args:
            metadata: 视频元数据

        Returns:
            发布结果字典
        """
        try:
            # 准备标题
            title = metadata.platform_titles.get('douyin', metadata.title)
            title = self._truncate_title(title, 55)

            # 准备描述
            desc = metadata.platform_descriptions.get('douyin', metadata.description)
            if metadata.tags:
                # 添加话题标签
                tags_str = ' '.join([f"#{tag}" for tag in metadata.tags[:5]])
                desc = f"{desc}\n\n{tags_str}"
            desc = self._truncate_desc(desc, 2000)

            logger.info(f"开始上传到抖音: {title}")

            async with async_playwright() as p:
                # 启动浏览器
                browser = await p.chromium.launch(headless=False)  # 设置为 False 以便调试
                context = await browser.new_context()

                # 加载 cookies
                if self.cookies:
                    await context.add_cookies(self.cookies)

                page = await context.new_page()

                # 访问上传页面
                await page.goto(self.upload_url, wait_until="networkidle")

                # 等待登录（如果需要）
                try:
                    await page.wait_for_selector('input[type="file"]', timeout=10000)
                except PlaywrightTimeout:
                    logger.warning("需要手动登录抖音创作者平台，等待30秒...")
                    await asyncio.sleep(30)

                # 上传视频文件
                file_input = await page.query_selector('input[type="file"]')
                if file_input:
                    await file_input.set_input_files(str(metadata.video_path))
                    logger.info("视频文件已选择，等待上传...")

                # 等待上传完成
                await asyncio.sleep(5)

                # 填写标题
                title_input = await page.query_selector('input[placeholder*="标题"]')
                if title_input:
                    await title_input.fill(title)
                    logger.info(f"标题已填写: {title}")

                # 填写描述
                desc_input = await page.query_selector('div[contenteditable="true"]')
                if desc_input:
                    await desc_input.fill(desc)
                    logger.info("描述已填写")

                # 上传封面（如果有）
                if metadata.cover_path:
                    cover_input = await page.query_selector('input[accept*="image"]')
                    if cover_input:
                        await cover_input.set_input_files(str(metadata.cover_path))
                        logger.info("封面已上传")

                # 等待视频上传完成（检查进度条消失）
                logger.info("等待视频上传完成...")
                try:
                    # 等待上传进度条或上传状态消失，最多等待5分钟
                    await page.wait_for_selector('.upload-progress', state='hidden', timeout=300000)
                except:
                    logger.info("未找到上传进度条，等待更长时间...")
                    # 如果没有进度条，就等待足够长的时间让视频上传完成
                    await asyncio.sleep(60)

                # 等待发布按钮可用
                logger.info("等待发布按钮可用...")
                await asyncio.sleep(10)

                # 关闭可能的弹窗
                logger.info("检查并关闭弹窗...")
                close_modal_selectors = [
                    'button:has-text("我知道了")',
                    'button:has-text("知道了")',
                    'button:has-text("关闭")',
                    'button.semi-modal-close',
                    'button[aria-label="Close"]',
                    '.semi-modal-close-btn'
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
                    'button:has-text("发布")',
                    'button[type="button"]:has-text("发布")',
                    'button.publish-btn',
                    '//button[contains(text(), "发布")]'
                ]

                publish_clicked = False
                for selector in publish_selectors:
                    try:
                        if selector.startswith('//'):
                            publish_btn = await page.query_selector(f'xpath={selector}')
                        else:
                            publish_btn = await page.query_selector(selector)

                        if publish_btn and await publish_btn.is_visible() and await publish_btn.is_enabled():
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

            logger.success(f"抖音发布完成: {title}")
            return {
                "status": "success",
                "platform": "douyin",
                "title": title,
            }

        except Exception as e:
            logger.error(f"抖音上传失败: {e}")
            return {
                "status": "error",
                "platform": "douyin",
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
