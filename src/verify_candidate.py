from pathlib import Path
import sys,json,hashlib,struct
from mute_manager_emulation import Machine,a
from unicorn.arm_const import *
from unicorn import UcError,UC_HOOK_MEM_INVALID
R=a.ROOT
manifest=json.loads((R/"candidate/patch-manifest.json").read_text())
MOD=(R/"candidate/FMAIN.experimental.bin").read_bytes()
BASE=int(manifest["code"],16);STATE=int(manifest["state"],16);TRAMP=int(manifest["trampoline"],16)
RESERVE=manifest["reserved_bytes"];APPENDED=MOD[-RESERVE:]
BOOT_CACHE={};BOOT_REPORT={}
def sha(x):return hashlib.sha256(x).hexdigest()
class CandidateMachine(Machine):
 def __init__(self,patched=True):
  self.voices=[];self.app_events=[];self.reports=[];self.notifications=[]
  self.mode=3;self.disabled=0;self.busy=0;self.patched=patched;self.booting=False;self.allocations=[]
  super().__init__()
  # Isolated MMIO register model for the interrupt-mask critical section.
  self.u.mem_map(0x08000000,0x1000)
  self.u.mem_write(0x08000004,(255).to_bytes(4,'little'))
  self.u.hook_add(UC_HOOK_MEM_INVALID,self.invalid)
  self.u.mem_map(0x10020000,0x20000)
  self.u.mem_map(0x40100000,0x700000)
  if patched in BOOT_CACHE:
   for addr,b in BOOT_CACHE[patched]:self.u.mem_write(addr,b)
  else:
   b=MOD if patched else a.b
   self.u.mem_map(a.SOURCE,(len(b)+0xfff)&~0xfff);self.u.mem_write(a.SOURCE,b)
   self.u.mem_write(0x10000000,b[:0x80f0])
   # Poison BSS and reserved memory so the native startup must initialize them.
   for p in range(0x4e0,0x4f8,8):
    dest,n=struct.unpack_from("<II",b,p);self.u.mem_write(dest,b"\xa5"*n)
   if patched:self.u.mem_write(BASE,b"\xa5"*RESERVE)
   self.booting=True;self.u.reg_write(UC_ARM_REG_CPSR,0xd3)
   self.u.emu_start(0x10000118,0,count=3000000)
   assert self.u.reg_read(UC_ARM_REG_PC)==0x100001d4
   self.booting=False
   for p in range(0x4e0,0x4f8,8):
    dest,n=struct.unpack_from("<II",b,p);assert bytes(self.u.mem_read(dest,n))==bytes(n)
   for p in [0x48c,0x498,0x4a4,0x4b0,0x4bc,0x4c8,0x4d4]:
    src,dest,n=struct.unpack_from("<III",b,p)
    if n:assert bytes(self.u.mem_read(dest,n))==b[src-a.SOURCE:src-a.SOURCE+n]
   if patched:assert bytes(self.u.mem_read(BASE,RESERVE))==APPENDED
   # Actual stock pool initialization uses modified literal; no heap-init stub.
   self.call(0x10000878)
   descriptor=struct.unpack("<8I",bytes(self.u.mem_read(0x400d0308,32)))
   expect_start=BASE+RESERVE if patched else BASE
   assert descriptor[0]==expect_start and descriptor[1]==0x405503e0,descriptor
   assert struct.unpack("<I",bytes(self.u.mem_read(0x400bb0c8,4)))[0]==0x400d02e8
   assert struct.unpack("<I",bytes(self.u.mem_read(0x400bb0cc,4)))[0]==3
   if patched:assert bytes(self.u.mem_read(BASE,RESERVE))==APPENDED
   BOOT_REPORT["patched" if patched else "stock"]={"native_startup_copy_and_BSS_passed":True,"native_heap_constructor_passed":True,"pool1_start":hex(descriptor[0]),"pool1_end":hex(descriptor[1]),"reservation_survives_heap_setup":patched,"payload_loaded_from_final_FMAIN":patched}
   BOOT_CACHE[patched]=[(addr,bytes(self.u.mem_read(addr,n))) for addr,n in [(0x10000000,0x40000),(0x40000000,0x800000)]]
  self.u.mem_write(0x40073604,b"\1");self.u.mem_write(0x400bb3d4,b"\1");self.u.mem_write(0x400bb3a0,b"\0")
  usb=self.client();self.attach_usb(usb);self.mic(1)
  self.voices.clear();self.events.clear()
 def invalid(self,u,access,address,size,value,data):
  print("UNMAPPED",hex(u.reg_read(UC_ARM_REG_PC)),hex(address),"r0-r3",[hex(u.reg_read(r)) for r in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]])
  return False
 def call(self,addr,*args):
  u=self.u;u.reg_write(UC_ARM_REG_SP,0x5000f000);u.reg_write(UC_ARM_REG_LR,0x400f0001)
  for r,v in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],args):u.reg_write(r,v)
  u.emu_start(addr|1,0,count=2000000)
  assert u.reg_read(UC_ARM_REG_PC)==0x400f0000,hex(u.reg_read(UC_ARM_REG_PC))
  return u.reg_read(UC_ARM_REG_R0)
 def hook(self,u,addr,size,data):
  if self.booting and addr==0x100001d4:u.emu_stop();return
  # Let the real original allocator execute. Only fault injection returns zero.
  if addr==0x40066ed4:
   if self.fail_alloc:u.reg_write(UC_ARM_REG_R0,0);u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
   return
  r=[u.reg_read(x) for x in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]]
  ret=None
  if addr==0x400411a4:u.mem_write(r[0],bytes([self.mode]));ret=1
  elif addr==0x40043194:u.mem_write(r[0],bytes([self.disabled]));ret=1
  elif addr==0x4001a1f8:ret=self.busy
  elif addr==0x40033f68:self.reports.append(r[:3]);ret=1
  elif addr==0x4001a794:self.notifications.append(r[0]);ret=1
  elif addr==0x4003ce6c:self.app_events.append(r[:2]);ret=1
  elif addr==0x4001a980:self.voices.append(bytes(u.mem_read(r[0],80)).split(b"\0")[0].decode("ascii"));ret=1
  if ret is not None:
   u.reg_write(UC_ARM_REG_R0,ret);u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR));return
  super().hook(u,addr,size,data)
 def press(self,key=6,event=0):
  n=[len(self.voices),len(self.reports),len(self.notifications),len(self.app_events)]
  regs=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
  vals=[0x10101010+i*0x01010101 for i in range(len(regs))]
  for reg,v in zip(regs,vals):self.u.reg_write(reg,v)
  status=self.call(0x4001a258,key,event)
  assert [self.u.reg_read(x) for x in regs]==vals and self.u.reg_read(UC_ARM_REG_SP)==0x5000f000
  return {"status":status,"state":self.u.mem_read(STATE,1)[0],"voice":self.voices[n[0]:],"reports":self.reports[n[1]:],"notifications":self.notifications[n[2]:],"app_events":self.app_events[n[3]:],"controls":self.snapshot(),"press_flag":self.u.mem_read(0x400bb3a0,1)[0]}
 def code_intact(self):
  assert bytes(self.u.mem_read(BASE,RESERVE-4))==APPENDED[:-4]
def expected(state):
 return {1:{"input108":1,"output206":0},2:{"input108":0,"output206":0},0:{"input108":1,"output206":1}}[state]
checks={};cycles=[]
for mode in [3,6,7]:
 m=CandidateMachine();m.mode=mode
 for i in range(9):
  v=m.press();state=[1,2,0][i%3]
  assert v["status"]==1 and v["state"]==state and v["controls"]==expected(state),v
  assert v["voice"]==(["@micunmute"] if state else ["@micmute"]),v
  assert v["reports"]==[[9 if state else 8,0,0]] and v["notifications"]==[5,5] and v["press_flag"]==0,v
  m.sync();assert m.snapshot()==expected(state);m.code_intact()
  v["mode"]=mode;v["after_USB_sync"]=m.snapshot();cycles.append(v)
checks["27_hardware_presses_from_built_image"]=cycles
blocked=[]
cases=[{"name":"app_mode_"+str(i),"mode":i} for i in [0,1,2,4,5,8]]
cases += [{"name":"busy","busy":1},{"name":"mic_absent","present":0},{"name":"mic_disabled","disabled":1},{"name":"flag_2","flag":2},{"name":"flag_255","flag":255}]
cases += [{"name":"event_"+str(i),"event":i} for i in [1,2,3,4]]
cases += [{"name":"unknown_key","key":7}]
for case in cases:
 out=[]
 for patched in [False,True]:
  m=CandidateMachine(patched);m.mode=case.get("mode",3);m.disabled=case.get("disabled",0);m.busy=case.get("busy",0)
  m.u.mem_write(0x400bb3d4,bytes([case.get("present",1)]));m.u.mem_write(0x400bb3a0,bytes([case.get("flag",0)]))
  v=m.press(case.get("key",6),case.get("event",0))
  if patched:assert v["state"]==0;m.code_intact()
  v.pop("state");out.append(v)
 assert out[0]==out[1],(case,out)
 blocked.append({"case":case,"matches_stock":True})
checks["16_blocked_or_other_cases_equal_stock"]=blocked
m=CandidateMachine();m.u.mem_write(0x400bb3a0,b"\1");v=m.press();assert v["state"]==1 and v["press_flag"]==0
checks["permitted_flag1"]=v
m=CandidateMachine()
for _ in range(3):m.press()
other=m.client();m.input(other,0);m.output(other,0);m.sync();assert m.snapshot()==expected(0)
checks["native_OFF_survives_other_owner_and_sync"]=m.snapshot()
m=CandidateMachine();m.press();m.press();m.call(0x4001b214,1,0);v=m.press();assert v["state"]==1 and v["controls"]==expected(1)
checks["external_native_mute_restarts_cycle"]=v
m=CandidateMachine();m.call(0x4001b214,0,0);m.fail_alloc=True
v=m.press();assert v["status"]==0 and v["state"]==0 and v["controls"]==expected(0) and v["voice"]==["@micmute"]
checks["allocator_failure_from_unmuted"]=v
m=CandidateMachine();m.u.mem_write(STATE,b"\xff");v=m.press();assert v["state"]==0 and v["controls"]==expected(0)
checks["invalid_state_OFF"]=v
m=CandidateMachine();allocs=[]
for i in range(64):
 ptr=m.call(0x100008a4,1,32+i*4) # Thumb target of the ARM import veneer
 assert BASE+RESERVE<=ptr<0x405503e0
 allocs.append(ptr)
m.code_intact();assert bytes(m.u.mem_read(STATE,4))==bytes(4)
checks["64_real_pool1_allocations_do_not_touch_reserved_payload"]={"min":hex(min(allocs)),"max":hex(max(allocs)),"count":len(allocs)}
assert sha((R/"candidate/FMAIN.experimental.bin").read_bytes())==manifest["modified_FMAIN_sha256"]
checks["tested_bytes_match_built_file"]=True
out={"canonical_truth":False,"status":"BUILT_IMAGE_PASSES_OFFLINE_STARTUP_HEAP_AND_BUTTON_CHECKS_NOT_HARDWARE_VALIDATED","modified_FMAIN_sha256":sha(MOD),"startup":BOOT_REPORT,"checks":checks,"executed_original":["ARM startup copy and BSS zero loops","all three heap pool constructors and real pool1 allocator","stock key handler/guard routing/native presence getter","generic native setter/wrappers/mute owner manager","voice selector/USB sync"],"stubs":["app-mode getter","disabled-mode getter","busy-guard result","final audio backend","event/USB notifications","gain backend","voice output queue","interrupt-controller mask register is an isolated memory model; no real IRQ scheduling","allocator failure is explicit injected fault only"],"limits":manifest["not_proven"],"device_commands_sent":False}
(R/"candidate/verification.json").write_text(json.dumps(out,indent=2))
print(json.dumps({"status":out["status"],"startup":BOOT_REPORT,"presses":len(cycles),"stock_comparison_cases":len(blocked),"allocator_test":checks["64_real_pool1_allocations_do_not_touch_reserved_payload"],"modified_FMAIN_sha256":sha(MOD)},indent=2))
