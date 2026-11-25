#!/usr/bin/env python3
"""分层任务路由 Demo：本地模型做前处理，在线模型只拿压缩后的简报。

流程：原文 → 本地llama.cpp整理成结构化简报 → 估算节省 → 派发给在线模型。
本地端点：http://127.0.0.1:11434/v1（llama.cpp, qwen3-35b-a3b）
在线端点：火山方舟豆包 API（便宜杂活）/ workbuddy 由 DSH subagent 派发（强推理）。

用法：
  python pipeline.py prepare  <文件>        # 本地前处理，输出简报到 stdout 并存 .brief.md
  python pipeline.py estimate <文件>        # 只估算 token 节省（不调用在线模型）
"""
import json, sys, urllib.request, re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
LOCAL_URL = 'http://127.0.0.1:11434/v1/chat/completions'
LOCAL_MODEL = 'qwen3-35b-a3b'

PREPARE_PROMPT = '''你是任务前处理助手。请把下面的原始材料整理成结构化简报，严格按四段输出：
【背景】一句话说明这是什么场景
【目标】用户要解决什么问题
【关键数据】列出必须保留的数字/事实/约束（最多5条）
【建议派发】判断该任务交给哪类在线模型：轻量(摘要/分类/初筛) 或 重度(推理/创作/决策)，并说明一句理由
要求：只保留在线模型做判断真正需要的信息，删除冗余叙述。简报务必显著短于原文。

--- 原始材料 ---
'''

def call_local(text):
    body = json.dumps({
        'model': LOCAL_MODEL,
        'messages': [{'role':'user','content': PREPARE_PROMPT + text[:20000]}],
        'max_tokens': 1200,
    }).encode('utf-8')
    req = urllib.request.Request(LOCAL_URL, data=body, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read().decode('utf-8'))
    return d['choices'][0]['message']['content'].strip()

def approx_tokens(s):
    # 中文约1字≈1token，英文约4字符≈1token，粗略估算
    cn = len(re.findall(r'[\u4e00-\u9fff]', s))
    other = len(re.sub(r'[\u4e00-\u9fff\s]', '', s))
    return cn + other // 4

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv)>1 else 'prepare'
    src = Path(sys.argv[2]) if len(sys.argv)>2 else None
    if not src or not src.exists(): raise SystemExit('用法: pipeline.py {prepare|estimate} <文件>')
    text = src.read_text(encoding='utf-8')
    orig = approx_tokens(text)
    if mode == 'estimate':
        print(f'原文估算 token: {orig}'); raise SystemExit
    brief = call_local(text)
    bt = approx_tokens(brief)
    out = src.with_suffix('.brief.md')
    out.write_text(brief, encoding='utf-8')
    print('===== 本地整理后的简报 =====')
    print(brief)
    print('===== 节省估算 =====')
    print(f'原文≈{orig} token → 简报≈{bt} token → 节省约 {100*(1-bt/orig):.0f}% 的在线输入 token')
    print(f'简报已保存: {out}')