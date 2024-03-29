#!/usr/bin/env python3

import argparse
import json
import os
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--manifest', '-m', type=str,
        default='.configs/manifest.js',
        help='Manifesto file in grok\'s format plus site field.')
parser.add_argument('lists', type=str, nargs='+',
        help='Name of the mailing list.')

args = parser.parse_args()
manifest_file = args.manifest
mail_lists = args.lists

with open(manifest_file) as f:
    manifest = json.load(f)

site = manifest['site']
for path in manifest:
    for mlist in mail_lists:
        if path.startswith('/%s/' % mlist):
            print('%s%s' % (site, path))
            git_url = '%s%s' % (site, path)
            local_path = '.mails%s' % path
            if not os.path.isdir(local_path):
                cmd = 'git clone --mirror %s %s' % (git_url, local_path)
            else:
                cmd = 'git --git-dir=%s remote update' % local_path
            subprocess.call(cmd.split())
