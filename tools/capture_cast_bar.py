"""Read only the pinned RoF2 cast timer fields; never inject or write process memory.

Run while the affected Nightcap client is open. Cast an ordinary non-DoT spell
while capture runs. File duration is a reference, not a read of native spell RAM.
"""
import argparse
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
from pathlib import Path
import time

EXPECTED_SHA256='2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e'
IMAGE_BASE=0x400000
PLAYER_RVA=0xdd2630-IMAGE_BASE
CLOCK_RVA=0xdd2660-IMAGE_BASE

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--pid',type=int,required=True)
 p.add_argument('--exe',type=Path,default=Path('E:/Nightcap/eqgame.exe'))
 p.add_argument('--seconds',type=int,default=30,choices=range(5,61),metavar='5..60')
 p.add_argument('--output',type=Path,required=True)
 a=p.parse_args()
 exe=a.exe.resolve(strict=True)
 if hashlib.sha256(exe.read_bytes()).hexdigest()!=EXPECTED_SHA256: raise ValueError('Unrecognized client executable')
 kernel=c.WinDLL('kernel32',use_last_error=True)
 kernel.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD]; kernel.OpenProcess.restype=w.HANDLE
 kernel.CloseHandle.argtypes=[w.HANDLE]; kernel.CloseHandle.restype=w.BOOL
 kernel.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,c.POINTER(w.DWORD)]; kernel.QueryFullProcessImageNameW.restype=w.BOOL
 kernel.ReadProcessMemory.argtypes=[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)]; kernel.ReadProcessMemory.restype=w.BOOL
 kernel.CreateToolhelp32Snapshot.argtypes=[w.DWORD,w.DWORD]; kernel.CreateToolhelp32Snapshot.restype=w.HANDLE
 class Module(c.Structure):
  _fields_=[('size',w.DWORD),('module_id',w.DWORD),('pid',w.DWORD),('global_refs',w.DWORD),('process_refs',w.DWORD),
   ('base',c.c_void_p),('image_size',w.DWORD),('handle',w.HMODULE),('name',w.WCHAR*256),('path',w.WCHAR*260)]
 kernel.Module32FirstW.argtypes=[w.HANDLE,c.POINTER(Module)]; kernel.Module32FirstW.restype=w.BOOL
 handle=kernel.OpenProcess(0x1000|0x10,False,a.pid) # QUERY_LIMITED_INFORMATION | VM_READ only
 if not handle: raise c.WinError(c.get_last_error())
 try:
  image=c.create_unicode_buffer(32768); length=w.DWORD(len(image))
  if not kernel.QueryFullProcessImageNameW(handle,0,image,c.byref(length)): raise c.WinError(c.get_last_error())
  if Path(image.value).resolve()!=exe: raise ValueError('PID is not the specified Nightcap executable')
  snapshot=kernel.CreateToolhelp32Snapshot(0x08|0x10,a.pid)
  if snapshot==c.c_void_p(-1).value: raise c.WinError(c.get_last_error())
  try:
   module=Module(); module.size=c.sizeof(module)
   if not kernel.Module32FirstW(snapshot,c.byref(module)): raise c.WinError(c.get_last_error())
   if Path(module.path).resolve()!=exe: raise ValueError('Unexpected main module')
   base=module.base
  finally: kernel.CloseHandle(snapshot)
  def u32(address):
   value=w.DWORD(); count=c.c_size_t()
   if not kernel.ReadProcessMemory(handle,address,c.byref(value),4,c.byref(count)) or count.value!=4:
    raise c.WinError(c.get_last_error())
   return value.value
  durations={}
  for line in (exe.parent/'spells_us.txt').read_text(encoding='latin1').splitlines():
   fields=line.split('^')
   if len(fields)==237: durations[int(fields[0])]=int(fields[13])
  a.output.parent.mkdir(parents=True,exist_ok=True)
  with a.output.open('x',encoding='utf-8') as stream:
   stream.write(json.dumps(dict(type='metadata',client_sha256=EXPECTED_SHA256,interval_ms=100,
    scope='deadline, spell ID and native clock only; spell duration reference from packaged file'))+'\n')
   started=time.monotonic()
   print('Read-only capture running; cast one ordinary non-instant spell now.',flush=True)
   while time.monotonic()-started<a.seconds:
    player=u32(base+PLAYER_RVA); clock=u32(base+CLOCK_RVA)
    if player and clock:
     deadline=u32(player+0x444); spell=u32(player+0x448); now=u32(clock+0x154)
     remaining=c.c_int32((deadline-now)&0xffffffff).value
     duration=durations.get(spell)
     row=dict(elapsed_ms=round((time.monotonic()-started)*1000),deadline=deadline,spell_id=spell,clock=now,
      remaining_ms=remaining,file_cast_ms=duration,native_timer_expired=bool(deadline and remaining<0))
     if deadline and remaining>=0 and duration and duration>0: row['arithmetic_reference_per_mille']=max(0,min(1000,remaining*1000//duration))
     stream.write(json.dumps(row)+'\n'); stream.flush()
    time.sleep(0.1)
  print('Saved '+str(a.output))
 finally: kernel.CloseHandle(handle)

if __name__=='__main__': main()
