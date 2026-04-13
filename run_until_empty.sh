#!/bin/bash
# 持续运行直到所有 confirm 都清空

echo "========================================"
echo "🚀 开始处理所有数据"
echo "========================================"
echo ""

run_count=0
no_progress_count=0
last_progress=-1

while true; do
    run_count=$((run_count + 1))
    current_progress=$(cat page_record_temu.json 2>/dev/null | grep -o '"last_page": [0-9]*' | awk '{print $2}' || echo "0")

    echo ""
    echo "----------------------------------------"
    echo "📌 第 $run_count 轮运行"
    echo "📌 当前进度: 第 $current_progress 页"
    echo "----------------------------------------"
    echo ""

    # 运行主脚本
    python3 run_temu_full_fixed.py
    exit_code=$?

    echo ""
    echo "✅ 脚本执行完成，退出码: $exit_code"

    # 检查进度
    new_progress=$(cat page_record_temu.json 2>/dev/null | grep -o '"last_page": [0-9]*' | awk '{print $2}' || echo "0")

    # 如果没有进展
    if [ "$new_progress" = "$current_progress" ] && [ "$new_progress" -gt "0" ]; then
        no_progress_count=$((no_progress_count + 1))
        echo "⚠️ 连续 $no_progress_count 次没有新进展"

        if [ "$no_progress_count" -ge "3" ]; then
            echo "🔄 连续多次无进展，重置进度从头开始..."
            echo '{"last_page": 0}' > page_record_temu.json
            no_progress_count=0
            last_progress=-1
        fi
    else
        no_progress_count=0
        last_progress=$new_progress
    fi

    # 检查是否全部完成（进度为0且连续无进展）
    if [ "$new_progress" = "0" ] && [ "$no_progress_count" -ge "2" ]; then
        echo "✅ 所有数据处理完成！"
        break
    fi

    # 等待后重新开始
    echo "⏱️  30秒后继续..."
    sleep 30
done

echo ""
echo "========================================"
echo "🏁 运行结束，共执行 $run_count 次"
echo "========================================"
