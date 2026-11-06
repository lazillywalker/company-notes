'use strict';
const $=id=>document.getElementById(id);let token='',notes=[],item='',revision=0,before=null,pending=null,proposal='',education=[];const fields=['category','title','ja','en','keywords','scope','source','start','end','visibility','reason'];
function language(){return $('language').value}function localize(){document.documentElement.lang=language();document.querySelectorAll('[data-ja]').forEach(e=>e.textContent=e.dataset[language()])}function message(t){$('status').textContent=t}function pre(parent,text){let el=document.createElement('pre');el.textContent=text;parent.append(el);return el}
async function api(path,p){let r=await fetch('/api/'+path,p?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...p,token})}:{});let d=await r.json();if(!r.ok)throw Error(d.error);return d}
async function task(button,fn){button.disabled=true;message(language()==='ja'?'処理中…':'Working…');try{await fn();message('完了 / Done')}catch(e){message(e.message)}finally{button.disabled=false}}
async function refresh(){let d=await api('state');token=d.token;notes=d.notes;if(!$('category').options.length)d.categories.forEach((s,i)=>$('category').add(new Option(s,i)));list()}
function list(){$('notes').replaceChildren();notes.filter(r=>r.content.toLowerCase().includes($('filter').value.toLowerCase())).forEach(r=>{let n=JSON.parse(r.content),box=document.createElement('div');box.className='card';let t=document.createElement('h3');t.textContent=n.title+' · '+r.state+' · v'+r.revision;box.append(t);let s=document.createElement('small');s.textContent=r.created+' · '+r.reviewer;box.append(s);let b=document.createElement('button');b.textContent='編集 / Edit';b.onclick=()=>load(r);box.append(b);let h=document.createElement('button');h.textContent='履歴・復元 / History & restore';h.className='secondary';h.onclick=()=>task(h,async()=>{let d=await api('history',{item:r.item});d.rows.forEach(old=>{pre(box,old.created+' '+old.state+'\n'+old.content);let restore=document.createElement('button');restore.textContent='この版を編集欄に戻す / Restore to editor';restore.onclick=()=>{load({...r,content:old.content});$('state').value='draft';$('reason').value='以前の版から復元 / Restored from v'+old.revision};box.append(restore)});h.disabled=true});box.append(h);$('notes').append(box)})}
function load(r){item=r.item;revision=r.revision;before=JSON.parse(r.content);fields.forEach(k=>$(k).value=before[k]??'');setHours(before.weekly_hours);$('state').value=r.state;$('preview').hidden=true;$('editor').scrollIntoView({behavior:'smooth'})}
$('new').onclick=()=>{item='';revision=0;before=null;$('editor').reset();setHours(null);$('preview').hidden=true};$('editor').onsubmit=async e=>{e.preventDefault();try{let note=Object.fromEntries(fields.map(k=>[k,$(k).value]));note.category=Number(note.category);if($('hoursEnabled').checked)note.weekly_hours=getHours();pending={note,item,revision,state:$('state').value,reviewer:$('reviewer').value};await api('validate',{note});$('diff').textContent=JSON.stringify({before,after:note,state:pending.state},null,2);$('preview').hidden=false}catch(error){message(error.message)}};$('save').onclick=()=>task($('save'),async()=>{await api('save',pending);$('preview').hidden=true;await refresh();$('new').click()});$('editor').oninput=()=>{$('preview').hidden=true;pending=null};
$('educate').onclick=()=>task($('educate'),async()=>{let text=$('educationText').value;education.push({role:'user',text});let d=await api('educate',{text:JSON.stringify(education.slice(-8))});proposal=d.answer;education.push({role:'assistant',text:proposal});pre($('educationLog'),text+'\n\n'+proposal);$('educationText').value=''});$('useDraft').onclick=()=>{if(proposal)$(language()).value=proposal;$('preview').hidden=true};
$('ask').onclick=()=>task($('ask'),async()=>{let text=$('question').value;let d=await api('ask',{text,language:language()});let box=document.createElement('div');pre(box,text+'\n\n'+d.answer);let details=document.createElement('details');let summary=document.createElement('summary');summary.textContent='参照元 / Sources';details.append(summary);(d.refs||[]).forEach(r=>pre(details,'#'+r.id+' '+r.title+' · v'+r.revision+'\n'+r.source+'\n'+r.updated));box.append(details);let b=document.createElement('button');b.textContent='教育側へ訂正を送る / Send for correction';b.onclick=()=>{$('teachTab').click();$('educationText').value='質問 / Question: '+text+'\n回答 / Answer: '+d.answer+'\n参照 / References: '+JSON.stringify(d.refs)+'\n訂正内容・理由 / Correction & reason: ';};box.append(b);$('answers').append(box);await loadLogs(true)});
$('teachTab').onclick=()=>{$('teach').hidden=false;$('respond').hidden=true};$('answerTab').onclick=()=>{$('teach').hidden=true;$('respond').hidden=false};$('export').onclick=()=>task($('export'),async()=>{let d=await api('export',{});pre($('notes'),'保存先 / Saved: '+d.path)});$('language').onchange=localize;$('filter').oninput=list;localize();refresh().catch(e=>message(e.message));

const days=['mon','tue','wed','thu','fri','sat','sun'];
const dayLabels=['月 / Mon','火 / Tue','水 / Wed','木 / Thu','金 / Fri','土 / Sat','日 / Sun'];
days.forEach((d,i)=>{const row=document.createElement('div'),label=document.createElement('label'),select=document.createElement('select'),input=document.createElement('input');label.textContent=dayLabels[i];select.id='status_'+d;[['unknown','未確認 / Unknown'],['open','営業 / Open'],['closed','休業 / Closed']].forEach(([v,t])=>select.add(new Option(t,v)));input.id='times_'+d;input.placeholder='09:00-18:00';input.disabled=true;select.onchange=()=>{input.disabled=select.value!=='open';if(input.disabled)input.value=''};row.append(label,select,input);$('weeklyHours').append(row)});
function setHours(hours){$('hoursEnabled').checked=!!hours;days.forEach(d=>{const e=hours?.[d]||{status:'unknown',periods:[]};$('status_'+d).value=e.status;$('times_'+d).value=(e.periods||[]).map(p=>p.join('-')).join(',');$('times_'+d).disabled=e.status!=='open'})}
function getHours(){return Object.fromEntries(days.map(d=>{const status=$('status_'+d).value;return[d,{status,periods:status==='open'?$('times_'+d).value.split(',').filter(x=>x.trim()).map(x=>x.trim().split('-').map(t=>t.trim())):[]}]}))}
$('loadJson').onclick=()=>task($('loadJson'),async()=>{let n=JSON.parse($('jsonInput').value);if(Array.isArray(n)){if(n.length!==1)throw Error('1件ずつ読み込んでください / Import one note at a time');n=n[0]}if(n.content)n=typeof n.content==='string'?JSON.parse(n.content):n.content;const d=await api('validate',{note:n});load({item:'',revision:0,content:JSON.stringify(d.note),state:'draft'});before=null});
$('jsonFile').onchange=async()=>{try{const f=$('jsonFile').files[0];if(!f)return;if(f.size>200000)throw Error('200 KB以下 / Maximum 200 KB');$('jsonInput').value=await f.text()}catch(e){message(e.message)}};
$('sampleJson').onclick=()=>{$('jsonInput').value=JSON.stringify({category:0,title:'サンプル店の営業時間 / Example store hours',ja:'通常の週間営業時間。祝日の営業は別途確認してください。',en:'Regular weekly schedule. Confirm holiday exceptions with staff.',scope:'サンプル店 / Example store',visibility:'public',keywords:'営業時間 定休日 opening hours',weekly_hours:Object.fromEntries(days.map(d=>[d,{status:d==='wed'?'closed':'open',periods:d==='wed'?[]:[[d==='sun'?'10:00':'09:00',d==='sun'?'17:00':'18:00']]}]))},null,2)};

let logCursor=0;
async function loadLogs(reset){
 if(reset){logCursor=0;$('chatLogs').replaceChildren()}
 const data=await api('chatlogs',{before:logCursor});
 if(reset&&!data.rows.length)pre($('chatLogs'),'記録はまだありません / No records yet');
 data.rows.forEach(r=>{
  const box=document.createElement('article'),heading=document.createElement('h3');box.className='card';
  heading.textContent='#'+r.id+' · '+new Date(r.created).toLocaleString(language()==='ja'?'ja-JP':'en-GB');box.append(heading);
  pre(box,'質問 / Question\n'+r.question);pre(box,'回答 / Answer\n'+r.answer);
  const detail=document.createElement('details'),summary=document.createElement('summary');summary.textContent='参照教材 / Sources';detail.append(summary);
  let refs;try{refs=JSON.parse(r.refs)}catch{refs=r.refs}
  pre(detail,JSON.stringify(refs,null,2));box.append(detail);
  const remove=document.createElement('button');remove.className='danger';remove.textContent=language()==='ja'?'このログを削除':'Delete this log';
  remove.onclick=()=>{if(!confirm(language()==='ja'?'ログ #'+r.id+' の質問・回答・参照記録を削除します。元には戻せません。削除しますか？':'Delete question, answer and references for log #'+r.id+'? This cannot be undone.'))return;task(remove,async()=>{await api('chatlogs/delete',{id:r.id});await loadLogs(true)})};
  box.append(remove);$('chatLogs').append(box);
 });
 if(data.rows.length)logCursor=data.rows[data.rows.length-1].id;$('olderLogs').hidden=data.rows.length<50;
}
async function exportLogs(format){
 const d=await api('chatlogs/export',{format});
 const blob=new Blob([d.content],{type:format==='txt'?'text/plain;charset=utf-8':'application/json;charset=utf-8'});
 const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=d.filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);
 $('logExportResult').textContent=d.count+'件を保存 / records saved — '+d.path+'（ダウンロード先にも保存 / Also downloaded）';
}
$('loadLogs').onclick=()=>task($('loadLogs'),()=>loadLogs(true));
$('olderLogs').onclick=()=>task($('olderLogs'),()=>loadLogs(false));
$('exportLogs').onclick=()=>task($('exportLogs'),()=>exportLogs('json'));
$('exportTextLogs').onclick=()=>task($('exportTextLogs'),()=>exportLogs('txt'));

$('deleteAllLogs').onclick=()=>{
 if(!confirm(language()==='ja'?'すべての応答ログ（質問・回答・参照記録）を削除します。教材と出力済みファイルは残ります。必要なログは先に保存してください。削除しますか？':'Delete ALL response logs? Notes and exported files remain. Save any needed logs first. Continue?'))return;
 task($('deleteAllLogs'),async()=>{await api('chatlogs/delete',{all:true,confirmation:'DELETE_ALL_RESPONSE_LOGS'});$('answers').replaceChildren();await loadLogs(true)});
};
