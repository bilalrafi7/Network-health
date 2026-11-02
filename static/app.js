const el = id => document.getElementById(id);
function node(tag, text, cls) {const n=document.createElement(tag); if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
async function refresh(){
  try{
    const response=await fetch('/api/health',{cache:'no-store'});if(!response.ok)throw Error('Server returned '+response.status);
    const data=await response.json();const targets=data.targets;const checked=targets.filter(t=>t.latest);const available=checked.filter(t=>t.latest.status!=='down');
    el('total').textContent=targets.length;el('up').textContent=available.length+' / '+targets.length;
    el('latency').textContent=available.length?Math.round(available.reduce((a,t)=>a+t.latest.latency,0)/available.length)+' ms':'—';
    const history=targets.flatMap(t=>t.history);el('uptime').textContent=history.length?(100*history.filter(h=>h.status!=='down').length/history.length).toFixed(1)+'%':'—';
    el('overall').textContent=checked.length<targets.length?'◌ Collecting initial checks':available.length<targets.length?'● Attention needed':available.some(t=>t.latest.status==='slow')?'● Slow responses detected':'● All services operational';
    el('updated').textContent='View updated '+new Date().toLocaleTimeString();el('services').replaceChildren();
    for(const t of targets){const card=node('article',undefined,'service');const head=node('div',undefined,'service-head');head.append(node('h3',t.name),node('span',t.latest?{up:'Available',slow:'Slow',down:'Unavailable'}[t.latest.status]:'Pending','badge '+(t.latest?.status||'pending')));card.append(head,node('div',t.url||t.host+':'+t.port,'endpoint'));const bars=node('div',undefined,'bars');
      for(let i=0;i<60-t.history.length;i++)bars.append(node('span',undefined,'bar pending'));
      for(const h of t.history){const bar=node('span',undefined,'bar '+h.status);bar.title=new Date(h.checked_at).toLocaleString()+' · '+h.status+(h.latency!==null?' · '+h.latency+' ms':'');bars.append(bar);}
      const foot=node('div',undefined,'service-foot');foot.append(node('span','Last 60 checks'),node('span',t.uptime===null?'Awaiting checks':t.uptime+'% available'));card.append(bars,foot,node('div',t.latest?(t.latest.latency!==null?t.latest.latency+' ms · ':'')+t.latest.detail:'Waiting for the first check…','detail'));el('services').append(card);}
    const failures=history.filter(h=>h.status==='down').sort((a,b)=>b.id-a.id).slice(0,8);el('failures').replaceChildren();if(!failures.length)el('failures').textContent=history.length?'No failures in the retained view.':'Waiting for first checks…';
    for(const h of failures){const row=node('div',undefined,'failure');row.append(node('span',h.target+' · '+h.detail),node('span',new Date(h.checked_at).toLocaleString()));el('failures').append(row);}
  }catch(error){el('overall').textContent='● Monitor connection lost';el('updated').textContent=error.message+' · Start python3 server.py';}
}
el('refresh').addEventListener('click',refresh);refresh();setInterval(refresh,5000);
