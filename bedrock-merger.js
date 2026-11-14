(function (root) {
"use strict";
const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const ALLOWED=new Set(["resources","data","script"]);
const fail=m=>{throw new Error(m);};
const makeUuid=()=>"xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g,c=>{const r=Math.random()*16|0;return(c==="x"?r:(r&3|8)).toString(16);});
function validVersion(v,label){if(!Array.isArray(v)||v.length!==3||v.some(n=>!Number.isInteger(n)||n<0))fail(label+" phải là [major, minor, patch].");return v;}
const cmp=(a,b)=>{for(let i=0;i<3;i++)if(a[i]!==b[i])return a[i]-b[i];return 0;};
function classifyManifest(m,name){
 if(!m||!m.header||!Array.isArray(m.modules)||!m.modules.length)fail(name+": manifest thiếu header hoặc modules.");
 if(!UUID_RE.test(m.header.uuid||""))fail(name+": header.uuid không hợp lệ.");
 validVersion(m.header.version,name+" header.version");
 const kinds=new Set(),seen=new Set();
 for(const mod of m.modules){
  if(!mod||!UUID_RE.test(mod.uuid||""))fail(name+": module.uuid không hợp lệ.");
  if(seen.has(mod.uuid.toLowerCase()))fail(name+": UUID module bị lặp."); seen.add(mod.uuid.toLowerCase());
  if(!ALLOWED.has(mod.type))fail(name+": module type không hỗ trợ: "+mod.type);
  validVersion(mod.version,name+" module.version");
  kinds.add(mod.type==="resources"?"resource":"behavior");
 }
 if(kinds.size!==1)fail(name+": pack chứa cả Resource và Behavior module; cần tách pack trước.");
 if(m.format_version!==2)fail(name+": chỉ hỗ trợ manifest format_version 2.");
 if(m.dependencies!==undefined&&!Array.isArray(m.dependencies))fail(name+": dependencies phải là mảng.");
 return [...kinds][0];
}
function normalizePath(path){
 const n=String(path).replace(/\\/g,"/");
 if(!n||n.startsWith("/")||/^[a-z]:/i.test(n)||n.split("/").some(p=>p===".."||p==="."||p===""))fail("Đường dẫn archive không an toàn: "+path);
 return n;
}
function mergeManifestMetadata(packs,createUuid=makeUuid){
 const kind=packs[0].kind;if(packs.some(p=>p.kind!==kind))fail("Không thể trộn Resource Pack với Behavior Pack.");
 const headerIds=new Set(packs.map(p=>p.manifest.header.uuid.toLowerCase())),moduleIds=new Map();
 for(const p of packs)for(const m of p.manifest.modules)moduleIds.set(m.uuid.toLowerCase(),createUuid());
 const deps=new Map();
 for(const p of packs)for(const d of p.manifest.dependencies||[]){
  if(!d||!UUID_RE.test(d.uuid||""))fail(p.file.name+": dependency UUID không hợp lệ.");
  if(headerIds.has(d.uuid.toLowerCase()))continue;
  validVersion(d.version,p.file.name+" dependency.version");
  const k=d.uuid.toLowerCase(),old=deps.get(k);
  if(old&&JSON.stringify(old.version)!==JSON.stringify(d.version))fail("Dependency ngoài bị yêu cầu hai phiên bản khác nhau: "+d.uuid);
  deps.set(k,{uuid:d.uuid,version:d.version});
 }
 const modules=[];
 for(const p of packs)for(const original of p.manifest.modules){
  const mod={...original,uuid:moduleIds.get(original.uuid.toLowerCase())};
  if(Array.isArray(original.dependencies))mod.dependencies=original.dependencies.map(d=>{
   if(typeof d==="string")return moduleIds.get(d.toLowerCase())||d;
   if(d&&typeof d==="object"&&d.uuid&&moduleIds.has(d.uuid.toLowerCase()))return {...d,uuid:moduleIds.get(d.uuid.toLowerCase())};
   return d;
  });
  modules.push(mod);
 }
 const manifests=packs.map(p=>p.manifest),first=manifests[0];
 const header={...first.header,uuid:createUuid(),name:"Merged "+(first.header.name||"Bedrock Pack")};
 const engines=manifests.map(m=>m.header.min_engine_version).filter(Array.isArray);
 if(engines.length){engines.forEach(v=>validVersion(v,"header.min_engine_version"));header.min_engine_version=engines.reduce((a,b)=>cmp(a,b)>=0?a:b);}
 const result={...first,header,modules,dependencies:[...deps.values()]};
 const caps=[...new Set(manifests.flatMap(m=>m.capabilities||[]))];if(caps.length)result.capabilities=caps;
 const subpacks=manifests.map(m=>JSON.stringify(m.subpacks||[]));if(subpacks.some(x=>x!==subpacks[0]))fail("Các pack có cấu hình subpacks khác nhau; không thể gộp an toàn.");
 return result;
}
async function merge(files,JSZip){
 if(!JSZip)fail("JSZip chưa được tải.");if(!files||files.length<2)fail("Cần ít nhất hai pack để gộp.");
 const packs=[];
 for(const file of files){
  let zip;try{zip=await JSZip.loadAsync(file);}catch(e){fail(file.name+": file ZIP/MCPACK không đọc được ("+e.message+").");}
  const entry=zip.file("manifest.json");if(!entry)fail(file.name+": thiếu manifest.json ở thư mục gốc.");
  let manifest;try{manifest=JSON.parse(await entry.async("string"));}catch(e){fail(file.name+": manifest.json không hợp lệ ("+e.message+").");}
  packs.push({file,zip,manifest,kind:classifyManifest(manifest,file.name)});
 }
 const manifest=mergeManifestMetadata(packs),out=new JSZip(),content=new Map();
 for(const p of packs)for(const [raw,entry] of Object.entries(p.zip.files)){
  if(entry.dir||raw==="manifest.json")continue;
  const name=normalizePath(raw),data=await entry.async("uint8array");
  if(name.toLowerCase().endsWith(".json")){try{JSON.parse(new TextDecoder().decode(data));}catch(e){fail(p.file.name+": JSON không hợp lệ tại "+name+".");}}
  const prev=content.get(name);
  if(prev){if(prev.length!==data.length||prev.some((v,i)=>v!==data[i]))fail("Xung đột nội dung tại "+name+". Không tự ghi đè file.");}
  else content.set(name,data);
 }
 for(const [name,data] of content)out.file(name,data);
 out.file("manifest.json",JSON.stringify(manifest,null,2));
 return {blob:await out.generateAsync({type:"blob"}),kind:packs[0].kind,packCount:packs.length,fileCount:content.size,dependencies:manifest.dependencies.length,moduleCount:manifest.modules.length};
}
root.ModMergeBedrock={merge,_test:{classifyManifest,normalizePath,mergeManifestMetadata}};
if(typeof module!=="undefined"&&module.exports)module.exports=root.ModMergeBedrock;
})(typeof globalThis!=="undefined"?globalThis:window);
