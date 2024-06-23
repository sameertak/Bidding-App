self.addEventListener('push', function(event) {
    console.log('Push received:', event); // Debugging

    if (!event.data) {
        console.error('Push event has no data');
        return;
    }

    try {
        const data = event.data.json();
        console.log('Push data:', data); // Debugging

        const options = {
            body: data.body,
            icon: data.icon,
            data: {
                url: data.url
            }
        };

        event.waitUntil(
            self.registration.showNotification(data.head, options)
        );
    } catch (error) {
        console.error('Error parsing push data:', error);
    }
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});