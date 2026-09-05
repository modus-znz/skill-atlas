import json,os,glob,re,sys

def fm(p):
    try: t=open(p,encoding='utf-8',errors='replace').read()
    except: return None
    if not t.startswith('---'): return None
    end=t.find('\n---',3)
    if end<0: return None
    head=t[3:end]
    def grab(key):
        m=re.search(r'^%s:\s*(.*?)\s*$(?=\n\S|\n---|\Z)'%key,head,re.M|re.S)
        if not m: return ''
        v=m.group(1).strip()
        if v[:1] in '"\'' and v[-1:]==v[:1]: v=v[1:-1]
        return ' '.join(v.split())
    return grab('name'), grab('description'), grab('when_to_use')

S=json.load(open(os.path.expanduser('~/.claude/settings.json')))
ov=S.get('skillOverrides',{})
CAP=1536
rows=[]

# local skills
for d in sorted(glob.glob(os.path.expanduser('~/.claude/skills/*/SKILL.md'))):
    slug=os.path.basename(os.path.dirname(d))
    st=ov.get(slug,'on')
    r=fm(d)
    if not r: continue
    name,desc,wtu=r
    name=name or slug
    if st in ('off','user-invocable-only'): continue
    rows.append(('local',slug,name,desc,wtu,st))

# plugin skills
PLUG={
 'frontend-design':'~/.claude/plugins/cache/claude-plugins-official/frontend-design/*/skills',
 'chrome-devtools-mcp':'~/.claude/plugins/cache/claude-plugins-official/chrome-devtools-mcp/*/skills',
 'superpowers':'~/.claude/plugins/cache/claude-plugins-official/superpowers/*/skills',
 'gsap-skills':'~/.claude/plugins/cache/gsap-skills/gsap-skills/*/skills',
 'ui-ux-pro-max':'~/.claude/plugins/cache/ui-ux-pro-max-skill/ui-ux-pro-max/*/.claude/skills',
 'video-captions':'~/.claude/plugins/cache/katareayush/video-captions/*/skills',
 'video-prep':'~/.claude/plugins/cache/video-prep/video-prep/*/skills',
 'claude-video-digest':'~/.claude/plugins/cache/anaidenko/claude-video-digest/*/skills',
}
for pn,pat in PLUG.items():
    base=sorted(glob.glob(os.path.expanduser(pat)))
    if not base: print('MISSING',pn,pat,file=sys.stderr); continue
    for d in sorted(glob.glob(base[-1]+'/*/SKILL.md')):
        r=fm(d)
        if not r: continue
        name,desc,wtu=r
        name=name or os.path.basename(os.path.dirname(d))
        rows.append((pn,pn,f'{pn}:{name}',desc,wtu,'plugin'))

tot=0; out=[]
for src,slug,name,desc,wtu,st in rows:
    full=f'{desc} - {wtu}' if wtu else desc
    el=len(name)+4+min(len(full),CAP)
    tot+=el
    out.append((el,src,name,len(full)))
E=tot+(len(rows)-1)
print(f'ENTRIES={len(rows)}  E={E}  (binary reported 95 / 31532)')
print(f'budget f=0.01 -> 6000 | f=0.03 -> 18000 | need to cut {E-18000}')
print('\n--- by source ---')
agg={}
for el,src,name,dl in out: a=agg.setdefault(src,[0,0]); a[0]+=1; a[1]+=el
for src,(c,s) in sorted(agg.items(),key=lambda x:-x[1][1]):
    print(f'{src:24s} {c:3d} entries  {s:6d} ch')
print('\n--- fattest 30 ---')
for el,src,name,dl in sorted(out,reverse=True)[:30]:
    print(f'{el:5d}  {src:20s} {name}')
