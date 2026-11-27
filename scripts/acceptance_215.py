"""Local acceptance evidence collector; never grants human approval."""
import argparse
import datetime
import json
import pathlib
import subprocess
import sys

CASES = (
    'Synthetic demo and authorized fixture upload',
    'Search, filters and evidence inspection',
    'Download JSON, manifest and triage CSV; verify integrity',
    'Invalid CSV and oversized upload rejected',
    'Missing or altered manifest fails closed',
    'Invalid Host, Origin and CSRF rejected',
    'Incomplete upload timeout and subsequent recovery',
    'Partial discard revokes links; authenticated retry',
    'Loopback, cache headers, token exposure and concurrency review',
)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=pathlib.Path, required=True)
    p.add_argument('--expected-head', required=True)
    args = p.parse_args()
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    if head != args.expected_head:
        p.error('HEAD differs from the reviewed revision')
    if subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip():
        p.error('Use a clean checkout; write evidence outside the repository')
    result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], capture_output=True, text=True)
    report = {'issue': 215, 'head': head, 'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'automated_exit_code': result.returncode, 'automated_log': result.stdout + result.stderr, 'manual_cases': [{'case': c, 'status': 'NOT_RUN', 'evidence': None} for c in CASES], 'human_acceptance': 'NOT_RECORDED'}
    with args.output.open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print('Evidence template saved. Manual acceptance remains pending.')
    return result.returncode

if __name__ == '__main__':
    sys.exit(main())
