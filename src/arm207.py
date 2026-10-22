from pathlib import Path
import sys,struct,re,json,os
ROOT=Path(os.environ.get("SXFI_BUILD_DIR", Path(__file__).resolve().parents[1]/"build")).resolve()
from capstone import *
from capstone.arm import *
b=(ROOT/"FMAIN.bin").read_bytes()
SOURCE=struct.unpack_from("<I",b,0x24)[0]
EXEC=struct.unpack_from("<I",b,0x28)[0]
resident=struct.unpack_from("<I",b,0x2c)[0]
maps=[(0,EXEC,resident)]
tables=[]
for a,z in [(0x20c,0x210),(0x214,0x218)]:
 start,end=[struct.unpack_from("<I",b,o)[0]-EXEC for o in [a,z]]
 assert 0<=start<=end<=resident and (end-start)%12==0
 tables.append((start,end))
 for o in range(start,end,12):
  src,dest,n=struct.unpack_from("<III",b,o)
  if n:
   assert SOURCE<=src and src-SOURCE+n<=len(b)
   maps.append((src-SOURCE,dest,n))

def offset(addr):
 addr&=~1
 for off,dest,n in maps:
  if dest<=addr<dest+n:return off+addr-dest
 if SOURCE<=addr<SOURCE+len(b):return addr-SOURCE
 return None
def addr(off):
 for start,dest,n in maps:
  if start<=off<start+n:return dest+off-start
 return SOURCE+off
def rawoff(a):
 for off,dest,n in maps:
  if dest<=a<dest+n:return off+a-dest
 if SOURCE<=a<SOURCE+len(b):return a-SOURCE
 return None
def u32(a):
 off=rawoff(a)
 return struct.unpack_from("<I",b,off)[0] if off is not None and off<=len(b)-4 else None
def txt(a):
 off=rawoff(a)
 if off is None:return ""
 v=b[off:off+140].split(b"\0")[0]
 return v.decode("ascii") if len(v)>=3 and all(32<=x<127 for x in v) else ""
def dis(addr0,size,mode=None):
 off=offset(addr0)
 if off is None:raise ValueError("Unmapped "+hex(addr0))
 mode=mode or ("thumb" if addr0&1 or addr0>=0x40000000 or 0x10000400<=addr0<0x100065d4 else "arm")
 m=Cs(CS_ARCH_ARM,CS_MODE_THUMB if mode=="thumb" else CS_MODE_ARM);m.detail=True;m.skipdata=True
 return m.disasm(b[off:off+size],addr0&~1)
def detail(i):
 extra=[]
 if i.id:
  for op in i.operands:
   if op.type==ARM_OP_MEM and op.mem.base==ARM_REG_PC:
    pc=(i.address+4)&~3 if i.size==2 or i.mnemonic.endswith(".w") or i.address>=0x40000000 else i.address+8
    la=pc+op.mem.disp;v=u32(la)
    if v is not None:extra.append("literal@"+hex(la)+"="+hex(v)+" "+repr(txt(v)))
 return hex(i.address)+"  "+i.mnemonic+" "+i.op_str+(" ; "+" | ".join(extra) if extra else "")
if __name__=="__main__":
 cmd=sys.argv[1]
 if cmd=="map":
  out={"source_base":SOURCE,"execution_base":EXEC,"regions":[{"file_offset":o,"address":d,"size":n} for o,d,n in maps]}
  (ROOT/"FMAIN-memory-map.json").write_text(json.dumps(out,indent=2))
  print(json.dumps(out))
 if cmd=="dump":
  for i in dis(int(sys.argv[2],0),int(sys.argv[3],0) if len(sys.argv)>3 else 256,sys.argv[4] if len(sys.argv)>4 else None):print(detail(i))
 if cmd=="strings":
  p=re.compile(sys.argv[2],re.I)
  for m in re.finditer(rb"[ -~]{5,}",b):
   s=m.group().decode()
   if p.search(s):print(hex(addr(m.start())),hex(m.start()),s)
 if cmd=="refs":
  p=re.compile(sys.argv[2],re.I)
  for m in re.finditer(rb"[ -~]{5,}",b):
   s=m.group().decode()
   if not p.search(s):continue
   a=addr(m.start());refs=[x.start() for x in re.finditer(re.escape(struct.pack("<I",a)),b)]
   print("STRING",hex(a),s,"POINTERS",[hex(addr(x)) for x in refs])
   for off in refs:
    start=max(0,off-16)&~3
    print("TABLE",[(hex(addr(x)),hex(u32(addr(x))) if u32(addr(x)) is not None else None,txt(u32(addr(x)) or 0)) for x in range(start,min(len(b)-4,off+28),4)])
