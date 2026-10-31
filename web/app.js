import {parseProfile, targetAt, toCsv, toTxt, asClock, EXAMPLE} from "./profile-core.mjs";

// This public site is an offline profile planner, NEVER a TCP roaster controller.
const $ = id => document.getElementById(id);
const SVG = "http://www.w3.org/2000/svg";
const state = {points:[],name:"",sec:0,playing:false,lastTick:0,target:180};
let messageTimer = null;

function notify(text,isError=false) {
  const el = $("message");
  el.textContent = text;
  el.classList.toggle("error",isError);
  if (messageTimer) clearTimeout(messageTimer);
  messageTimer=setTimeout(()=>{el.textContent="";el.classList.remove("error");},6500);
}
function saveTarget(value) {
  try {localStorage.setItem("geneRev4WebTarget",String(value));} catch {}
}
try {
  const v = Number(localStorage.getItem("geneRev4WebTarget"));
  if (Number.isInteger(v) && v >= 150 && v <= 250) state.target=v;
} catch {}
$("manualTarget").value=String(state.target);
$("manualValue").textContent=String(state.target);
$("manualTarget").addEventListener("input",ev=>{
  state.target=Number(ev.target.value);
  $("manualValue").textContent=String(state.target);
  saveTarget(state.target);
});

function load(points,name) {
  state.points=points;state.name=name;state.sec=0;state.playing=false;
  state.lastTick=0;render();
  notify(points.length+" profilpont sikeresen betöltve. Ez csak helyi előnézet.");
}
function render() {
  const p=state.points, has=p.length>0;
  const duration=has?p[p.length-1].time:0;
  state.sec=Math.max(0,Math.min(state.sec,duration));
  $("fileName").textContent=has?state.name:"Nincs kiválasztva";
  $("pointCount").textContent=p.length+" PONT";
  $("play").disabled=!has || state.playing || state.sec>=duration;
  $("pause").disabled=!state.playing;
  $("reset").disabled=!has || (state.sec===0&&!state.playing);
  $("exportCsv").disabled=!has;
  $("exportTxt").disabled=!has;
  $("clear").disabled=!has;
  $("seek").disabled=!has;
  $("seek").max=String(Math.max(duration,1));
  $("seek").value=String(Math.floor(state.sec));
  $("clock").textContent=asClock(state.sec);
  $("seekLabel").textContent=asClock(state.sec)+" / "+asClock(duration);
  const planned=targetAt(p,state.sec);
  $("profileTarget").textContent=(planned===null?"—":Number(planned).toFixed(1))+" °C";
  $("targetDetail").textContent=has?"Tervezett, nem mért célérték":"Tölts be egy profilt";
  $("previewState").textContent=!has?"NINCS PROFIL":state.playing?"ELŐNÉZET FUT":state.sec>=duration?"PROFIL VÉGE":"ELŐNÉZET KÉSZ";
  $("chartNote").textContent=!has
    ?"Tölts be egy CSV/TXT fájlt, vagy próbáld ki a minta-profilt."
    :state.sec>=duration?"A profil véget ért. NEM küldtünk COOL parancsot.":("Időpont: "+asClock(state.sec)+", tervezett cél: "+(planned===null?"még nincs":planned+" °C")+".");
  renderChart();
}

function svgNode(name,attrs,text) {
  const node=document.createElementNS(SVG,name);
  for (const [key,val] of Object.entries(attrs||{})) node.setAttribute(key,String(val));
  if(text!==undefined)node.textContent=String(text);
  return node;
}
function renderChart() {
  const svg=$("chart"),pts=state.points;
  svg.replaceChildren();
  const L=58,T=20,W=665,H=207,B=T+H;
  const total=pts.length?Math.max(60,pts[pts.length-1].time):360;
  const x=s=>L+(s/total)*W, y=t=>T+H-(t-140)/120*H;
  for(let c=150;c<=250;c+=25){
    svg.append(svgNode("line",{x1:L,y1:y(c),x2:L+W,y2:y(c),stroke:"#704a35","stroke-width":1,"stroke-dasharray":"4,5"}));
    svg.append(svgNode("text",{x:45,y:y(c)+4,fill:"#d6af91","text-anchor":"end","font-size":13},c+"°"));
  }
  for(let i=0;i<=5;i++){
    const sec=total*i/5;
    svg.append(svgNode("text",{x:x(sec),y:B+24,fill:"#d6af91","text-anchor":"middle","font-size":13},asClock(sec)));
  }
  svg.append(svgNode("line",{x1:L,y1:B,x2:L+W,y2:B,stroke:"#9b6d4d","stroke-width":1.5}));
  svg.append(svgNode("text",{x:L,y:14,fill:"#d6af91","font-size":12},"CÉLHŐMÉRSÉKLET (°C)"));
  if(!pts.length){
    svg.append(svgNode("text",{x:L+W/2,y:125,fill:"#ac8b76","text-anchor":"middle","font-size":18},"Nincs betöltött profil"));
    return;
  }
  const first=pts[0];
  let path="M"+x(first.time).toFixed(2)+" "+y(first.temp).toFixed(2);
  for(let i=1;i<pts.length;i++){
    path+=" H"+x(pts[i].time).toFixed(2)+" V"+y(pts[i].temp).toFixed(2);
  }
  path+=" H"+x(total).toFixed(2);
  svg.append(svgNode("path",{d:path,fill:"none",stroke:"#ffbd78","stroke-width":4,"stroke-linejoin":"round"}));
  for(const p of pts)svg.append(svgNode("circle",{cx:x(p.time),cy:y(p.temp),r:4,fill:"#fff1d6",stroke:"#df9155","stroke-width":2}));
  svg.append(svgNode("line",{x1:x(state.sec),y1:T,x2:x(state.sec),y2:B,stroke:"#ffe29b","stroke-width":2,"stroke-dasharray":"6,4"}));
  const planned=targetAt(pts,state.sec);
  if(planned!==null)svg.append(svgNode("circle",{cx:x(state.sec),cy:y(planned),r:7,fill:"#fff2ba",stroke:"#854a27","stroke-width":3}));
}
function renderTable() {
  const body=$("pointsBody");body.replaceChildren();
  if(!state.points.length){
    const tr=document.createElement("tr"),td=document.createElement("td");
    td.colSpan=3;td.className="empty";td.textContent="Még nincs betöltött profil.";
    tr.append(td);body.append(tr);return;
  }
  const fragment=document.createDocumentFragment();
  for(const p of state.points){
    const tr=document.createElement("tr");
    for(const val of [asClock(p.time),String(p.time),p.temp.toFixed(1)+" °C"]){
      const td=document.createElement("td");td.textContent=val;tr.append(td);
    }
    fragment.append(tr);
  }
  body.append(fragment);
}
const originalLoad=load;
function loadAndTable(pts,name){originalLoad(pts,name);renderTable();}
$("upload").addEventListener("change",async ev=>{
  const file=ev.target.files&&ev.target.files[0];if(!file)return;
  try{
    if(file.size>1024*1024)throw Error("A profilfájl legfeljebb 1 MB lehet.");
    const content=await file.text();
    loadAndTable(parseProfile(content),file.name);
  }catch(error){notify(error.message||"A profil nem olvasható.",true);}
  ev.target.value="";
});
$("example").addEventListener("click",()=>loadAndTable(EXAMPLE.map(p=>({...p})),"MINTA_PROFIL – NEM MÉRÉS"));
$("clear").addEventListener("click",()=>{
  state.playing=false;state.points=[];state.name="";state.sec=0;render();renderTable();notify("Profil törölve.");
});
function saveFile(filename,content,type) {
  const blob=new Blob([content],{type:type+";charset=utf-8"});
  const url=URL.createObjectURL(blob);
  const link=document.createElement("a");
  link.href=url;link.download=filename;
  document.body.appendChild(link);link.click();link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
$("exportCsv").addEventListener("click",()=>{
  if(state.points.length)saveFile("GeneRev4_profil.csv",toCsv(state.points),"text/csv");
});
$("exportTxt").addEventListener("click",()=>{
  if(state.points.length)saveFile("GeneRev4_profil.txt",toTxt(state.points),"text/plain");
});
$("seek").addEventListener("input",ev=>{
  state.sec=Number(ev.target.value);
  state.lastTick=performance.now();
  render();
});
$("play").addEventListener("click",()=>{
  if(!state.points.length || state.playing)return;
  state.playing=true;state.lastTick=performance.now();render();
});
$("pause").addEventListener("click",()=>{state.playing=false;render();});
$("reset").addEventListener("click",()=>{state.playing=false;state.sec=0;render();});
window.setInterval(()=>{
  if(!state.playing||!state.points.length)return;
  const now=performance.now();
  state.sec+=(now-state.lastTick)/1000;
  state.lastTick=now;
  const final=state.points[state.points.length-1].time;
  if(state.sec>=final){state.sec=final;state.playing=false;notify("A profil előnézete véget ért. A pörkölő nem kapott parancsot.");}
  render();
},250);
document.addEventListener("visibilitychange",()=>{
  // Pausing is deliberate: the browser must not pretend that a real roast kept running.
  if(document.hidden&&state.playing){state.playing=false;render();}
});
render();renderTable();
if("serviceWorker" in navigator&&window.isSecureContext){
  navigator.serviceWorker.register("./sw.js").catch(()=>{});
}
