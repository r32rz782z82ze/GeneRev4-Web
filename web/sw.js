const VERSION="generev4-profile-web-v1";
const ASSETS=["./","./index.html","./style.css","./app.js","./profile-core.mjs","./manifest.webmanifest","./icon.svg"];
self.addEventListener("install",event=>{
  event.waitUntil(caches.open(VERSION).then(cache=>cache.addAll(ASSETS)).then(()=>self.skipWaiting()));
});
self.addEventListener("activate",event=>{
  event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==VERSION).map(key=>caches.delete(key)))).then(()=>self.clients.claim()));
});
self.addEventListener("fetch",event=>{
  if(event.request.method!=="GET" || new URL(event.request.url).origin!==self.location.origin)return;
  event.respondWith(fetch(event.request).then(response=>{
    if(response.ok){const cloned=response.clone();caches.open(VERSION).then(cache=>cache.put(event.request,cloned)).catch(()=>{});}
    return response;
  }).catch(()=>caches.match(event.request)));
});
