"""Prefix every item display name with "PR&D - " (idempotent; skips #localized keys). Run after any gen_*.py."""
import os, re, sys
ROOTS=[os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "SFHELMETS")]
PAT=re.compile(r'(ItemDisplayName\s+\w+\s+"\{[0-9A-F]+\}"\s*\{\s*\n(?:[^\n]*\n)*?\s*Name\s+")([^"]*)(")')
WRITE=not (len(sys.argv)>1 and sys.argv[1]=="dry")
PREFIX="PR&D - "
tot=0
for root in ROOTS:
    n=0; names=set(); skipped=set()
    for dp,dn,fn in os.walk(root):
        dn[:]=[d for d in dn if d not in (".git","_tools")]
        for f in fn:
            if not f.endswith((".et",".conf")): continue
            p=os.path.join(dp,f); s=open(p,encoding="utf-8",newline="").read()
            def rep(m):
                global n
                name=m.group(2)
                if name.startswith("#") or name.startswith(PREFIX) or not name:
                    skipped.add(name); return m.group(0)
                names.add(name)
                return m.group(1)+PREFIX+name+m.group(3)
            new=PAT.sub(rep,s)
            if new!=s:
                n+=1
                if WRITE: open(p,"w",encoding="utf-8",newline="").write(new)
    print(f"{root}: files {n}, names {len(names)}, skipped {sorted(skipped)}")
    for x in sorted(names)[:6]: print("   ",x)
    brand=[x for x in names if re.search(r"vanguard|outlaw|kagwerks",x,re.I)]
    if brand: print("    BRANDED:",brand)
