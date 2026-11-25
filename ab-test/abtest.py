#!/usr/bin/env python3
"""A/B 质量验证：原文直给 vs 本地简报后给，同一在线模型。"""
import json, sys, urllib.request, re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
LOCAL = 'http://127.0.0.1:11434/v1/chat/completions'
LOCAL_MODEL = 'qwen3-35b-a3b'
GW = 'http://127.0.0.1:3425/v1/chat/completions'
GW_MODEL = 'opencode-zen-free/hy4-flash-free'

def env(name):
    for l in (Path.home()/'.dsh'/'.env').read_text(encoding='utf-8').splitlines():
        if l.startswith(name+'='): return l.split('=',1)[1].strip()
    return ''

def post(url, payload, auth=None, timeout=300):
    h = {'Content-Type':'application/json'}
    if auth: h['Authorization'] = 'Bearer ' + auth
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def brief(text):
    p = ('你是任务前处理助手。把材料整理成简报，保留所有关键数字、时间点、约束条件，删除冗余叙述。\n'
         '严格四段：【背景】【目标】【关键数据】【约束】\n\n' + text)
    d = post(LOCAL, {'model':LOCAL_MODEL,'messages':[{'role':'user','content':p}],'max_tokens':900})
    return d['choices'][0]['message']['content'].strip()

def answer(question_block, content):
    p = content + '\n\n' + question_block
    d = post(GW, {'model':GW_MODEL,'messages':[{'role':'user','content':p}],
                  'reasoning_effort':'none','max_tokens':1500}, env('MAGPIE_GATEWAY_KEY'))
    u = d.get('usage', {})
    return d['choices'][0]['message'].get('content') or '', u.get('prompt_tokens',0), u.get('completion_tokens',0)

if __name__ == '__main__':
    task = Path(sys.argv[1])
    _log = open(task.with_suffix('.result.txt'), 'w', encoding='utf-8')
    _orig = sys.stdout
    class _T:
        def write(self, s):
            _orig.write(s); _log.write(s)
        def flush(self):
            _orig.flush(); _log.flush()
    sys.stdout = _T()
    full = task.read_text(encoding='utf-8')
    idx = full.find('## 请回答')
    material, questions = full[:idx], full[idx:]
    print('=' * 60)
    print('任务:', task.name)
    print('=' * 60)
    # A 组：原文直给
    a_out, a_in, a_outtok = answer(questions, material)
    print(f'\n--- A 组（原文直给）输入 {a_in} tok, 输出 {a_outtok} tok ---')
    print(a_out[:1200])
    # B 组：本地简报
    b_brief = brief(material)
    b_out, b_in, b_outtok = answer(questions, f'【以下是本地模型整理的简报】\n{b_brief}')
    print(f'\n--- 本地简报（{len(b_brief)} 字符）---')
    print(b_brief[:700])
    print(f'\n--- B 组（简报后给）输入 {b_in} tok, 输出 {b_outtok} tok ---')
    print(b_out[:1200])
    print(f'\n>>> token 对比: A={a_in} B={b_in} 节省={100*(1-b_in/a_in):.0f}%')