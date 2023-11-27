#!/usr/bin/env python

import json
import os, shutil
from pathlib import Path
from string import Template 

import pyproj
#from contextlib import redirect_stdout

def substitute(src_filename, dst_folder, dic):
    Path(dst_folder).mkdir(parents=True, exist_ok=True)
    dst_folder += '/index.html'
    
    with open(src_filename, 'r') as src, open(dst_folder, 'w') as dst:
        txt = Template(src.read())
        result = txt.substitute(dic)
        dst.write(result)

if __name__ == '__main__':
    dest_dir = os.getenv('DEST_DIR', '.')
    dest_file = f'{dest_dir}/crslist.json'
    templates = './templates'

    pyproj_versions = pyproj.show_versions()

    crs_list = pyproj.database.query_crs_info(allow_deprecated=True)

    crss = sorted(
        [crs._asdict() for crs in crs_list if crs.area_of_use],
        key=lambda d: d['auth_name'] + d['code'].zfill(7)
    )

    print('\nAnalysis of duplicated codes')
    codes = [d['auth_name'] + ':' + d['code'] for d in crss]
    unique = []
    for code in codes:
        if code in unique:
            print(code + ' is duplicated')
        else:
            unique.append(code)

    with open(dest_file, 'w') as fp:
        json.dump(crss, fp, indent=2, default=lambda o: str(o).replace('PJType.', ''))

    shutil.copy(f'{templates}/sr_logo.jpg', dest_dir)
    for literal in ['base.js', 'base.css']:
        shutil.copy(f'{templates}/{literal}', dest_dir)
    
    dic = {'version': os.getenv('PROJ_VERSION', '.'),
           'home_dir': '.'}
    substitute(f'{templates}/index.tmpl', f'{dest_dir}', dic)
    dic['home_dir'] = '..'
    substitute(f'{templates}/about.tmpl', f'{dest_dir}/about', dic)
    substitute(f'{templates}/ref.tmpl', f'{dest_dir}/ref', dic)

    exit(0)

    types = ({'path': 'wkt1', 'version': 'WKT1_GDAL'},
             {'path': 'wkt2', 'version': 'WKT2_2019'})

    urls = []
    for c in crss:
        crs = pyproj.CRS.from_authority(auth_name=c["auth_name"], code=c["code"])
        for t in types:
            url = f'{t["path"]}/{c["auth_name"]}/{c["code"]}.txt'
            if not url in urls:
                urls.append(url)
            wtk_file = f'{dest_dir}/{url}'
            if not os.path.exists(os.path.dirname(wtk_file)):
                os.makedirs(os.path.dirname(wtk_file))

            try:
                output_axis_rule = True if crs.is_projected else None
                wkt = crs.to_wkt(version=t["version"], pretty=True, output_axis_rule=output_axis_rule)
            except:
                wkt = None
            if not wkt:
                type = str(c["type"]).replace('PJType.', '')
                wkt = (f'Error: {c["auth_name"]}:{c["code"]} cannot be written as {t["version"]}\n'
                        f' type: {type}\n'
                        f' name: {c["name"]}')
            with open(wtk_file, 'w') as fp:
                fp.write(wkt)
                fp.write('\n')
