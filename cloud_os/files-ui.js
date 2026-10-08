(()=>{
const FILE_RENDER_BATCH=120;
window.__cloudOsFileRenderBatch=FILE_RENDER_BATCH;
let generation=0;
const H=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const joinPath=(base,name)=>(base?base+'/':'')+name;
const isViewer=()=>typeof me!=='undefined'&&me?.role==='viewer';
function fmtSize(n){n=Number(n)||0;if(n<1024)return n+' B';if(n<1048576)return(n/1024).toFixed(1)+' KB';if(n<1073741824)return(n/1048576).toFixed(1)+' MB';return(n/1073741824).toFixed(2)+' GB'}
function rowHtml(path,x){let rel=joinPath(path,x.name),viewer=isViewer();return `<div class="row filePagedRow"><div class="file-name"><span>${x.directory?'📁':'📄'}</span><button ${x.directory?`data-dir="${H(rel)}"`:`data-edit="${H(rel)}"`}>${H(x.name)}</button>${x.directory?'':`<span class="small">${H(fmtSize(x.size))}</span>`}</div><div class="row-actions">${!x.directory?`<a class="btn" href="/api/download?path=${encodeURIComponent(rel)}">Download</a>`:''}${viewer?'':`<button class="btn" data-ren="${H(rel)}" data-name="${H(x.name)}">Rename</button><button class="btn danger" data-del="${H(rel)}">Delete</button>`}</div></div>`}
function afterChunk(){requestAnimationFrame(()=>{document.dispatchEvent(new CustomEvent('cloudos:files-chunk'));if(isViewer())document.querySelectorAll('#fileRows [data-share]').forEach(x=>x.remove())})}
window.files=async function(path=''){
 const mine=++generation;let offset=0,total=0,loading=false;
 let first=await api(`/api/files/page?path=${encodeURIComponent(path)}&offset=0&limit=${FILE_RENDER_BATCH}`);if(mine!==generation)return;
 total=Number(first.total)||0;
 let parts=path?path.split('/').filter(Boolean):[],crumbs='<button data-dir="">Storage</button>'+parts.map((x,i)=>` / <button data-dir="${H(parts.slice(0,i+1).join('/'))}">${H(x)}</button>`).join('');
 q('#content').innerHTML=`<div class="card glass"><div class="sectionbar"><div><h3 style="margin:0">Files</h3><div class="small" id="fileCount">${total} item${total===1?'':'s'}</div></div><button id="refreshFiles" class="btn">Refresh</button></div><div class="toolbar">${isViewer()?'':`<button id="newFolder" class="btn primary">New folder</button><button id="newFile" class="btn">New file</button><button id="uploadBtn" class="btn">Upload file</button><input id="uploadFile" type="file" hidden>`}</div><div class="crumb">${crumbs}</div><div class="list" id="fileRows"></div><div id="fileEmpty" class="empty hidden">This folder is empty. Create a file, folder, or upload.</div><div style="display:flex;justify-content:center;margin-top:12px"><button id="loadMoreFiles" class="btn hidden">Load more</button></div></div>`;
 const list=q('#fileRows'),empty=q('#fileEmpty'),more=q('#loadMoreFiles');
 function append(items){if(mine!==generation)return;if(items.length)list.insertAdjacentHTML('beforeend',items.map(x=>rowHtml(path,x)).join(''));offset+=items.length;empty.classList.toggle('hidden',total!==0);more.classList.toggle('hidden',offset>=total);more.textContent=offset<total?`Load more · ${offset}/${total}`:'All files loaded';afterChunk()}
 append(first.items||[]);
 async function loadMore(){if(loading||offset>=total)return;loading=true;more.disabled=true;more.textContent='Loading…';try{let d=await api(`/api/files/page?path=${encodeURIComponent(path)}&offset=${offset}&limit=${FILE_RENDER_BATCH}`);if(mine!==generation)return;total=Number(d.total)||total;append(d.items||[])}catch(e){await notice('Files',`${e.code||'FILE'}: ${e.message||'Could not load files'}`)}finally{loading=false;if(more){more.disabled=false;if(offset<total)more.textContent=`Load more · ${offset}/${total}`}}}
 more.onclick=loadMore;
 q('#refreshFiles').onclick=()=>window.files(path);
 document.querySelectorAll('.crumb [data-dir]').forEach(b=>b.onclick=()=>window.files(b.dataset.dir));
 list.onclick=async e=>{
  let b=e.target.closest('[data-dir],[data-edit],[data-ren],[data-del]');if(!b)return;
  if(b.dataset.dir!==undefined){await window.files(b.dataset.dir);return}
  if(b.dataset.edit!==undefined){if(isViewer()){window.open('/preview?path='+encodeURIComponent(b.dataset.edit),'_blank','noopener');return}try{let d=await api('/api/file/content?path='+encodeURIComponent(b.dataset.edit));let pending=modal('Edit '+b.dataset.edit,'<textarea id="fileContent"></textarea>');let ta=q('#fileContent');if(ta)ta.value=d.content||'';let ok=await pending;if(!ok)return;await api('/api/file/content',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:b.dataset.edit,content:q('#fileContent').value})});await window.files(path)}catch(err){await notice('File editor',`${err.code||'FILE'}: ${err.message||'Could not edit file'}`)}return}
  if(b.dataset.ren!==undefined){let pending=modal('Rename',`<input id="renameValue" value="${H(b.dataset.name)}" placeholder="New name">`);let ok=await pending;if(!ok)return;let n=q('#renameValue').value.trim();if(!n)return;try{await api('/api/files/rename',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:b.dataset.ren,new_name:n})});await window.files(path)}catch(err){await notice('Rename failed',`${err.code||'FILE'}: ${err.message||'Could not rename item'}`)}return}
  if(b.dataset.del!==undefined){let ok=await modal('Delete item',`<p>Delete <b>${H(b.dataset.del)}</b>?</p>`,'Delete');if(!ok)return;try{await api('/api/files?path='+encodeURIComponent(b.dataset.del),{method:'DELETE'});await window.files(path)}catch(err){await notice('Delete failed',`${err.code||'FILE'}: ${err.message||'Could not delete item'}`)}}
 };
 if(!isViewer()){
  q('#newFolder').onclick=async()=>{let pending=modal('Create folder','<input id="folderName" placeholder="Folder name">','Create');let ok=await pending;if(!ok)return;let n=q('#folderName').value.trim();if(!n)return;try{await api('/api/folder',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:joinPath(path,n)})});await window.files(path)}catch(e){await notice('Create folder',`${e.code||'FILE'}: ${e.message||'Could not create folder'}`)}};
  q('#newFile').onclick=async()=>{let pending=modal('Create text file','<input id="fileName" placeholder="File name, e.g. notes.txt"><textarea id="newContent" placeholder="File content"></textarea>','Create');let ok=await pending;if(!ok)return;let n=q('#fileName').value.trim();if(!n)return;try{await api('/api/file',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:joinPath(path,n),content:q('#newContent').value})});await window.files(path)}catch(e){await notice('Create file',`${e.code||'FILE'}: ${e.message||'Could not create file'}`)}};
  q('#uploadBtn').onclick=()=>q('#uploadFile').click();
  q('#uploadFile').onchange=async()=>{let file=q('#uploadFile').files?.[0];if(!file)return;let fd=new FormData();fd.append('file',file);q('#uploadBtn').disabled=true;q('#uploadBtn').textContent='Uploading…';try{await api('/api/upload?path='+encodeURIComponent(path),{method:'POST',body:fd});await window.files(path)}catch(e){q('#uploadBtn').disabled=false;q('#uploadBtn').textContent='Upload file';await notice('Upload failed',`${e.code||'FILE'}: ${e.message||'Upload failed'}`)}}
 }
};
})();
