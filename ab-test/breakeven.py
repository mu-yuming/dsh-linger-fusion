import json, urllib.request, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
LOCAL='http://127.0.0.1:11434/v1/chat/completions'
GW='http://127.0.0.1:3425/v1/chat/completions'
def env(n):
    for l in (Path.home()/'.dsh'/'.env').read_text(encoding='utf-8').splitlines():
        if l.startswith(n+'='): return l.split('=',1)[1].strip()
    return ''
def post(u,p,a=None,t=300):
    h={'Content-Type':'application/json'}
    if a: h['Authorization']='Bearer '+a
    r=urllib.request.Request(u,data=json.dumps(p).encode(),headers=h)
    with urllib.request.urlopen(r,timeout=t) as x: return json.loads(x.read())
base=Path('C:/AI/github-sync/routing-pipeline/sample-long-task.md').read_text(encoding='utf-8')
Q='\n\n请用3条要点总结上述材料的核心内容。'
print('倍数 原文tok 简报tok B输入tok 节省率')
for m in [2,6,12]:
    mat = base*m
    dA=post(GW,{'model':'opencode-zen-free/hy4-flash-free','messages':[{'role':'user','content':mat+Q}],'reasoning_effort':'none','max_tokens':400},env('MAGPIE_GATEWAY_KEY'))
    a_in=dA.get('usage',{}).get('prompt_tokens',0)
    br=post(LOCAL,{'model':'qwen3-35b-a3b','messages':[{'role':'user','content':'整理成简报，保留关键数字事实，删除冗余：\n'+mat}],'max_tokens':700})
    bt=br['choices'][0]['message']['content'].strip()
    dB=post(GW,{'model':'opencode-zen-free/hy4-flash-free','messages':[{'role':'user','content':'【简报】\n'+bt+Q}],'reasoning_effort':'none','max_tokens':400},env('MAGPIE_GATEWAY_KEY'))
    b_in=dB.get('usage',{}).get('prompt_tokens',0)
    bt_tok=br.get('usage',{}).get('prompt_tokens',0)+br.get('usage',{}).get('completion_tokens',0)
    print(f'{m:3d}x  {a_in:6d}  {bt_tok:6d}  {b_in:7d}  {100*(1-b_in/a_in):+6.0f}%')