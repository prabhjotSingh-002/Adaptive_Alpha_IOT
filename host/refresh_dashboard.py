"""Promote a verified result snapshot without changing any experimental artifact."""
import argparse
import datetime
import json
from pathlib import Path
from campaign import atomic_json
from latest_results import ROOT,build_catalog,sha

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validation-dir',default='results/phase_05/mechanism_17nov/validation-v2')
    args=parser.parse_args();catalog=build_catalog(args.validation_dir)
    directory=ROOT/'results/dashboard';directory.mkdir(exist_ok=True)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path=directory/f'catalog-{stamp}.json';atomic_json(path,catalog)
    pointer=directory/'current.json';previous=json.loads(pointer.read_text()) if pointer.exists() else None
    selection={'catalog':str(path.relative_to(ROOT)),'catalog_sha256':sha(path)}
    atomic_json(directory/f'promotion-{stamp}.json',{'previous':previous,'selected':selection,'verified_before_promotion':True})
    atomic_json(pointer,selection)
    print('Dashboard selects',len(catalog['records']),'verified runs:',selection['catalog'])
if __name__=='__main__':main()
