// if ('serviceWorker' in navigator && 'PushManager' in window) {
//     navigator.serviceWorker.register('/static/js/service-worker.js').then(function(swReg) {
//         console.log('Service Worker Registered', swReg);
//         swRegistration = swReg;
//         initializeUI();
//     }).catch(function(error) {
//         console.error('Service Worker Error', error);
//     });
// }

// function initializeUI() {
//     Notification.requestPermission().then(function(permission) {
//         if (permission === 'granted') {
//             console.log('Notification permission granted.');
//         } else {
//             console.log('Notification permission denied.');
//         }
//     });
// }