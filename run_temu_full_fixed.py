#!/usr/bin/env python3
"""
Temu Agentseller 邮件验证自动化脚本 - 修复版
功能: 自动点击Confirm按钮处理邮件验证任务
"""

import asyncio
from playwright.async_api import async_playwright
import json
import time
from datetime import datetime

URL = "https://agentseller.temu.com/safety-service/email-validate?urlToken=aeaf34d2d9fdc5ad430140c19f00accb&repType=10"
VERIFY_CODE = "zEh1QJ"
PAGE_RECORD_FILE = 'page_record_temu.json'

def load_last_page():
    try:
        with open(PAGE_RECORD_FILE, 'r') as f:
            return json.load(f).get('last_page', 0)
    except:
        return 0

def save_last_page(page_num):
    with open(PAGE_RECORD_FILE, 'w') as f:
        json.dump({'last_page': page_num}, f)

async def process_all():
    start_time = time.time()
    start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total_confirmed = 0
    total_expired = 0
    total_pages = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})

        print("="*60)
        print("🚀 Temu Agentseller 自动化脚本启动")
        print("="*60)
        print(f"开始时间: {start_time_str}")
        print("="*60)

        # 初始化
        print("\n[1/4] 正在访问页面...")
        await page.goto(URL)
        await asyncio.sleep(2)

        print("[2/4] 正在输入验证码...")
        modal = await page.query_selector('div[class*="modal"]')
        if modal:
            inputs = await modal.query_selector_all('input')
            for i, c in enumerate(VERIFY_CODE):
                if i < len(inputs):
                    await inputs[i].fill(c)
            # 等待验证码提交/弹窗关闭
            print("  等待验证码验证...")
            await asyncio.sleep(5)
            # 点击空白处关闭可能的弹窗
            await page.mouse.click(100, 100)
            await asyncio.sleep(2)
        else:
            print("  未检测到验证码弹窗")
            await asyncio.sleep(1)

        print("[3/4] 正在筛选 Status...")

        # 先关闭可能存在的 modal 弹窗
        try:
            # 尝试按 ESC 键关闭 modal
            await page.keyboard.press('Escape')
            await asyncio.sleep(0.5)
            # 尝试点击空白处
            await page.mouse.click(100, 100)
            await asyncio.sleep(0.5)
        except:
            pass

        # 1. 点击 Status 下拉框 - 使用 JavaScript 点击避免被遮挡
        try:
            await page.evaluate('''() => {
                const el = document.querySelector('#mailConfirmStatusList [data-testid="beast-core-select-header"]');
                if (el) el.click();
            }''')
        except:
            await page.click('#mailConfirmStatusList [data-testid="beast-core-select-header"]')
        await asyncio.sleep(0.5)

        # 2. 勾选 "Requires verification"
        await page.click('text=Requires verification')
        await asyncio.sleep(0.5)

        # 3. 点击下拉框外关闭下拉框
        await page.mouse.click(500, 500)
        await asyncio.sleep(0.5)

        print("[4/4] 正在搜索...")
        # 4. 点击 Search 按钮执行搜索
        await page.click('button:has-text("Search")')
        await asyncio.sleep(2)

        # 获取总数据量
        total_info = await page.evaluate('''() => {
            const bodyText = document.body.innerText;
            const match = bodyText.match(/Total[\\s]+([\\d]+)[\\s]+items/i);
            return match ? match[1] : '0';
        }''')

        total_items = int(total_info)
        total_pages_calc = (total_items // 50) + (1 if total_items % 50 > 0 else 0)

        print(f"\n📊 总数据: {total_items} 条")
        print(f"📄 总页数: {total_pages_calc} 页\n")

        if total_items == 0:
            print("✅ 没有需要处理的数据！")
            await browser.close()
            return

        # 设置每页显示条数（如果可选）
        try:
            await page.evaluate('''() => {window.scrollTo(0,document.body.scrollHeight)}''')
            await asyncio.sleep(0.5)
            # 尝试点击下拉选择50条
            page_select = await page.query_selector('[data-testid="beast-core-select"]')
            if page_select:
                await page_select.click()
                await asyncio.sleep(0.5)
                option_50 = await page.query_selector('text=50')
                if option_50:
                    await option_50.click()
                    await asyncio.sleep(2)
        except Exception as e:
            print(f"  ⚠️ 设置每页条数失败（可能只有一页数据）: {e}")

        # 获取上次进度
        last_page = load_last_page()
        current_page = last_page + 1 if last_page > 0 else 1

        print(f"🚀 从第{current_page}页开始处理\n")

        # 翻到起始页
        if current_page > 1:
            print(f"翻到第{current_page}页...")
            for _ in range(current_page - 1):
                await page.evaluate('''() => {window.scrollTo(0,document.body.scrollHeight)}''')
                await page.mouse.click(1860, 1020)
                await asyncio.sleep(0.5)

        # 处理所有页
        while current_page <= total_pages_calc:
            total_pages += 1

            # 等待页面稳定
            await asyncio.sleep(1.5)

            # 获取当前页所有可点击的Confirm链接
            confirm_links = await page.evaluate('''() => {
                const links = [];
                document.querySelectorAll('table tbody tr').forEach((r, rowIndex) => {
                    const cells = r.querySelectorAll('td');
                    if(cells.length < 2) return;

                    // 检查Expiration date列（倒数第2列）
                    const expCell = cells[cells.length - 2];
                    const expText = expCell?.textContent?.trim() || '';
                    const isExpired = expText.toLowerCase().includes('expired');

                    // 只收集未过期的Confirm链接
                    const actionCell = cells[cells.length-1];
                    const linkElements = actionCell.querySelectorAll('a');

                    for(const link of linkElements){
                        const text = link.textContent?.trim();
                        if(text === 'Confirm' && !isExpired){
                            links.push(rowIndex);
                        }
                    }
                });
                return links;
            }''')

            clicked_count = 0
            skipped_count = 0

            # 逐个点击Confirm，每次间隔2秒
            for row_idx in confirm_links:
                await page.click(f'table tbody tr:nth-child({row_idx + 1}) td:last-child a:has-text("Confirm")')
                clicked_count += 1

                # 每次点击后等待2秒
                if clicked_count < len(confirm_links):
                    await asyncio.sleep(2)

            # 统计跳过的过期数据
            skipped_count = await page.evaluate('''() => {
                let skipped = 0;
                document.querySelectorAll('table tbody tr').forEach(r => {
                    const cells = r.querySelectorAll('td');
                    if(cells.length < 2) return;

                    const expCell = cells[cells.length - 2];
                    const expText = expCell?.textContent?.trim() || '';
                    const isExpired = expText.toLowerCase().includes('expired');

                    const actionCell = cells[cells.length-1];
                    const links = actionCell.querySelectorAll('a');

                    for(const link of links){
                        if(link.textContent?.trim() === 'Confirm' && isExpired){
                            skipped++;
                        }
                    }
                });
                return skipped;
            }''')

            # 如果页数为0，刷新页面
            row_count = len(confirm_links) + skipped_count
            if row_count == 0:
                print("  🔄 页数为0，刷新页面...")
                await page.goto(URL)
                await asyncio.sleep(2)

                # 重新执行筛选流程
                modal = await page.query_selector('div[class*="modal"]')
                if modal:
                    inputs = await modal.query_selector_all('input')
                    for i, c in enumerate(VERIFY_CODE):
                        if i < len(inputs):
                            await inputs[i].fill(c)
                await asyncio.sleep(1)

                await page.click('#mailConfirmStatusList [data-testid="beast-core-select-header"]')
                await asyncio.sleep(0.5)
                await page.click('text=Requires verification')
                await asyncio.sleep(0.5)
                await page.mouse.click(500, 500)
                await asyncio.sleep(0.5)
                await page.click('button:has-text("Search")')
                await asyncio.sleep(2)

                # 重新翻到当前页
                for _ in range(current_page - 1):
                    await page.evaluate('''() => {window.scrollTo(0,document.body.scrollHeight)}''')
                    await page.mouse.click(1860, 1020)
                    await asyncio.sleep(0.5)

                # 重新获取数据
                await asyncio.sleep(1.5)

                confirm_links = await page.evaluate('''() => {
                    const links = [];
                    document.querySelectorAll('table tbody tr').forEach((r, rowIndex) => {
                        const cells = r.querySelectorAll('td');
                        if(cells.length < 2) return;

                        const expCell = cells[cells.length - 2];
                        const expText = expCell?.textContent?.trim() || '';
                        const isExpired = expText.toLowerCase().includes('expired');

                        const actionCell = cells[cells.length-1];
                        const linkElements = actionCell.querySelectorAll('a');

                        for(const link of linkElements){
                            const text = link.textContent?.trim();
                            if(text === 'Confirm' && !isExpired){
                                links.push(rowIndex);
                            }
                        }
                    });
                    return links;
                }''')

                clicked_count = 0
                for row_idx in confirm_links:
                    await page.click(f'table tbody tr:nth-child({row_idx + 1}) td:last-child a:has-text("Confirm")')
                    clicked_count += 1
                    if clicked_count < len(confirm_links):
                        await asyncio.sleep(2)

                skipped_count = await page.evaluate('''() => {
                    let skipped = 0;
                    document.querySelectorAll('table tbody tr').forEach(r => {
                        const cells = r.querySelectorAll('td');
                        if(cells.length < 2) return;

                        const expCell = cells[cells.length - 2];
                        const expText = expCell?.textContent?.trim() || '';
                        const isExpired = expText.toLowerCase().includes('expired');

                        const actionCell = cells[cells.length-1];
                        const links = actionCell.querySelectorAll('a');

                        for(const link of links){
                            if(link.textContent?.trim() === 'Confirm' && isExpired){
                                skipped++;
                            }
                        }
                    });
                    return skipped;
                }''')

            total_confirmed += clicked_count
            total_expired += skipped_count

            print(f'第{current_page:3d}/{total_pages_calc}页: Confirm:{clicked_count:2d} | 跳过过期:{skipped_count:2d} | 累计:{total_confirmed}')

            # 保存进度
            save_last_page(current_page)

            # 翻页
            if current_page < total_pages_calc:
                await page.evaluate('''() => {window.scrollTo(0,document.body.scrollHeight)}''')
                await page.mouse.click(1860, 1020)
                await asyncio.sleep(1)

            current_page += 1

        await browser.close()

        # 统计
        end_time = time.time()
        end_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elapsed = end_time - start_time

        print("\n" + "="*60)
        print("📊 任务完成统计")
        print("="*60)
        print(f"开始时间: {start_time_str}")
        print(f"结束时间: {end_time_str}")
        print(f"总耗时: {elapsed:.0f}秒 ({elapsed/60:.1f}分钟)")
        print(f"处理页数: {total_pages} 页")
        print(f"✅ 完成Confirm: {total_confirmed} 条")
        print(f"📅 已到期跳过: {total_expired} 条")
        print("="*60)

if __name__ == '__main__':
    asyncio.run(process_all())
