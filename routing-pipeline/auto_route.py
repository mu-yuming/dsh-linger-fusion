#!/usr/bin/env python3
"""端到端分层路由：本地简报 → 自动判断 → 自动派发在线模型。一条命令跑完。

流程：
  ① 本地 llama.cpp（免费）把原文整理成结构化简报，并给出【建议派发】
  ② 解析简报判断 light / heavy
  ③ 自动派发：light→豆包API（便宜）；heavy→magpie网关免费强模型（省钱）
  ④ 输出最终结果 + token 节省报告

所有 key 从 ~/.dsh/.env 读取，不写入本文件、不进仓库。
用法：python auto_route.py <任务文件>
"""
import json, sys, urllib.request, re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
LOCAL_URL = 'http://127.0.0.1:11434/v1/chat/completions'
LOCAL_MODEL = 'qwen3-35b-a3b'
GW_URL = 'http://127.0.0.1:3425/v1/chat/completions'
GW_HEAVY_MODEL = 'opencode-zen-free/hy4-flash-free'  # 免费模型，输出干净，省钱；需顶级推理可换 auto/deepseek-v4-pro(付费)
DOUBAO_URL = 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'
DOUBAO_MODEL = 'doubao-seed-2-1-turbo-260628'

def extract(d):
    try:
        m = d['choices'][0]['message']
        c = m.get('content') or ''
        if not c.strip(): c = m.get('reasoning_content') or ''
        return c.strip() or '(模型未返回文本)'
    except Exception:
        return str(d)[:200]

def env_value(name):
    for line in (Path.home()/'.dsh'/'.env').read_text(encoding='utf-8').splitlines():
        if line.startswith(name+'='):
            return line.split('=',1)[1].strip()
    return ''

import time

def post(url, payload, auth=None):
    headers = {'Content-Type':'application/json'}
    if auth: headers['Authorization'] = 'Bearer ' + auth
    last = None
    for attempt in range(1, 4):
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode('utf-8'))
        except Exception as e:
            last = e
            if attempt < 3: time.sleep(2 * attempt)  # 偶发 502 重试，退避
    raise SystemExit(f'调用失败(重试3次) {url}: {last}')

def approx(s):
    cn = len(re.findall(r'[\u4e00-\u9fff]', s))
    oth = len(re.sub(r'[\u4e00-\u9fff\s]', '', s))
    return cn + oth//4

PREP = '''你是任务前处理助手。把原始材料整理成结构化简报，严格按四段输出：
【背景】一句话
【目标】一句话
【关键数据】必须保留的数字/事实/约束，最多5条
【建议派发】只输出 LIGHT 或 HEAVY 加一句理由。LIGHT=摘要/分类/初筛等简单任务；HEAVY=推理/创作/决策等复杂任务
要求：简报显著短于原文，只留在线模型判断真正需要的信息。

--- 原始材料 ---
'''

def make_brief(text):
    d = post(LOCAL_URL, {'model':LOCAL_MODEL,
        'messages':[{'role':'user','content':PREP+text[:20000]}], 'max_tokens':1200})
    return d['choices'][0]['message']['content'].strip()

def decide(brief):
    m = re.search(r'【建议派发】\s*(LIGHT|HEAVY)', brief)
    return m.group(1) if m else 'HEAVY'  # 默认走重度，安全

def dispatch(brief, target):
    if target == 'LIGHT':
        d = post(DOUBAO_URL, {'model':DOUBAO_MODEL,
            'messages':[{'role':'user','content':'基于以下简报完成用户任务，直接给结果：\n'+brief}],
            'thinking':{'type':'disabled'}, 'max_tokens':800}, env_value('ARK_API_KEY'))
        return '豆包(轻量)', extract(d)
    else:
        d = post(GW_URL, {'model':GW_HEAVY_MODEL,
            'messages':[{'role':'user','content':'基于以下简报完成用户任务，直接给结果：\n'+brief}],
            'reasoning_effort':'none', 'max_tokens':800}, env_value('MAGPIE_GATEWAY_KEY'))
        return GW_HEAVY_MODEL+'(免费)', extract(d)

if __name__ == '__main__':
    if len(sys.argv)<2 or not Path(sys.argv[1]).exists(): raise SystemExit('用法: auto_route.py <任务文件>')
    text = Path(sys.argv[1]).read_text(encoding='utf-8')
    orig = approx(text)
    SKIP_THRESHOLD = 1500  # 实测盈亏平衡点：低于此值做简报是负收益
    if orig < SKIP_THRESHOLD:
        print(f'① 原文仅 {orig} token < {SKIP_THRESHOLD}，跳过简报（实测做简报负收益）')
        brief = text
        bt = orig
        target = decide(text)
    else:
        print('① 本地前处理中（免费）...')
        brief = make_brief(text)
        bt = approx(brief)
        target = decide(brief)
    print(f'   简报 {bt} token（原文 {orig}，省 {100*(1-bt/orig):.0f}%）| 派发判断: {target}')
    print('② 自动派发到在线模型...')
    who, result = dispatch(brief, target)
    print(f'   模型: {who}')
    print('③ 最终结果:')
    print(result)
    Path(sys.argv[1]).with_suffix('.brief.md').write_text(brief,encoding='utf-8')
    print(f'\n[简报已存 .brief.md] 在线输入 token 节省约 {100*(1-bt/orig):.0f}%')