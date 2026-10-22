from pathlib import Path
import struct,json,hashlib,sys
import arm207 as a
from keystone import Ks,KS_ARCH_ARM,KS_MODE_THUMB
R=a.ROOT
ORIGINAL_SHA="7bcca20699b7bfe746923fd1791a4cc36a5021f0389ae9ce65c56dfd78bec761"
CIFF_SHA="0ebab178dd4f9aa5b0c3ea975040279df39bd2aec7073bfef55c288bd12c4eb3"
sha=lambda b:hashlib.sha256(b).hexdigest()
old=(R/"FMAIN.bin").read_bytes();container=(R/"CUDSP600_RDCATA.bin").read_bytes()
assert sha(old)==ORIGINAL_SHA and sha(container)==CIFF_SHA
BASE=0x400d03e0;RESERVE=256;STATE=BASE+RESERVE-4;HOOK=0x4001a402
assert struct.unpack_from("<I",old,0x1cd0)[0]==BASE
assert struct.unpack_from("<III",old,0x4bc)==(0x2004c0f0,0x40000000,0)
bss=[struct.unpack_from("<II",old,p) for p in range(0x4e0,0x4f8,8)]
assert all(d+n<=BASE or d>=BASE+RESERVE for d,n in bss)
assert max(d+n for d,n in bss if d>=0x40000000)==0x400d03cc
ks=Ks(KS_ARCH_ARM,KS_MODE_THUMB)
source=Path(__file__).with_name("cycle.s").read_text(encoding="utf-8")
assert "5001" not in source
code=bytes(ks.asm(source,BASE)[0]);TRAMP=(BASE+len(code)+3)&~3
tramp_source=f"""
ldr r3,={BASE|1:#x}
blx r3
cmp r0,#0
beq failed
ldr r3,={STATE:#x}
ldrb r3,[r3]
cmp r3,#0
beq off
ldr r3,=0x4001a421
bx r3
off:
ldr r3,=0x4001a44b
bx r3
failed:
ldr r3,=0x4001a3bd
bx r3
"""
tramp=bytes(ks.asm(tramp_source,TRAMP)[0])
assert TRAMP+len(tramp)<=STATE
payload=bytearray(RESERVE)
payload[:len(code)]=code
payload[TRAMP-BASE:TRAMP-BASE+len(tramp)]=tramp
overlay=bytes(ks.asm("ldr.w pc,[pc,#4];nop",HOOK)[0])+struct.pack("<I",TRAMP|1)+bytes(ks.asm("nop",HOOK+10)[0])
assert len(overlay)==12
new=bytearray(old);patches=[]
def patch(offset,after,label):
 before=bytes(new[offset:offset+len(after)])
 patches.append({"label":label,"file_offset":hex(offset),"length":len(after),"before":before.hex(),"after":bytes(after).hex()})
 new[offset:offset+len(after)]=after
patch(0x1cd0,struct.pack("<I",BASE+RESERVE),"reserve256 bytes from pool1 start; end unchanged")
patch(0x4bc,struct.pack("<III",a.SOURCE+len(old),BASE,RESERVE),"use formerly zero-length startup copy entry")
patch(a.offset(HOOK),overlay,"only hardware mic-key branch after guards")
new.extend(payload)
assert len(new)==len(old)+RESERVE
covered=set()
for p in patches:
 off=int(p["file_offset"],16);covered.update(range(off,off+p["length"]))
assert all(old[i]==new[i] for i in range(len(old)) if i not in covered)
# Every pre-existing initialized region retains its destination and size.
def maps(b):
 out=[(0,a.EXEC,struct.unpack_from("<I",b,0x2c)[0])]
 for st,en in [(0x48c,0x4b0),(0x4b0,0x4e0)]:
  for o in range(st,en,12):
   src,dest,n=struct.unpack_from("<III",b,o)
   if n:out.append((src-a.SOURCE,dest,n))
 return out
newmaps=maps(new)
for off,d,n in a.maps:assert (off,d,n) in newmaps
# Rebuild CIFF: retain all original chunks except FMAIN and its length; recompute CHK2.
assert container[:4]==b"CIFF"
pos=8;chunks=[];before_chunks=[];seen=0
while pos<len(container):
 tag=container[pos:pos+4];n=struct.unpack_from("<I",container,pos+4)[0]
 data=container[pos+8:pos+8+n];assert len(data)==n
 if tag==b"CHK2":
  assert sha(container[8:pos])==data.hex() and n==32
  assert pos+8+n==len(container)
 else:
  before_chunks.append((tag,data))
  if tag==b"DATA" and data[:32].decode("utf-16le").rstrip("\0")=="FMAIN":
   assert data[32:]==old;data=data[:32]+new;seen+=1
  chunks.append(tag+struct.pack("<I",len(data))+data)
 pos+=8+n
assert seen==1
body=b"".join(chunks)
ciff=b"CIFF"+struct.pack("<I",len(body))+body+b"CHK2"+struct.pack("<I",32)+hashlib.sha256(body).digest()
assert struct.unpack_from("<I",ciff,4)[0]+48==len(ciff)
pos=8;after_chunks=[]
while pos<len(ciff):
 tag=ciff[pos:pos+4];n=struct.unpack_from("<I",ciff,pos+4)[0];data=ciff[pos+8:pos+8+n]
 if tag==b"CHK2":assert data==hashlib.sha256(ciff[8:pos]).digest()
 else:after_chunks.append((tag,data))
 pos+=8+n
assert len(before_chunks)==len(after_chunks)
for (t,b),(t2,c) in zip(before_chunks,after_chunks):
 assert t==t2
 if t==b"DATA" and b[:32].decode("utf-16le").rstrip("\0")=="FMAIN":continue
 assert b==c
assert sha(new)=="4ae6e3b6f4e14d310f6dedafe3293c48a6658137f757fd1b1999ce3ec160b05b"
assert sha(ciff)=="0af6cbe38b9302db1d614374ff20339f556b1cbdf443712bf1082a3350867887"
out=R/"candidate";out.mkdir(exist_ok=True)
(out/"FMAIN.experimental.bin").write_bytes(new)
(out/"SXFI_GAMER_2.07.02-three-state-r1.experimental.ciff").write_bytes(ciff)
(out/"cycle.s").write_text(source)
(out/"trampoline.s").write_text(tramp_source)
report={"canonical_truth":False,"status":"OFFLINE_REPRODUCIBLE_BUILD","model":"Creative SXFI GAMER EF0880","usb":"041E:3269","base_version":"2.07.02","revision":"three-state-r1","original_FMAIN_sha256":sha(old),"modified_FMAIN_sha256":sha(new),"original_CIFF_sha256":sha(container),"modified_CIFF_sha256":sha(ciff),"original_bytes":len(old),"modified_bytes":len(new),"code":hex(BASE),"code_bytes":len(code),"trampoline":hex(TRAMP),"trampoline_bytes":len(tramp),"state":hex(STATE),"reserved_bytes":RESERVE,"original_pool1":[hex(BASE),"0x405503e0"],"modified_pool1":[hex(BASE+RESERVE),"0x405503e0"],"original_BSS_ranges":[[hex(d),hex(n)] for d,n in bss],"new_startup_copy":[hex(a.SOURCE+len(old)),hex(BASE),RESERVE],"patches":patches,"new_memory_map":[[hex(o),hex(d),n] for o,d,n in newmaps],"unchanged":["all other FMAIN bytes","global guarded setter/common mic","existing startup destinations/BSS/stack sizes","FBOOT","voice files","all CIFF chunks other than FMAIN and CHK2"],"validated_container_checks":["CIFF structural lengths","CHK2 SHA256","exact FMAIN replacement","all other chunks byte identical"],"not_proven":["this offline run does not test hardware; see docs/VALIDATION.md"],"no_device_commands":True,"no_flashing":True}
(out/"patch-manifest.json").write_text(json.dumps(report,indent=2))
print(json.dumps({k:report[k] for k in ["status","modified_FMAIN_sha256","modified_CIFF_sha256","code","code_bytes","trampoline","trampoline_bytes","state","reserved_bytes"]},indent=2))
