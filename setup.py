#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parent
# Quote Desktop Entry Exec arguments independently of shell syntax.
def quote(value):
    value=value.replace("%","%%")
    for char in [chr(92),chr(34),chr(96),"$"]:
        value=value.replace(char,chr(92)+char)
    return chr(34)+value+chr(34)
launcher=root/"会社の教育ノート.desktop"
launcher.write_text("[Desktop Entry]\nVersion=1.0\nType=Application\nName=会社の教育ノート\nComment=教育・応答チャットを開く\nExec=/usr/bin/python3 "+quote(str(root/"launch.py"))+"\nIcon=accessories-text-editor\nTerminal=true\nCategories=Office;Education;\nStartupNotify=false\n",encoding="utf-8")
launcher.chmod(0o755)
print("ランチャーを作成しました:",launcher)
print("ダブルクリックで起動できます。デスクトップへコピーしても使えます。")
