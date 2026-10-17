// 旅遊小助手 service worker: app shell offline; deals always from network (falls back to last copy).
const C='flysave-v30', SHELL=['./','index.html','manifest.json','icon-96.png','icon-192.png','apple-touch-icon.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(SHELL)));self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k)))));self.clients.claim();});
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  if(e.request.method!=='GET')return;
  if(u.origin!==location.origin){ // Apps Script JSON: network first, keep last good copy
    e.respondWith(fetch(e.request).then(r=>{const k=r.clone();caches.open(C).then(c=>c.put(e.request,k));return r;}).catch(()=>caches.match(e.request)));return;}
  e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));
});
// v22.1 iPhone 推播修正：自己處理 push 事件，每則一定顯示通知（iOS 規定），不靠 Firebase SDK 代為顯示
self.addEventListener('push',e=>{let p={};try{p=e.data?e.data.json():{}}catch(x){try{p={notification:{body:e.data.text()}}}catch(y){}}
 const n=p.notification||{},d=p.data||{},t=n.title||d.title||'飛省 FlySave',l=(p.fcmOptions&&p.fcmOptions.link)||d.link||'./#tab=notify';
 e.stopImmediatePropagation();
 e.waitUntil(self.registration.showNotification(t,{body:n.body||d.body||'',icon:'icon-192.png',badge:'icon-96.png',tag:d.id||undefined,data:{link:l}}));});
// v18 FCM web push（Firebase Cloud Messaging）
importScripts('https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js','https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging-compat.js');
try{firebase.initializeApp({"apiKey":"AIzaSyAguQSoX4yxi9N3OjN0-wctY7emdD_DU3k","authDomain":"flysave-28017.firebaseapp.com","projectId":"flysave-28017","storageBucket":"flysave-28017.firebasestorage.app","messagingSenderId":"55694360376","appId":"1:55694360376:web:e4318bd17848073e9a4bcd","measurementId":"G-T5Z7VYPTQL"});const m=firebase.messaging();
 m.onBackgroundMessage(p=>{if(p.notification)return;const d=p.data||{};return self.registration.showNotification(d.title||'飛省 FlySave',{body:d.body||'',icon:'icon-192.png',data:{link:d.link}});});}catch(e){}
self.addEventListener('notificationclick',e=>{const d=(e.notification.data||{}),l=(d.FCM_MSG&&d.FCM_MSG.data&&d.FCM_MSG.data.link)||d.link||'./';e.notification.close();
 e.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(cs=>{for(const c of cs){if('focus' in c){c.postMessage({link:l});return c.focus();}}return clients.openWindow(l);}));});
