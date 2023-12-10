#!/usr/bin/env python3

import requests
import json
import html
import re

if __name__ == '__main__':

    for domain_upper_case in ['IAU2000', 'SR-ORG']:
        res_dict = []

        domain = domain_upper_case.lower()
        for page in range(1,70): # 70 is a safe number. Both are below 60 pages
            page_url = f'https://spatialreference.org/ref/{domain}/?page={page}'
            r = requests.get(page_url)
            if not r.ok:
                print("Error! cannot get ", page_url)
                continue
            pattern = re.compile(f'<li>.*?\"/ref/{domain}/(.*?)/\">.*?</a>: (.*?)</li>')
            all = pattern.findall(r.text)
            print(f'in page {page} found {len(all)} entries')
            if len(all) == 0:
                print(f'Done! Last page was #{page-1}')
                break
            for code, name in all:
                name = html.unescape(name)
                print(code, name)
                d = {'auth_name' : domain_upper_case, 'code': str(code), 'name': name}
                url = f'https://spatialreference.org/ref/{domain}/{code}/ogcwkt/'
                r = requests.get(url)
                if r.ok:
                    d['ogcwkt'] = r.text
                res_dict.append(d)

        with open(f'{domain}.json', 'w') as fp:
            json.dump(res_dict, fp, indent=2)

    exit(0)