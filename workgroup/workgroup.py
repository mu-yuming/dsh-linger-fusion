#!/usr/bin/env python3
"""DSH 原生原语版「工作小组」原型 —— 不装第三方 bot 插件。

角色（都是 DSH subagent / HTTP 端点的轻量封装）：
  调度bot (conductor)：本地 Qwen3，免费。整理简报 + 判断派给谁。
  整理bot (local-worker)：本地 Qwen3，免费。摘要/分类/初筛。
  轻量bot (doubao)：豆包 API，便宜。查证/复核。
  专家bot (workbuddy)：magpie 网关免费强模型，深度推理。
  编码bot (codex)：已配好，走 magpie 网关 deepseek/deepseek-flash（本原型先占位）。

省钱三铁律：① 简报先行（只看压缩后的简报）② @才发言（只派发被点名的角色）③ 轮次上限（本原型单轮，不循环）。

用法：python workgroup.py <任务文件> <调度方式:auto|local|doubao|expert|codex>
"""
import sys, subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
AUTO_ROUTE = Path(__file__).resolve().parent.parent / 'routing-pipeline' / 'auto_route.py'

ROLES = {
  'auto':   '调度bot 自动判断（简报先行）',
  'local':  '整理bot（本地免费）',
  'doubao': '轻量bot 豆包（便宜）',
  'expert': '专家bot（免费强模型）',
  'codex':  '编码bot Codex→DeepSeek（占位，见说明）',
}

def main():
    if len(sys.argv) < 3 or sys.argv[2] not in ROLES:
        raise SystemExit('用法: workgroup.py <任务文件> <auto|local|doubao|expert|codex>')
    task, mode = Path(sys.argv[1]), sys.argv[2]
    if not task.exists(): raise SystemExit('任务文件不存在')
    print(f'【工作小组】调度方式={ROLES[mode]}')
    print('—— 群规：简报先行 / @才发言 / 单轮 ——')
    if mode == 'auto':
        # 复用 auto_route：本地简报 + 自动判断 + 自动派发
        r = subprocess.run([sys.executable, str(AUTO_ROUTE), str(task)], capture_output=True, text=True, encoding='utf-8')
        print(r.stdout)
        if r.returncode != 0: print('[错误]', r.stderr[:300])
    elif mode == 'local':
        print('[整理bot] 本地前处理（免费）：调用 pipeline.py prepare')
        pipe = AUTO_ROUTE.parent / 'pipeline.py'
        r = subprocess.run([sys.executable, str(pipe), 'prepare', str(task)], capture_output=True, text=True, encoding='utf-8')
        print(r.stdout)
    elif mode == 'doubao':
        print('[轻量bot] 豆包 API（便宜，thinking off）：调用 doubao_assist.py')
        da = AUTO_ROUTE.parent.parent / 'doubao' / 'doubao_assist.py'
        r = subprocess.run([sys.executable, str(da), 'summarize', str(task)], capture_output=True, text=True, encoding='utf-8')
        print(r.stdout)
    elif mode == 'expert':
        print('[专家bot] 免费强模型：用 auto_route.py 的 HEAVY 派发路径')
        r = subprocess.run([sys.executable, str(AUTO_ROUTE), str(task)], capture_output=True, text=True, encoding='utf-8')
        print(r.stdout)
    elif mode == 'codex':
        print('[编码bot] Codex 已通过 magpie 网关接 deepseek/deepseek-flash。')
        print('   真实编码任务应在 Codex CLI 中执行（~/.codex/config.toml 已配好）。')
        print('   本脚本不直接驱动 Codex CLI；群内编码任务请@它并附简报文件路径。')

if __name__ == '__main__':
    main()