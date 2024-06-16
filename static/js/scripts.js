// document.addEventListener('DOMContentLoaded', function () {
//     const input = document.getElementById('destination');
//     const suggestions = document.getElementById('suggestions');
//     input.addEventListener('input', function () {
//         const query = input.value;
//         if (query.length > 2) {
//             fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${query}&addressdetails=1&countrycodes=IN`)
//                 .then(response => response.json())
//                 .then(data => {
//                     suggestions.innerHTML = '';
//                     data.forEach(item => {
//                         const li = document.createElement('li');
//                         li.textContent = item.display_name;
//                         li.addEventListener('click', function () {
//                             input.value = item.display_name;
//                             document.getElementById('destination_lat').value = item.lat;
//                             document.getElementById('destination_lng').value = item.lon;
//                             suggestions.innerHTML = '';
//                         });
//                         suggestions.appendChild(li);
//                     });
//                 });
//         } else {
//             suggestions.innerHTML = '';
//         }
//     });
// });