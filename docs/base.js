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

function generate_entries(data, home_dir, from, number, container) {
    for (let i = from; i < from + number; i++) {
        if (i >= data.length)
            break;
        const crs = data[i]
        let li = document.createElement('li');
        let a = document.createElement('a');
        a.href = `${home_dir}/ref/${crs.auth_name.toLowerCase()}/${crs.code}/`;
        a.innerText = `${crs.auth_name}:${crs.code}`;
        li.appendChild(a);
        name_broken = crs.name.replaceAll('_', '<wbr />_')
        li.innerHTML += `: ${name_broken}`;
        container.appendChild(li);
    }
}

function update_pages_links(page, search, max_pages) {
    let s = search ? `&search=${search}` : '';
    function doit (page_number, class_name, show) {
        let prev = document.querySelectorAll(class_name);
        Array.from(prev).forEach(e => {
            if (!show) {
                e.classList.add('hidden');
            } else {
                e.classList.remove('hidden');
                e.href = `?page=${page_number}${s}`;
            }
        });
    }
    page = Number(page)
    doit(page - 1, '.prev_page', page > 1)
    doit(page + 1, '.next_page', page < max_pages)
    Array.from(document.querySelectorAll('.next_page')).forEach(e => e.href = `?page=${page + 1}${s}`);
}

function paramsToDic(location) {
    const url = new URL(location);
    let dic = {};
    for (let k of url.searchParams.keys()) {
        dic[k] = url.searchParams.get(k);
    }
    return dic;
}

function filter_data(data, search) {
    if (!search || !search.trim()) {
        return data;
    }
    let s = search.toLowerCase().split(' ');
    let r = data.filter(d => {
        let name = d.name.toLowerCase();
        let valid = s.reduce((accum, current) => accum && name.includes(current), true);

        if (!isNaN(s[0]) && d.code === s[0]) {
            valid = true
        }
        return valid;
    });
    return r;
}

function init_ref(home_dir) {
    fetch(home_dir + '/crslist.json', {
        method: "GET",
    })
    .then(response => response.json())
    .then(data => {
        let entries_per_page = 50;
        let params = paramsToDic(window.location);
        let page = params.page || 1;
        data = filter_data(data, params.search);
        document.querySelector('#found').innerText = data.length;
        if(params.search && params.search.trim()) {
            document.querySelector('#searched_text').innerHTML =
            ` from search: <pre style="display: inline;">${params.search}</pre>`;
        }
        let container = document.querySelector('#list1 ul');
        generate_entries(data, home_dir, (page - 1) * entries_per_page, entries_per_page/2, container);
        container = document.querySelector('#list2 ul');
        generate_entries(data, home_dir, (page - 0.5) * entries_per_page, entries_per_page/2, container);
        update_pages_links(page, params.search, Math.ceil(data.length / entries_per_page))
    });
}

function download_prj(name, file) {
    if (name && name !=='') {
      var link = document.createElement('a');
      link.download = name;
      link.href = file;  
      link.click();
    }
  }