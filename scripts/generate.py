#!/usr/bin/env python3

import json
import os, shutil, sys
import re
from itertools import groupby
from pathlib import Path
from datetime import date
from string import Template

from pygments.lexer import RegexLexer
from pygments.token import *
from pygments import highlight
from pygments.formatters import HtmlFormatter

import pyproj
#from contextlib import redirect_stdout

class WKTLexer(RegexLexer):
    name = 'wkt'
    aliases = ['wkt']
    filenames = ['*.wkt']

    tokens = {
        'root': [
            (r'^This CRS cannot be written.*', Error),
            (r'\s+', Text),
            (r'[{}\[\]();,-.]+', Punctuation),
            (r'^(PROJCS|GEOGCS|GEOCCS|VERT_CS|COMPD_CS)\b', Generic.Heading),
            (r'^(PROJCRS|GEOGCRS|GEODCRS|VERTCRS|COMPOUNDCRS)\b', Generic.Heading),
            (r'(PROJCS|GEOGCS|GEOCCS|VERT_CS)\b', Keyword.Declaration),
            (r'(PROJCRS|GEOGCRS|GEODCRS|VERTCRS)\b', Keyword.Declaration),
            (r'(PARAMETER|PROJECTION|SPHEROID|DATUM|GEOGCS|AXIS|VERT_DATUM)\b', Keyword),
            (r'(ELLIPSOID)\b', Keyword),
            (r'(METHOD)\b', Keyword),
            (r'(PRIMEM|UNIT|TOWGS84)\b', Keyword.Constant),
            (r'([A-Z]+UNIT)\b', Name.Class),
            (r'(east|west|north|south|up|down|geocentric[XYZ])\b', Literal.String),
            (r'(EAST|WEST|NORTH|SOUTH|UP|DOWN)\b', Literal.String),
            (r'(ORDER|SCOPE|AREA|BBOX)\b', Keyword.Constant),
            (r'(BASEGEOGCRS|CONVERSION|CS|USAGE|VDATUM)\b', Keyword.Declaration),
            (r'([Cc]artesian|[Ee]llipsoidal|[Vv]ertical)\b', Literal.String),
            (r'(AUTHORITY)\b', Name.Builtin),
            (r'(ID)\b', Name.Builtin),
            (r'[$a-zA-Z_][a-zA-Z0-9_]*', Name.Other),
            (r'[0-9][0-9]*\.[0-9]+([eE][0-9]+)?[fd]?', Number.Float),
            (r'0x[0-9a-fA-F]+', Number.Hex),
            (r'[0-9]+', Number.Integer),
            (r'"(\\\\|\\"|[^"])*"', String.Double),
            (r"'(\\\\|\\'|[^'])*'", String.Single),
        ]
    }

def read_file(src_filename):
    with open(src_filename, 'r') as src:
        return src.read()

def read_tmpl(src_filename, dic):
    with open(src_filename, 'r') as src:
        txt = Template(src.read())
        result = txt.substitute(dic)
        return result

def subs(str, mapping):
    return Template(str).substitute(mapping)

def substitute(src_filename, dst_folder, dic):
    Path(dst_folder).mkdir(parents=True, exist_ok=True)
    dst_folder += '/index.html'

    with open(dst_folder, 'w') as dst:
        dst.write(read_tmpl(src_filename, dic))


def dump_f(dst_folder, file, txt):
    Path(dst_folder).mkdir(parents=True, exist_ok=True)
    dst_file = dst_folder + '/' + file

    with open(dst_file, 'w') as dst:
        dst.write(txt)

def dump(dst_folder, txt):
    return dump_f(dst_folder, 'index.html', txt)

def add_frozen_crss(crss):
    parent = Path(__file__).parent.resolve()
    for domain in ['iau2000.json', 'sr-org.json']:
        with open(f'{parent}/{domain}', 'r') as fp:
            dom = json.load(fp)
            crss = [*crss, *dom]
    return crss

def make_crslist(dest_dir):
    dest_file = f'{dest_dir}/crslist.json'

    pyproj.show_versions()

    crs_list = pyproj.database.query_crs_info(allow_deprecated=True)

    def adapt_crs(crs):
        crs = crs._asdict()
        crs['type'] = str(crs['type']).replace('PJType.', '')
        return crs

    crss = sorted(
        [adapt_crs(crs) for crs in crs_list if crs.area_of_use],
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

    crss = add_frozen_crss(crss)

    with open(dest_file, 'w') as fp:
        json.dump(crss, fp, indent=2)

    return crss

def make_mapping(sections, home_dir):
    mapping = {'last_revised': os.getenv('LAST_REVISED', '-missing-'),
               'home_dir': home_dir}
    for sec in ['head', 'leaflet', 'header', 'searchbox', 'navbar', 'footer']:
        mapping[sec] = Template(sections[sec]).substitute({'home_dir': home_dir})
    return mapping

def make_wkts(crs):
    try:
        output_axis_rule = True if crs.is_projected else None
        pretty = crs.to_wkt(version='WKT1_GDAL', pretty=True, output_axis_rule=output_axis_rule)
        ogcwkt = crs.to_wkt(version='WKT1_GDAL', pretty=False, output_axis_rule=output_axis_rule)
    except:
        pretty = 'This CRS cannot be written as WKT1_GDAL'
        ogcwkt = 'This CRS cannot be written as WKT1_GDAL'

    pretty2 = crs.to_wkt(version='WKT2_2019', pretty=True, output_axis_rule=output_axis_rule)
    ogcwkt2 = crs.to_wkt(version='WKT2_2019', pretty=False, output_axis_rule=output_axis_rule)

    syntax_pretty = highlight(pretty, WKTLexer(), HtmlFormatter(cssclass='syntax', nobackground=True))
    syntax_pretty2 = highlight(pretty2, WKTLexer(), HtmlFormatter(cssclass='syntax', nobackground=True))

    return (syntax_pretty, pretty, ogcwkt, syntax_pretty2, pretty2, ogcwkt2)

if __name__ == '__main__':
    dest_dir = os.getenv('DEST_DIR', '.')
    templates = './templates'

    crss = make_crslist(dest_dir)

    # copy some literal files, not modified
    for literal in ['base.js', 'base.css', 'sr_logo.jpg', 'favicon.ico']:
        shutil.copy(f'{templates}/{literal}', dest_dir)

    sections = {
        'head': read_file(f'{templates}/sections/head.tmpl'),
        'leaflet': read_file(f'{templates}/sections/leaflet.tmpl'),
        'header': read_file(f'{templates}/sections/header.tmpl'),
        'searchbox': read_file(f'{templates}/sections/searchbox.tmpl'),
        'navbar': read_file(f'{templates}/sections/navbar.tmpl'),
        'footer': read_file(f'{templates}/sections/footer.tmpl'),
    }

    # footer has some variables, apart from home_dir
    today = date.today().isoformat()
    sections['footer'] = Template(sections['footer']).safe_substitute({
        'proj_version': os.getenv('PROJ_VERSION', '-missing-'),
        'built_date': today,
    })

    authorities = {
        key: len(list(group))
        for key, group in groupby(crss, lambda x: x['auth_name'])
    }
    count_authorities = {
        f'count_{key.lower().replace("-","_")}' : str(value)
        for key, value in authorities.items()
    }

    mapping = make_mapping(sections, '.') | count_authorities
    substitute(f'{templates}/index.tmpl', f'{dest_dir}', mapping)
    mapping = make_mapping(sections, '..')
    substitute(f'{templates}/about.tmpl', f'{dest_dir}/about', mapping)
    substitute(f'{templates}/ref.tmpl', f'{dest_dir}/ref', mapping)

    mapping_ref = make_mapping(sections, '../../..')
    mapping_wkt = make_mapping(sections, '../../../..')
    no_display = 'style="display: none;"'

    count = 0
    total = len(crss)
    sys.stdout.write(f'Processing {total} CRSs:\n')

    for id, c in enumerate(crss):
        count += 1
        if count > 1000:
            break
        if count % int(total/100) == 0 or total == count:
            sys.stdout.write('\r')
            # the exact output you're looking for:
            sys.stdout.write("[%-20s] %d%%" % ('='*int(count/total*20), int(count/total*100)))
            sys.stdout.flush()

        code=c["code"]
        auth_name=c["auth_name"]
        name = c["name"]
        auth_lowercase = auth_name.lower()
        error = ''
        error_style = no_display
        list_style = ''
        crs = None
        if "ogcwkt" in c:
            list_style = no_display
            try:
                crs = pyproj.CRS.from_user_input(c["ogcwkt"])
            except Exception as e:
                print('error with', auth_name, code, name)
                error = str(e).replace(',', ',<wbr>') # to be more readable in html
                error_style = ''
        else:
            crs = pyproj.CRS.from_authority(auth_name=auth_name, code=code)

        if auth_name == "EPSG":
            epsg_scaped_name = re.sub(r'[^0-9a-zA-Z]+', '-', name);
            epsg_style = ''
        else:
            epsg_scaped_name = ''
            epsg_style = no_display
        aou = c.get("area_of_use")
        bounds = ', '.join([str(x) for x in aou[:4]]) if aou else 'Unknown'
        bounds_json = '{{"west_longitude": {}, "south_latitude": {}, "east_longitude": {}, "north_latitude": {} }}'.format(*aou) if aou else "Unknonw"
        full_name = lambda c: f'{c["auth_name"]}:{c["code"]} : {c["name"]}'
        url = lambda c: f'../../../ref/{c["auth_name"].lower()}/{c["code"]}'

        mapping = mapping_ref | {
               'authority': auth_name,
               'code': code,
               'name': name,
               'area_name': aou[4] if aou else 'Unknown',
               'epsg_scaped_name': epsg_scaped_name,
               'epsg_style': epsg_style,
               'deprecated_style': '' if c.get("deprecated", '') else no_display,
               'crs_type': c.get("type", '--'),
               'bounds': bounds,
               'bounds_map': bounds if aou else '-180, -90, 180, 90',
               'scope': crs.scope if crs else '--',
               'prev_full_name': full_name(crss[id-1]),
               'prev_url': url(crss[id-1]),
               'next_full_name': full_name(crss[(id+1)%len(crss)]),
               'next_url': url(crss[(id+1)%len(crss)]),
               'error': error,
               'error_style': error_style,
               'list_style': list_style,
        }
        substitute(f'{templates}/crs.tmpl', f'{dest_dir}/ref/{auth_lowercase}/{code}', mapping)

        dir = f'{dest_dir}/ref/{auth_lowercase}/{code}'
        if not crs:
            ogcwkt = c.get("ogcwkt")
            dump_f(f'{dir}', 'ogcwkt.txt', ogcwkt)
            dump(f'{dir}/ogcwkt', ogcwkt) # backwards compatible
        else:
            syntax_pretty, pretty, ogcwkt, syntax_pretty2, pretty2, ogcwkt2 = make_wkts(crs)

            mapping = mapping_wkt | {
                'authority': auth_name,
                'code': code,
                'syntax_html': syntax_pretty,
                'syntax_html_2': syntax_pretty2,
            }

            substitute(f'{templates}/html.tmpl', f'{dir}/html', mapping)
            dump_f(f'{dir}', 'prettywkt.txt', pretty)
            dump_f(f'{dir}', 'ogcwkt.txt', ogcwkt)
            dump(f'{dir}/prettywkt', pretty) # backwards compatible
            dump(f'{dir}/ogcwkt', ogcwkt) # backwards compatible


            substitute(f'{templates}/html.tmpl', f'{dest_dir}/ref/{auth_lowercase}/{code}/htmlwkt2', mapping)
            dump_f(f'{dest_dir}/ref/{auth_lowercase}/{code}', 'prettywkt2.txt', pretty2)
            dump_f(f'{dest_dir}/ref/{auth_lowercase}/{code}', 'ogcwkt2.txt', ogcwkt2)

            dump_f(f'{dest_dir}/ref/{auth_lowercase}/{code}', 'bounds.json', bounds_json)

            try:
                esri = crs.to_wkt(version='WKT1_ESRI')
            except:
                esri = 'This CRS cannot be written as WKT1_ESRI'
            dump_f(f'{dest_dir}/ref/{auth_lowercase}/{code}', 'esriwkt.txt', esri)
            dump(f'{dest_dir}/ref/{auth_lowercase}/{code}/esriwkt', esri)  # backwards compatible

            projjson = crs.to_json(pretty=True)
            dump_f(f'{dest_dir}/ref/{auth_lowercase}/{code}', 'projjson.json', projjson)

            try:
                proj4 = crs.to_proj4()
            except:
                proj4 = ''
            dump(f'{dest_dir}/ref/{auth_lowercase}/{code}/proj4', proj4)

    exit(0)