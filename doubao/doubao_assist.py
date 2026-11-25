#!/usr/bin/env python3
"""豆包轻量协同工具 —— API 直连，不经 DSH subagent。

用途：对产线文本（报警日志/工艺记录/文档）做摘要与分类初筛，
作为异构双路（本地Qwen3 + 云端混元）之外的低成本杂活处理。

用法：
  python doubao_assist.py summarize <文件或文本>
  python doubao_assist.py classify <文件或文本>

key 从 ~/.dsh/.env 的 ARK_API_KEY 读取，不写入本文件。
"""
import json, os, sys, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')  # Windows 下强制 UTF-8 输出，避免中文乱码

BASE_URL = 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'
MODEL = 'doubao-seed-2-1-turbo-260628'

PROMPTS = {
    'summarize': '请用中文把以下内容压缩成3条要点，每条不超过30字，只输出要点：',
    'classify': '请判断以下内容属于哪类：报警处置/工艺参数/设备故障/其他。只输出类别名和一句理由：',
}

def load_key():
    env = Path.home() / '.dsh' / '.env'
    for line in env.read_text(encoding='utf-8').splitlines():
        if line.startswith('ARK_API_KEY='):
            k = line.split('=', 1)[1].strip()
            if k: return k
    raise SystemExit('ARK_API_KEY 未配置或为空')

def ask(mode, content):
    body = json.dumps({
        'model': MODEL,
        'messages': [
            {'role': 'system', 'content': PROMPTS[mode]},
            {'role': 'user', 'content': content[:8000]},
        ],
        'max_tokens': 512,
        'thinking': {'type': 'disabled'},
    }).encode('utf-8')
    req = urllib.request.Request(BASE_URL, data=body, headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + load_key(),
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode('utf-8'))
    except Exception as e:
        raise SystemExit(f'API 调用失败: {e}')
    if 'error' in data:
        raise SystemExit(f"API 错误: {data['error'].get('message', data['error'])}")
    return data['choices'][0]['message']['content'].strip()

if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] not in PROMPTS:
        raise SystemExit('用法: doubao_assist.py {summarize|classify} <文本或文件路径>')
    mode, arg = sys.argv[1], sys.argv[2]
    content = Path(arg).read_text(encoding='utf-8') if Path(arg).is_file() else arg
    print(ask(mode, content))