#!/usr/bin/env bash
# list a folder of a public GitHub repo: ghls.sh owner/repo path
curl -s -m 25 -H 'User-Agent: fonts-check' "https://api.github.com/repos/$1/contents/$2" | python3 -c "import sys,json; d=json.load(sys.stdin); print([x['name'] for x in d] if isinstance(d,list) else str(d)[:200])"
