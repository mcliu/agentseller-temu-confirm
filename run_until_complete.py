#!/usr/bin/env python3
"""
持续运行直到所有数据处理完成
功能: 自动循环运行，遇到退出时刷新从头执行
"""

import asyncio
import subprocess
import sys
import time
import json
import os
from datetime import datetime

# ============ 配置 ============
MAIN_SCRIPT = "run_temu_full_fixed.py"
PAGE_RECORD_FILE = "page_record_temu.json"
MAX_RETRIES = 100  # 最大重试次数
RESTART_DELAY = 3  # 重启间隔（秒）
# =============================

def log(msg):
    """打印日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def get_progress():
    """获取当前进度"""
    try:
        if os.path.exists(PAGE_RECORD_FILE):
            with open(PAGE_RECORD_FILE, 'r') as f:
                data = json.load(f)
                return data.get('last_page', 0)
    except:
        pass
    return 0

def reset_progress():
    """重置进度"""
    with open(PAGE_RECORD_FILE, 'w') as f:
        json.dump({'last_page': 0}, f)
    log("🔄 进度已重置，将从头开始")

def check_if_complete():
    """检查是否已完成（连续多次没有新数据）"""
    # 读取页面记录文件
    try:
        with open(PAGE_RECORD_FILE, 'r') as f:
            data = json.load(f)
            last_page = data.get('last_page', 0)
            # 如果上次处理到了第0页，可能是新任务
            if last_page == 0:
                return False
    except:
        pass
    return False

async def run_main_script():
    """运行主脚本"""
    process = await asyncio.create_subprocess_exec(
        sys.executable, MAIN_SCRIPT,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    # 实时输出
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        print(line.decode('utf-8', errors='replace'), end='')

    await process.wait()
    return process.returncode

async def main():
    """主循环"""
    log("="*60)
    log("🚀 Temu Agentseller 持续运行模式启动")
    log("="*60)
    log(f"主脚本: {MAIN_SCRIPT}")
    log(f"最大重试: {MAX_RETRIES} 次")
    log(f"重启间隔: {RESTART_DELAY} 秒")
    log("="*60)

    retry_count = 0
    total_runs = 0
    last_progress = 0
    no_progress_count = 0

    while retry_count < MAX_RETRIES:
        total_runs += 1
        current_progress = get_progress()

        log("")
        log("-"*60)
        log(f"📌 第 {total_runs} 次运行 (重试 {retry_count}/{MAX_RETRIES})")
        log(f"📌 当前进度: 第 {current_progress} 页")
        log("-"*60)

        # 检查是否有进展
        if current_progress == last_progress and current_progress > 0:
            no_progress_count += 1
            log(f"⚠️ 连续 {no_progress_count} 次没有新进展")

            # 如果连续3次没有进展，重置进度从头开始
            if no_progress_count >= 3:
                log("🔄 连续多次无进展，准备刷新从头开始...")
                reset_progress()
                no_progress_count = 0
                retry_count = 0
                last_progress = 0
                continue
        else:
            no_progress_count = 0

        last_progress = current_progress

        try:
            # 运行主脚本
            exit_code = await run_main_script()

            log("")
            log(f"✅ 脚本执行完成，退出码: {exit_code}")

            # 检查是否处理完所有数据
            new_progress = get_progress()
            if new_progress == current_progress and new_progress > 0:
                log("📊 进度没有变化，可能已完成或需要刷新")
                retry_count += 1
            else:
                log(f"📊 进度更新: 第 {current_progress} 页 → 第 {new_progress} 页")
                retry_count = 0  # 重置重试计数

        except KeyboardInterrupt:
            log("\n⚠️ 用户中断，等待 2 秒后重新开始...")
            await asyncio.sleep(2)
            retry_count += 1

        except Exception as e:
            log(f"\n❌ 发生错误: {str(e)}")
            log("等待 3 秒后重新开始...")
            await asyncio.sleep(3)
            retry_count += 1

        # 重启间隔
        if retry_count < MAX_RETRIES:
            log(f"⏱️  {RESTART_DELAY} 秒后重新开始...")
            await asyncio.sleep(RESTART_DELAY)

    log("")
    log("="*60)
    log(f"🏁 运行结束，共执行 {total_runs} 次")
    log("="*60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n用户中断程序")
        sys.exit(0)
