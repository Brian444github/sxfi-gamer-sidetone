from pathlib import Path
import sys,struct,json,hashlib
import arm207 as a
R=a.ROOT
from unicorn import *
from unicorn.arm_const import *
SHA="7bcca20699b7bfe746923fd1791a4cc36a5021f0389ae9ce65c56dfd78bec761"
assert hashlib.sha256(a.b).hexdigest()==SHA
class Machine:
 def __init__(self):
  self.u=Uc(UC_ARCH_ARM,UC_MODE_THUMB)
  for p,n in [(0x10000000,0x20000),(0x40000000,0x100000),(0x50000000,0x40000)]:self.u.mem_map(p,n)
  for o,d,n in a.maps:self.u.mem_write(d,a.b[o:o+n])
  self.heap=0x50020000;self.events=[];self.levels={};self.fail_alloc=False
  self.u.hook_add(UC_HOOK_CODE,self.hook)
 def hook(self,u,addr,size,data):
  if addr==0x400f0000:u.emu_stop();return
  r=[u.reg_read(x) for x in [UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]]
  ret=None
  if addr==0x40066ed4:
   n=r[0]*r[1]
   assert 0<n<=4096
   ret=0 if self.fail_alloc else self.heap
   if ret:self.heap+=(n+7)&~7;assert self.heap<0x50040000;u.mem_write(ret,bytes(n))
  elif addr in [0x4004dbb8,0x4004ddc8]:
   direction="input" if addr==0x4004dbb8 else "output"
   self.levels[(direction,r[0])]=r[1]
   self.events.append({"backend":direction,"channel":r[0],"mute":r[1]})
   ret=1
  elif addr in [0x4004dd3c,0x40065edc]:ret=1
  elif addr==0x40041930:
   u.mem_write(0x400c466c+8,bytes([int(bool(r[0]))]));ret=1
  if ret is not None:
   u.reg_write(UC_ARM_REG_R0,ret);u.reg_write(UC_ARM_REG_PC,u.reg_read(UC_ARM_REG_LR))
 def call(self,addr,*args):
  u=self.u;u.reg_write(UC_ARM_REG_SP,0x5000f000);u.reg_write(UC_ARM_REG_LR,0x400f0001)
  for r,v in zip([UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3],args):u.reg_write(r,v)
  u.emu_start(addr|1,0,count=100000)
  assert u.reg_read(UC_ARM_REG_PC)==0x400f0000,hex(u.reg_read(UC_ARM_REG_PC))
  return u.reg_read(UC_ARM_REG_R0)
 def client(self):return self.call(0x4004d88c)
 def attach_usb(self,client):self.u.mem_write(0x400c468a,struct.pack("<H",client))
 def input(self,c,mute):return self.call(0x4004d904,c,108,mute)
 def output(self,c,mute):return self.call(0x4004d8fa,c,206,mute)
 def sync(self):return self.call(0x40041bac)
 def mic(self,mute):return self.call(0x4001a8b8,mute)
 def snapshot(self):return {"input108":self.levels.get(("input",108)),"output206":self.levels.get(("output",206))}
if __name__=="__main__":
 runs={}
 m=Machine();usb=m.client();assert usb==1;m.attach_usb(usb)
 m.u.mem_write(0x4001a8f0,bytes.fromhex("0122"))
 m.mic(0);before=m.snapshot();m.sync();after=m.snapshot()
 assert before=={"input108":1,"output206":0} and after=={"input108":0,"output206":0}
 runs["single_instruction_overlay_reset_by_USB_sync"]={"before":before,"after":after,"events":m.events}
 m=Machine();usb=m.client();monitor=m.client();assert (usb,monitor)==(1,2);m.attach_usb(usb)
 m.input(monitor,1);m.mic(0);before=m.snapshot()
 for _ in range(3):m.sync()
 after=m.snapshot();assert before==after=={"input108":1,"output206":0}
 runs["independent_monitor_owner_survives_USB_sync"]={"before":before,"after":after,"events":m.events[:]}
 m.input(monitor,0);assert m.snapshot()=={"input108":0,"output206":0}
 m.mic(1);m.input(monitor,0);off=m.snapshot()
 host=m.client();m.input(host,0);m.output(host,0)
 assert off==m.snapshot()=={"input108":1,"output206":1}
 runs["native_mute_owner_survives_other_owner_unmute"]={"before":off,"after":m.snapshot(),"events":m.events}
 out={"canonical_truth":False,"scope":"offline firmware control-flow emulation, not an acoustic test","image_sha256":SHA,"method":"Execute actual vendor mute-manager, owner registration, linked-list aggregation, mic routine and USB synchronization; stub allocator, final audio backend, event dispatch, gain writes and USB cache notification","runs":runs,"not_proven":["input108 is exclusive sidetone","USB voice recording remains audible","hardware button three-state handler installed","actual host callback paths and all modes","firmware deploy/recovery"],"device_commands_sent":False,"modified_firmware_written":False}
 (R/"mute-owner-emulation.json").write_text(json.dumps(out,indent=2))
 print(json.dumps({k:{x:v for x,v in z.items() if x!="events"} for k,z in runs.items()},indent=2))
 print("CHECKS_PASSED: real vendor owner aggregation prevents USB synchronization from clearing a separate mute owner.")
