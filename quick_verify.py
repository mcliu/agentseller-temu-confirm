#!/usr/bin/env python3
"""
快速邮箱验证脚本
"""
import asyncio
import argparse
from temu_browser import TemuBrowser

async def verify_email(verification_link: str, captcha_code: str):
    """验证邮箱"""
    browser = None
    try:
        print("🚀 启动浏览器...")
        browser = TemuBrowser()

        print(f"🔗 正在访问验证链接...")
        print(f"   链接: {verification_link}")
        print(f"   验证码: {captcha_code}")

        success = await browser.verify_email(verification_link, captcha_code)

        if success:
            print("✅ 邮箱验证成功！")
        else:
            print("❌ 邮箱验证失败")

        return success

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

    finally:
        if browser:
            print("🔄 关闭浏览器...")
            await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Temu 邮箱验证工具")
    parser.add_argument("--link", "-l", required=True, help="验证链接")
    parser.add_argument("--code", "-c", required=True, help="验证码")

    args = parser.parse_args()

    asyncio.run(verify_email(args.link, args.code))
