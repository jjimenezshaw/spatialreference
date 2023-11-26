#!/usr/bin/env python

import json
import os, shutil

import pyproj
from contextlib import redirect_stdout

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

    for literal in ['base.js', 'base.css']:
        shutil.copy(templates + '/' + literal, dest_dir)

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
