const $=s=>document.querySelector(s);
const state={java:[],bedrock:[]};
const status=m=>{const el=$("#status");if(el)el.textContent=m;};
const reportError=(kind,error)=>{
  const message=error&&error.message?error.message:String(error);
  status("Lỗi "+kind+": "+message+" — mở Chẩn đoán / sửa lỗi để xem hướng dẫn.");
  console.error("[ModMerge]",kind,error);
};
window.addEventListener("error",e=>reportError("JavaScript",e.error||e.message));
window.addEventListener("unhandledrejection",e=>reportError("Promise",e.reason));
const uuid=()=>"xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g,c=>{const r=Math.random()*16|0;return(c==="x"?r:(r&3|8)).toString(16)});
function esc(s){return s.replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function setBusy(button,busy){button.disabled=busy;}
document.querySelectorAll(".tab").forEach(b=>b.addEventListener("click",()=>{document.querySelectorAll(".tab").forEach(x=>x.classList.toggle("active",x===b));document.querySelectorAll(".panel").forEach(x=>x.classList.toggle("active",x.id==="panel-"+b.dataset.tab))}));
function render(k){const el=$("#"+k+"-list"),files=state[k];el.innerHTML=files.length?files.map((f,i)=>'<div class="file-row"><span>'+esc(f.name)+'</span><small>'+(f.size/1048576).toFixed(2)+' MB · '+(i+1)+'</small></div>').join(""):'<p class="empty">Chưa có file nào được chọn.</p>';$("#"+k+"-build").disabled=files.length===0||(k==="bedrock"&&files.length<2);}
function add(k,files){const valid=files.filter(f=>k==="java"?f.name.toLowerCase().endsWith(".jar"):/\.(mcpack|mcaddon|zip)$/i.test(f.name));for(const f of valid)if(!state[k].some(x=>x.name===f.name&&x.size===f.size))state[k].push(f);render(k);status("Đã thêm "+valid.length+" file vào danh sách "+k+".");}
["java","bedrock"].forEach(k=>{const input=$("#"+k+"-files"),drop=$("#"+k+"-drop");input.addEventListener("change",()=>add(k,[...input.files]));["dragenter","dragover"].forEach(e=>drop.addEventListener(e,x=>{x.preventDefault();drop.classList.add("drag")}));["dragleave","drop"].forEach(e=>drop.addEventListener(e,x=>{x.preventDefault();drop.classList.remove("drag");if(e==="drop")add(k,[...x.dataTransfer.files])}));});
async function readZip(file){if(!window.JSZip)throw Error("JSZip chưa tải được. Kiểm tra mạng hoặc mở diagnostics.html.");return JSZip.loadAsync(file);}
async function identify(file){const z=await readZip(file),n=Object.keys(z.files),l=[];if(n.includes("fabric.mod.json"))l.push("Fabric");if(n.includes("quilt.mod.json"))l.push("Quilt");if(n.includes("META-INF/mods.toml")||n.includes("mcmod.info"))l.push("Forge");if(n.includes("META-INF/neoforge.mods.toml"))l.push("NeoForge");return{file,loaders:l};}
function download(blob,name){const u=URL.createObjectURL(blob),a=document.createElement("a");a.href=u;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),2000);}
$("#java-build").addEventListener("click",async()=>{const b=$("#java-build");setBusy(b,true);try{const loader=$("#java-loader").value,items=[];for(const f of state.java)items.push(await identify(f));const bad=items.filter(x=>!x.loaders.includes(loader));if(bad.length)throw Error("Không nhận diện được loader "+loader+" cho: "+bad.map(x=>x.file.name).join(", "));const z=new JSZip();items.forEach(x=>z.file("mods/"+x.file.name,x.file));z.file("README.txt","ModMerge Studio bundle. JAR files remain separate in mods/. This is not a merged Java bytecode JAR.");z.file("modmerge-report.json",JSON.stringify({loader,mods:items.map(x=>({name:x.file.name,loaders:x.loaders}))},null,2));download(await z.generateAsync({type:"blob"}),"modmerge-java-bundle.zip");status("Đã đóng gói "+items.length+" mod. Giải nén thư mục mods/ vào profile Minecraft phù hợp.");}catch(e){reportError("đóng gói Java",e);}finally{setBusy(b,false);}});
$("#bedrock-build").addEventListener("click",async()=>{const b=$("#bedrock-build");setBusy(b,true);try{if(!window.ModMergeBedrock)throw Error("Không tải được bedrock-merger.js. Mở trang Chẩn đoán.");const result=await window.ModMergeBedrock.merge(state.bedrock,window.JSZip);download(result.blob,"modmerge-bedrock-"+result.kind+"-merged.mcpack");status("Đã gộp "+result.packCount+" pack "+result.kind+"; "+result.moduleCount+" module, "+result.fileCount+" file, giữ "+result.dependencies+" dependency ngoài. Hãy kiểm thử trong world mới.");}catch(e){reportError("gộp Bedrock",e);}finally{setBusy(b,false);}});
if(!window.JSZip)reportError("khởi động","JSZip không tồn tại. Mở diagnostics.html.");
else status("Sẵn sàng. File của bạn được xử lý cục bộ trong trình duyệt.");
