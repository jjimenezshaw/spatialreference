function init_map(area_of_use) {
    let map = L.map('map').setView([0, 0], 1);
    let osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18,
    }).addTo(map);
    let rect = makeRectangle(area_of_use, 'green').addTo(map);
    map.fitBounds(rect.getBounds());
}

function makeRectangle (area_of_use, color) {
    let bounds = null;

    let off0 = 0, off2 = 0;
    if (area_of_use[0] < area_of_use[2]) {
    } else if (Math.abs(area_of_use[0]) < Math.abs(area_of_use[2])) {
        off2 = 360
    } else {
        off0 = 360
    }
    bounds = [[area_of_use[1], area_of_use[0]-off0], [area_of_use[3], area_of_use[2]+off2]];

    return L.rectangle(bounds, {color: color});
}