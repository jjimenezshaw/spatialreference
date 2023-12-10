#!/usr/bin/env python3

import requests
import json
import os, shutil, sys
import re
from string import Template

if __name__ == '__main__':

    r = requests.get('https://spatialreference.org/ref/sr-org/?page=1')
    print('asdf', r)

    exit(0)