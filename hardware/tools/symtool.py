# SPDX-FileCopyrightText: 2026 stefangrozdanovski-sys
# SPDX-License-Identifier: MIT
import re,sys
def block(s,name):
    i=s.find(f'(symbol "{name}"')
    if i<0: return None
    d=0;j=i
    while True:
        c=s[j]
        if c=='(':d+=1
        elif c==')':
            d-=1
            if d==0:break
        j+=1
    return s[i:j+1]
def pins(lib,name):
    s=open(f'/usr/share/kicad/symbols/{lib}.kicad_sym').read()
    b=block(s,name)
    if b is None: return None
    ext=re.search(r'\(extends "([^"]+)"',b[:300])
    if ext: return ('extends',ext.group(1),pins(lib,ext.group(1)))
    return re.findall(r'\(pin (\w+) \w+ \(at ([-\d.]+) ([-\d.]+) (\d+)\) \(length [\d.]+\)[^)]*?\(name "([^"]*)".*?\(number "([^"]*)"',b,re.S)
if __name__=='__main__':
    for a in sys.argv[1:]:
        lib,n=a.split(':');print(a,pins(lib,n))
