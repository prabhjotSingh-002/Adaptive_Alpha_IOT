"""Plot validated comparison summaries; final metrics belong to metrics.py."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    parser=argparse.ArgumentParser();parser.add_argument('runs',nargs='+',type=Path);parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    if len(args.runs) not in (2,4): raise ValueError('Expected two diagnostic/AES arms or four static protected arms')
    manifests=[json.loads((p/'manifest.json').read_text()) for p in args.runs]
    summaries=[json.loads((p/'summary.json').read_text()) for p in args.runs]
    labels=[m['mode'] for m in manifests]
    if labels not in (['B1','B4'],['N0-single','N0-batch'],['B1','B2','B4','B5']): raise ValueError('Unsupported control group')
    if any(m['status']!='passed' for m in manifests) or any('test' in s['security'] for s in summaries): raise ValueError('Invalid/test-only run')
    comparison=json.loads((args.runs[1]/'paired-comparison.json').read_text())
    if not comparison.get('comparison_eligible',comparison.get('generation_identical')): raise ValueError('Ineligible comparison')
    project=Path(__file__).resolve().parents[1]
    if [(project/p).resolve() for p in comparison['runs']] != [p.resolve() for p in args.runs]: raise ValueError('Group identity mismatch')
    keys=['packets_submitted','reading_pdr','p95_delay_ms'];titles=['UDP data submissions','Unique reading PDR','p95 delay (ms)']
    if all(s.get('energy_per_delivered_reading_nj') is not None for s in summaries):
        keys+=['energy_per_delivered_reading_nj'];titles+=['Model energy / delivered reading (nJ)']
    fig,axes=plt.subplots(1,len(keys),figsize=(4*len(keys),3.5))
    for ax,key,title in zip(axes,keys,titles):
        ax.bar(labels,[s[key] for s in summaries]);ax.set_title(title,fontsize=9)
    axes[1].set_ylim(0,1.05)
    fig.suptitle('Engineering pilot — '+comparison.get('timing_contract','exact legacy generation'),fontsize=10)
    fig.tight_layout();args.output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(args.output);plt.close(fig)
    args.output.with_suffix('.sources.json').write_text(json.dumps({'runs':comparison['runs'],'metrics':keys,'comparison':comparison},indent=2)+'\n')
if __name__=='__main__': main()
