const chat = document.getElementById('chat');
const form = document.getElementById('chatForm');
const question = document.getElementById('question');
const trace = document.getElementById('trace');
const sourceUsed = document.getElementById('sourceUsed');
const memoryInfo = document.getElementById('memoryInfo');
const domain = 'hr';
const welcomeHtml = chat.innerHTML;

// ---- Conversation id, kept per domain in the browser ----
const threadKey = `threadId:${domain}`;
function newThreadId(){return (window.crypto?.randomUUID?.() || `${Date.now()}${Math.random().toString(16).slice(2)}`).replace(/[^A-Za-z0-9_-]/g,'');}
function loadThreadId(){try{return localStorage.getItem(threadKey);}catch{return null;}}
function saveThreadId(id){try{localStorage.setItem(threadKey,id);}catch{}}
let threadId = loadThreadId() || newThreadId();
saveThreadId(threadId);
function setMemoryInfo(turns){memoryInfo.textContent = turns ? `Memory: ${turns} turn${turns>1?'s':''}` : 'New conversation';}

function escapeHtml(s=''){return String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
function formatText(s=''){return escapeHtml(s).replace(/\n/g,'<br>');}
function renderCitation(c){
  const isWeb=c.type==='web' && /^https?:\/\//.test(c.url||'');
  const title=isWeb?`<a href="${escapeHtml(c.url)}" target="_blank" rel="noopener">${escapeHtml(c.title)}</a>`:escapeHtml(c.title);
  const page=c.page?`<span class="cite-page">p. ${escapeHtml(c.page)}</span>`:'';
  const kind=`<span class="cite-kind ${isWeb?'web':'kb'}">${isWeb?'Web':'Company KB'}</span>`;
  const quote=c.excerpt?`<details><summary>Excerpt</summary><blockquote>${escapeHtml(c.excerpt)}</blockquote></details>`:'';
  return `<div class="cite-item"><div class="cite-head">${kind}<span class="cite-title">${title}</span>${page}</div>${quote}</div>`;
}
function addMessage(role, text, source='', citations=[]){
  const wrap=document.createElement('div'); wrap.className=`message ${role}`;
  const citeHtml=citations.length?`<div class="citations"><strong>Sources</strong>${citations.map(renderCitation).join('')}</div>`:'';
  wrap.innerHTML=`<div class="avatar">${role==='user'?'You':'AI'}</div><div class="bubble">${formatText(text)}${source?`<div class="answer-source">Source: ${escapeHtml(source)}</div>`:''}${citeHtml}</div>`;
  chat.appendChild(wrap); chat.scrollTop=chat.scrollHeight;
}
function renderTrace(items=[]){trace.innerHTML=items.length?items.map(x=>`<div class="trace-item">${escapeHtml(x)}</div>`).join(''):'<div class="empty">No trace.</div>';}

async function askAgent(q){
  addMessage('user',q); question.value=''; renderTrace(['Running LangGraph workflow...']); sourceUsed.textContent='Running';
  const btn=form.querySelector('button'); btn.disabled=true;
  try{
    const res=await fetch(`/api/chat/${domain}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,thread_id:threadId})});
    const data=await res.json(); if(!res.ok) throw new Error(typeof data.detail==='string'?data.detail:'Request failed');
    const checked={fully_supported:' · verified against sources',partially_supported:' · partially verified'}[data.support_status]||'';
    addMessage('assistant',data.answer,data.source_used+checked,data.citations||[]); renderTrace(data.trace||[]); sourceUsed.textContent=data.source_used;
    setMemoryInfo(data.memory_turns);
    loadConversations();
  }catch(e){addMessage('assistant',`Error: ${e.message}`); renderTrace(['Request failed']); sourceUsed.textContent='Error';}
  finally{btn.disabled=false;}
}

async function restoreHistory(){
  try{
    const res=await fetch(`/api/sessions/${domain}/${encodeURIComponent(threadId)}`);
    if(!res.ok) return;
    const data=await res.json();
    data.turns.forEach(t=>{addMessage('user',t.question); addMessage('assistant',t.answer,t.source_used,t.citations||[]);});
    setMemoryInfo(data.turns.length);
  }catch{}
}

// ---- Previous conversations of this domain ----
const convList = document.getElementById('convList');
function formatDate(iso){try{return new Date(iso).toLocaleString([], {dateStyle:'short', timeStyle:'short'});}catch{return '';}}
async function loadConversations(){
  try{
    const res=await fetch(`/api/sessions/${domain}`); if(!res.ok) return;
    const {sessions}=await res.json();
    convList.innerHTML=sessions.length?sessions.map(s=>`
      <div class="conv-item${s.thread_id===threadId?' active':''}" data-id="${escapeHtml(s.thread_id)}" role="button" tabindex="0" title="${escapeHtml(s.title)}">
        <div class="conv-text"><div class="conv-title">${escapeHtml(s.title)}</div>
        <div class="conv-meta">${formatDate(s.updated_at)} · ${s.turns} msg</div></div>
        <button class="conv-delete" type="button" title="Delete conversation">×</button>
      </div>`).join(''):'<div class="empty">No conversation yet.</div>';
  }catch{}
}
function resetChat(){chat.innerHTML=welcomeHtml; renderTrace([]); sourceUsed.textContent='—'; setMemoryInfo(0);}
function openConversation(id){threadId=id; saveThreadId(id); resetChat(); restoreHistory(); loadConversations();}
function startNewChat(){threadId=newThreadId(); saveThreadId(threadId); resetChat(); loadConversations();}
convList.addEventListener('click',async e=>{
  const item=e.target.closest('.conv-item'); if(!item) return;
  const id=item.dataset.id;
  if(e.target.closest('.conv-delete')){
    if(!confirm('Delete this conversation?')) return;
    await fetch(`/api/sessions/${domain}/${encodeURIComponent(id)}`,{method:'DELETE'});
    if(id===threadId) startNewChat(); else loadConversations();
    return;
  }
  if(id!==threadId) openConversation(id);
});
convList.addEventListener('keydown',e=>{
  if((e.key==='Enter'||e.key===' ')&&e.target.classList.contains('conv-item')){e.preventDefault(); e.target.click();}
});

document.getElementById('newChat').onclick=startNewChat;
form.addEventListener('submit',e=>{e.preventDefault(); const q=question.value.trim(); if(q) askAgent(q);});
document.querySelectorAll('.example').forEach(b=>b.addEventListener('click',()=>askAgent(b.textContent.trim())));
restoreHistory();
loadConversations();

// ---- Documents: upload, list, delete ----
const modal=document.getElementById('uploadModal');
const docList=document.getElementById('docList');
const uploadStatus=document.getElementById('uploadStatus');
const adminKey=()=>document.getElementById('adminKey').value;
async function loadDocuments(){
  try{
    const res=await fetch(`/api/documents/${domain}`); if(!res.ok) return;
    const {documents}=await res.json();
    docList.innerHTML=documents.length?documents.map(d=>`
      <div class="doc-item" data-file="${escapeHtml(d.filename)}">
        <div class="conv-text"><div class="conv-title" title="${escapeHtml(d.filename)}">${escapeHtml(d.filename)}</div>
        <div class="conv-meta">${d.chunks} chunks · ${formatDate(d.indexed_at)}</div></div>
        <button class="conv-delete" type="button" title="Remove from knowledge base">×</button>
      </div>`).join(''):'<div class="empty">No document indexed from this app yet.</div>';
  }catch{}
}
docList.addEventListener('click',async e=>{
  if(!e.target.closest('.conv-delete')) return;
  const file=e.target.closest('.doc-item').dataset.file;
  if(!confirm(`Remove "${file}" from the knowledge base?`)) return;
  uploadStatus.textContent=`Removing ${file}...`;
  try{
    const r=await fetch(`/api/documents/${domain}/${encodeURIComponent(file)}`,{method:'DELETE',headers:{'X-Admin-Key':adminKey()}});
    const d=await r.json(); if(!r.ok) throw new Error(d.detail||'Delete failed');
    uploadStatus.textContent=`Removed ${file}.`; loadDocuments();
  }catch(e){uploadStatus.textContent=`Error: ${e.message}`;}
});
document.getElementById('openUpload').onclick=()=>{modal.classList.remove('hidden'); loadDocuments();};
document.getElementById('closeUpload').onclick=()=>modal.classList.add('hidden');
document.getElementById('uploadBtn').onclick=async()=>{
  const file=document.getElementById('fileInput').files[0];
  if(!file){uploadStatus.textContent='Choose a file first.'; return;}
  uploadStatus.textContent='Indexing document...'; const fd=new FormData(); fd.append('file',file);
  try{const r=await fetch(`/api/ingest/${domain}`,{method:'POST',headers:{'X-Admin-Key':adminKey()},body:fd}); const d=await r.json(); if(!r.ok) throw new Error(d.detail||'Upload failed'); uploadStatus.textContent=`Indexed ${d.file}: ${d.chunks} chunks.`; loadDocuments();}catch(e){uploadStatus.textContent=`Error: ${e.message}`;}
};
