"use strict";
// Actual TCP commands are sent ONLY to the loopback Python bridge, never from GitHub Pages.
const $ = id => document.getElementById(id);
let token = "";
let lastStatus = null;
let busy = false;
let samples = [];
const localApi = async (path, body) => {
  const response = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? {} : {
      "Content-Type": "application/json", "X-GeneRev4-Token": token
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store"
  });
  const data = await response.json();
  if (!response.ok) throw Error(data.error || "HTTP " + response.status);
  return data;
};
function seconds(t) {
  if (t === null || t === undefined || !Number.isFinite(t)) return "—";
  const s = Math.max(0, Math.floor(t));
  return String(Math.floor(s/60)).padStart(2, "0") + ":" +
         String(s%60).padStart(2, "0");
}
function plot(history) {
  const svg = $("history");
  const NS = "http://www.w3.org/2000/svg";
  const node = (name, attrs, text) => {
    const el = document.createElementNS(NS, name);
    for (const [k,v] of Object.entries(attrs)) el.setAttribute(k,String(v));
    if (text !== undefined) el.textContent = String(text);
    return el;
  };
  svg.replaceChildren();
  const pad = 45, right = 702, top = 20, bottom = 158;
  for (const y of [50,100,150,200,250]) {
    const yy = bottom-(y/250)*(bottom-top);
    svg.append(node("line",{x1:pad,y1:yy,x2:right,y2:yy,stroke:"#6b4a39","stroke-dasharray":"4 5"}));
    svg.append(node("text",{x:37,y:yy+4,"font-size":12,fill:"#cba58a","text-anchor":"end"},y+"°"));
  }
  if (history.length < 2) {
    svg.append(node("text",{x:360,y:93,fill:"#d9b396","text-anchor":"middle","font-size":16},
      "Várakozás valódi hőmérsékletadatra"));
    return;
  }
  const first=history[0][0], range=Math.max(1,history[history.length-1][0]-first);
  const sx=time=>pad+((time-first)/range)*(right-pad);
  const sy=temp=>bottom-Math.max(0,Math.min(temp,250))/250*(bottom-top);
  const d=history.map((p,i)=>(i?"L":"M")+sx(p[0]).toFixed(2)+" "+sy(p[1]).toFixed(2)).join(" ");
  svg.append(node("path",{d,fill:"none",stroke:"#ffbc82","stroke-width":3}));
  svg.append(node("text",{x:pad,y:181,fill:"#d0aa8e","font-size":11},"Korábbi értékek"));
  svg.append(node("text",{x:right,y:181,fill:"#d0aa8e","font-size":11,"text-anchor":"end"},"Legfrissebb mérés"));
}
function update(s) {
  lastStatus = s;
  const connected = Boolean(s.connected), fresh=Boolean(s.fresh);
  const ready=connected && fresh && s.controlEnabled;
  $("statusBadge").textContent = connected ? (fresh ? "TCP + FRISS MÉRÉS" : "TCP / MÉRÉS NINCS") : "NINCS KAPCSOLAT";
  $("statusBadge").classList.toggle("ok",fresh);
  $("temperature").textContent = fresh ? s.temperature.toFixed(1)+" °C" : "— °C";
  $("freshness").textContent= fresh ? ("Utoljára "+s.age+" másodperce érkezett szám") : "Nincs friss mérés";
  $("clock").textContent = seconds(s.elapsed);
  $("shownTarget").textContent=String(s.setpoint)+" °C";
  $("requestedState").textContent=s.requestedState || "ISMERETLEN";
  $("notice").textContent=s.notice || "";
  $("modeBadge").textContent=s.controlEnabled?"HELYI VEZÉRLÉS ENGEDÉLYEZVE":"CSAK MONITOR MÓD";
  $("armState").textContent=s.armed?"INDÍTÁS ENGEDÉLYEZVE – 2 percen belül START lehetséges":"Nincs élesítve.";
  $("lastCommand").textContent="Utolsó elküldött parancs: "+(s.lastCommand||"nincs")+
    ". Nincs firmware-visszaigazolás!";
  if(!busy){
    $("connect").disabled=connected;
    $("disconnect").disabled=!connected;
    $("arm").disabled=!ready;
    $("start").disabled=!ready || !s.armed || s.runningRequested;
    $("cool").disabled=!connected || !s.controlEnabled;
    $("stop").disabled=!connected || !s.controlEnabled;
    $("setpoint").disabled=!ready || !s.runningRequested;
  }
  samples=Array.isArray(s.history)?s.history:[];
  $("export").disabled=!samples.length;
  plot(samples);
}
async function send(path, body, confirmText) {
  if(busy)return;
  if(confirmText&&!window.confirm(confirmText))return;
  busy=true;
  try {
    const s=await localApi(path,body);update(s);
  } catch (error) {
    alert("GeneRev4: "+error.message);
  } finally {
    busy=false;
    try{update(await localApi("/api/status"));}catch{}
  }
}
$("connect").addEventListener("click",()=>{
  const ip=$("host").value.trim();
  const port=Number($("port").value);
  if(!Number.isInteger(port))return alert("Hibás TCP-port.");
  send("/api/connect",{host:ip,port});
});
$("disconnect").addEventListener("click",()=>send("/api/disconnect",{},
  "Biztosan bontod a kapcsolatot? Ha START volt kérve, COOL megkísérlése következik, de a hardveres leállás nem garantált."));
$("arm").addEventListener("click",()=>send("/api/arm",{confirmation:$("armText").value},
  "A pörkölő mellett vagy, és ellenőrizted a független hővédelmet és a fizikai vészleállítót?"));
$("start").addEventListener("click",()=>send("/api/command",{action:"start",temperature:Number($("target").value)},
  "VALÓDI FŰTÉSINDÍTÁSI KÉRÉS! Fizikai felügyelet mellett is csak kipróbált hardverrel. Folytatod?"));
$("cool").addEventListener("click",()=>send("/api/command",{action:"cool"},
  "Valódi COOL-parancs elküldése? A hardver válasza nem ellenőrizhető."));
$("stop").addEventListener("click",()=>send("/api/command",{action:"stop"},
  "Valódi STOP / dob-visszaállítási parancs elküldése? Ez nem a fizikai vészleállító!"));
$("setpoint").addEventListener("click",()=>send("/api/command",
  {action:"setpoint",temperature:Number($("target").value)},
  "Új célhőmérséklet elküldése a valódi fűtésvezérlőnek?"));
$("target").addEventListener("input",()=>{
  $("targetValue").textContent=$("target").value+" °C";
});
$("export").addEventListener("click",()=>{
  if(!samples.length)return;
  const csv="idopont_monotonic_sec,homerseklet_celsius\r\n"+
    samples.map(x=>x.map(Number).join(",")).join("\r\n")+"\r\n";
  const url=URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"}));
  const a=document.createElement("a");
  a.href=url;a.download="GeneRev4_Valodi_Meresek.csv";
  a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
async function refresh(){
  if(busy)return;
  try {update(await localApi("/api/status"));}
  catch(e){$("statusBadge").textContent="HÍD NEM ELÉRHETŐ";$("statusBadge").classList.remove("ok");
    $("notice").textContent="A helyi híd nem válaszol. A fizikai pörkölő állapota ISMERETLEN. "+e.message;
    for(const id of ["connect","disconnect","arm","start","cool","stop","setpoint"])$(id).disabled=true;
  }
}
(async()=>{
  try{
    const session=await localApi("/api/session");
    token=session.token;
    await refresh();
    setInterval(refresh,850);
  }catch(e){$("notice").textContent="A helyi GeneRev4 híd nem érhető el: "+e.message;}
})();
