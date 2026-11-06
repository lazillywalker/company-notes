#!/usr/bin/env python3
"""Start Company Notes or open the existing local instance."""
import json
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent
URL = 'http://127.0.0.1:8766'

def main():
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(URL + '/api/state', timeout=3) as response:
            state = json.load(response)
        if isinstance(state, dict) and isinstance(state.get('notes'), list) and 'categories' in state and 'token' in state:
            webbrowser.open(URL)
            return 0
        raise RuntimeError('ポート8766を別のアプリが使用しています。 / Port 8766 is in use.')
    except urllib.error.URLError as error:
        if isinstance(error, urllib.error.HTTPError):
            print('ポート8766を別のアプリが使用しています。 / Port 8766 is in use.')
            input('Enterで閉じる / Press Enter to close')
            return 1
    except (ValueError, RuntimeError) as error:
        print(error)
        input('Enterで閉じる / Press Enter to close')
        return 1
    print('会社の教育ノートを起動します。終了はこの端末で Ctrl+C。', flush=True)
    try:
        result = subprocess.run([sys.executable, str(ROOT/'gui.py'), '--open-browser'], cwd=ROOT)
        if result.returncode:
            input('起動できませんでした。上の表示を確認してください。Enterで閉じます。')
        return result.returncode
    except KeyboardInterrupt:
        return 0

if __name__ == '__main__':
    sys.exit(main())
