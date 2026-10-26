"""Prove ELF64 runtime sections/program headers unchanged after debug stripping."""
import hashlib,json,struct,sys
from pathlib import Path

def identity(path):
 data=Path(path).read_bytes()
 assert data[:6]==b'\x7fELF\x02\x01','Requires little-endian ELF64'
 h=struct.unpack_from('<16sHHIQQQIHHHHHH',data)
 assert h[8]==64 and h[9]==56 and h[11]==64 and 0<h[10]<128 and 0<h[12]<65535
 assert h[5]+h[9]*h[10]<=len(data) and h[6]+h[11]*h[12]<=len(data)
 programs=[struct.unpack_from('<IIQQQQQQ',data,h[5]+i*56) for i in range(h[10])]
 sections=[struct.unpack_from('<IIQQQQIIQQ',data,h[6]+i*64) for i in range(h[12])]
 assert h[13]<len(sections)
 strings=sections[h[13]];assert strings[4]+strings[5]<=len(data)
 names=data[strings[4]:strings[4]+strings[5]];allocated={}
 for s in sections:
  if not s[2]&2:continue
  assert s[0]<len(names) and b'\0' in names[s[0]:]
  name=names[s[0]:].split(b'\0',1)[0].decode('ascii');assert name not in allocated
  digest=None
  if s[1]!=8:
   assert s[4]+s[5]<=len(data);digest=hashlib.sha256(data[s[4]:s[4]+s[5]]).hexdigest()
  allocated[name]=[s[1],s[2],s[3],s[4],s[5],s[8],s[9],digest]
 assert allocated and any(p[0]==1 for p in programs)
 # Hash bytes actually mapped by the loader, including padding outside sections.
 # strip-debug may only relocate/recount the non-runtime section table in ELF header.
 normalized=bytearray(data)
 for offset,size in ((40,8),(60,2),(62,2)):normalized[offset:offset+size]=bytes(size)
 loads=[]
 for p in programs:
  if p[0]!=1:continue
  offset,size=p[2],p[5]
  assert offset+size<=len(data) and size<=p[6]
  loads.append(hashlib.sha256(normalized[offset:offset+size]).hexdigest())
 return {'elf_ident':data[:16].hex(),'load_bytes':loads,'header':[h[i] for i in (1,2,3,4,5,7,8,9,10)],'program_headers':programs,'allocated_sections':allocated}

def verify(before,after):
 original=identity(before);candidate=identity(after)
 assert original==candidate,'Runtime section, entry, mapping or protection changed'
 return {'status':'PASS','allocated_sections':len(original['allocated_sections']),'program_headers':len(original['program_headers']),
 'original_sha256':hashlib.sha256(Path(before).read_bytes()).hexdigest(),'sha256':hashlib.sha256(Path(after).read_bytes()).hexdigest(),
 'original_size':Path(before).stat().st_size,'size':Path(after).stat().st_size}
if __name__=='__main__':print(json.dumps(verify(sys.argv[1],sys.argv[2])))
