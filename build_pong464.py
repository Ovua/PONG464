"""Dependency-free two-pass Z80 assembler for this Pong source (not a full assembler).
Builds the .BIN and a type-in friendly .BAS with DATA decimal bytes.
"""
import re
from pathlib import Path
HERE = Path(__file__).resolve().parent
source = (HERE/'PONG464.ASM').read_text()
lines = []
for line in source.splitlines():
    line = line.split(';', 1)[0].strip()
    if not line: continue
    m = re.match(r'^(\w+):\s*(.*)$',line)
    label = None
    if m: label, line = m.groups()
    if label or line: lines.append((label, line.strip()))

R8 = {'b':0, 'c':1,'d':2,'e':3,'h':4,'l':5,'(hl)':6,'a':7}
R16={'bc':0,'de':1,'hl':2,'sp':3}
PUSH={'bc':0xC5,'de':0xD5,'hl':0xE5,'af':0xF5}
POP={'bc':0xC1,'de':0xD1,'hl':0xE1,'af':0xF1}
SINGLE={'ret':0xC9,'scf':0x37,'xor a':0xAF,'or a':0xB7}
CONDITIONS={'nz':0x20,'z':0x28,'nc':0x30,'c':0x38}
RETCC={'nz':0xC0,'z':0xC8,'nc':0xD0,'c':0xD8}

def value(s, syms, strict):
    s=s.strip()
    if s.startswith('&'):return int(s[1:],16)
    if re.fullmatch(r'-?\d+',s):return int(s)
    if s.upper() in syms:return syms[s.upper()]
    if not strict:return 0
    raise ValueError(f'unresolved symbol {s!r}')

def enc(assembly, pc, symbols, strict):
    if not assembly:return []
    ss=assembly.split(maxsplit=1)
    op=ss[0].lower()
    arg=ss[1].strip() if len(ss)==2 else ''
    argl=arg.lower()
    if op=='org':return []
    if op=='db':return [value(i,symbols,strict)&0xff for i in arg.split(',')]
    if assembly.lower() in SINGLE:return [SINGLE[assembly.lower()]]
    if op=='ret' and argl in RETCC:return [RETCC[argl]]
    if op=='push':return [PUSH[argl]]
    if op=='pop':return [POP[argl]]
    if op=='call':
        n=value(arg,symbols,strict)
        return [0xCD,n&0xFF,(n>>8)&0xFF]
    if op=='jp':
        n=value(arg,symbols,strict)
        return [0xC3,n&0xFF,(n>>8)&0xFF]
    if op in ('jr','djnz'):
        if op=='djnz':code=0x10;target=arg
        elif ',' in arg:
            c,target=[s.strip() for s in arg.split(',',1)]
            code=CONDITIONS[c.lower()]
        else:code=0x18;target=arg
        to=value(target,symbols,strict)
        off=to-(pc+2)
        if strict and not -128<=off<=127:
            raise ValueError(f'out-of-range JR from {pc:04X} to {to:04X} ({off})')
        return [code,off&255]
    if op=='ld':
        dst,src=[a.strip() for a in argl.split(',',1)]
        if dst in R8 and src in R8: return [0x40+R8[dst]*8+R8[src]]
        if dst=='a' and src.startswith('(') and src.endswith(')'):
            n=value(src[1:-1],symbols,strict)
            return [0x3A,n&255,(n>>8)&255]
        if dst in R8:
            n=value(src,symbols,strict)
            return [0x06+R8[dst]*8,n&255]
        if dst in R16:
            n=value(src,symbols,strict)
            return [0x01+R16[dst]*16,n&255,(n>>8)&255]
        if dst.startswith('(') and dst.endswith(')') and src=='a':
            n=value(dst[1:-1],symbols,strict)
            return [0x32,n&255,(n>>8)&255]
        if dst=='a' and src.startswith('(') and src.endswith(')'):
            n=value(src[1:-1],symbols,strict)
            return [0x3A,n&255,(n>>8)&255]
    if op in ('inc','dec'):
        if argl in R8:return [(0x04 if op=='inc' else 0x05)+R8[argl]*8]
        if argl in R16:return [(0x03 if op=='inc' else 0x0B)+R16[argl]*16]
    if op=='cp':
        if argl in R8:return [0xB8+R8[argl]]
        return [0xFE,value(arg,symbols,strict)&255]
    if op=='xor': return [0xEE,value(arg,symbols,strict)&255]
    if op=='and': return [0xE6,value(arg,symbols,strict)&255]
    if op=='add':
        dst,src=[a.strip() for a in argl.split(',',1)]
        if dst=='hl' and src in R16:return [0x09+R16[src]*16]
        if dst=='a':
            if src in R8:return [0x80+R8[src]]
            return [0xC6,value(src,symbols,strict)&255]
    raise ValueError(f'Unknown instruction: {assembly}')

symbols={}
pc=0
for label,assem in lines:
    if label:
        if label in symbols: raise ValueError('Duplicate '+label)
        symbols[label]=pc
    if assem.lower().startswith('org '):pc=value(assem.split(' ',1)[1],symbols,False)
    else:pc+=len(enc(assem,pc,symbols,False))

bytecode=[]
pc=0
for label,assem in lines:
    if assem.lower().startswith('org '):
        pc=value(assem.split(' ',1)[1],symbols,True)
    else:
        b=enc(assem,pc,symbols,True)
        bytecode.extend(b)
        pc+=len(b)
assert symbols['START']==0x9000
assert len(bytecode) == symbols['END_CODE']-0x9000
(HERE/'PONG464.BIN').write_bytes(bytes(bytecode))

basic=[
'10 MEMORY &8FFF',
'20 MODE 1:INK 0,0:INK 1,26:INK 2,6:INK 3,18:BORDER 0',
f'30 CK=0:FOR I=0 TO {len(bytecode)-1}:READ V:POKE &9000+I,V:CK=CK+V:NEXT I',
f'35 IF CK<>{sum(bytecode)} THEN PRINT "DATA ERROR":STOP',
'40 PS=0:CS=0',
'50 CLS:LOCATE 10,1:PRINT "PONG 464 - Z80 + BASIC"',
'60 LOCATE 7,2:PRINT "TU:";PS;"  COMPUTER:";CS',
'70 LOCATE 4,3:PRINT "Q/A O FRECCE  -  ESC ESCI"',
'72 LOCATE 2,4:PRINT STRING$(37,"-")',
'74 LOCATE 2,25:PRINT STRING$(37,"-")',
'80 CALL &9000',
f'90 R=PEEK(&{symbols["RESULT"]:04X}):IF R=3 THEN MODE 1:PRINT "FINE PARTITA":END',
'100 IF R=1 THEN PS=PS+1',
'110 IF R=2 THEN CS=CS+1',
'120 SOUND 1,120,12,12',
'130 IF PS<5 AND CS<5 THEN 50',
'140 CLS:LOCATE 13,10:IF PS=5 THEN PRINT "HAI VINTO!" ELSE PRINT "VINCE IL CPC!"',
'150 LOCATE 5,15:PRINT "PREMI UN TASTO PER RIGIOCARE"',
'160 WHILE INKEY$="":WEND',
'170 PS=0:CS=0:GOTO 50',
]
for line_num,i in enumerate(range(0,len(bytecode),20),start=1000):
    basic.append(f'{line_num} DATA '+','.join(map(str,bytecode[i:i+20])))
(HERE/'PONG464.BAS').write_text('\r\n'.join(basic)+'\r\n',encoding='ascii')
(HERE/'PONG464.MAP').write_text('\n'.join(f'{s:<17} &{addr:04X}' for s,addr in symbols.items())+'\n')
print('Assembly:', len(bytecode), 'bytes, ',len(basic),'BASIC lines')
print('RESULT: &%04X' % symbols['RESULT'])
print('Range &9000-&%04X'% (pc-1))
print('checksum: %d' % sum(bytecode))
