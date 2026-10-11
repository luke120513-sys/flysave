// 飛省 FlySave：推播已合併在 sw.js（scope /flysave/）。這個檔只給 Firebase 預設路徑備用。
// v18 FCM web push（Firebase Cloud Messaging）
importScripts('https://www.gstatic.com/firebasejs/10.12.2/firebase-app-compat.js','https://www.gstatic.com/firebasejs/10.12.2/firebase-messaging-compat.js');
try{firebase.initializeApp({"apiKey":"AIzaSyAguQSoX4yxi9N3OjN0-wctY7emdD_DU3k","authDomain":"flysave-28017.firebaseapp.com","projectId":"flysave-28017","storageBucket":"flysave-28017.firebasestorage.app","messagingSenderId":"55694360376","appId":"1:55694360376:web:e4318bd17848073e9a4bcd","measurementId":"G-T5Z7VYPTQL"});const m=firebase.messaging();
 m.onBackgroundMessage(p=>{if(p.notification)return;const d=p.data||{};return self.registration.showNotification(d.title||'飛省 FlySave',{body:d.body||'',icon:'icon-192.png',data:{link:d.link}});});}catch(e){}
self.addEventListener('notificationclick',e=>{const d=(e.notification.data||{}),l=(d.FCM_MSG&&d.FCM_MSG.data&&d.FCM_MSG.data.link)||d.link||'./';e.notification.close();
 e.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(cs=>{for(const c of cs){if('focus' in c){c.postMessage({link:l});return c.focus();}}return clients.openWindow(l);}));});
