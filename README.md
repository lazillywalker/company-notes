# 会社の教育ノート / Company Notes

ローカルAIを入れたけれど、次に何を試したらよいか分からない方へ。
会社やお店の情報を教材として登録し、質問・回答・訂正を試せる、無料配布の研究用アプリです。

## できること

- 教育チャットと応答チャットを分けて利用
- 日本語・英語の教材と回答
- JSON入力、5分類の教材、承認と取下げ
- 店舗ごとの曜日別営業時間
- 有効期間・公開範囲を考慮した教材検索
- 回答の参照元表示、応答ログの閲覧・保存・削除
- ランチャー、架空のサンプル教材5件、確認用の質問集

モデル自体を追加学習するものではありません。登録した教材を検索し、その内容を参考情報としてモデルへ渡します。

## ダウンロード

このリポジトリの Releases から `company-notes-distribution.zip` をダウンロードしてください。GitHubが自動生成するSource codeではなく、配布用ZIPを選んでください。

## 必要環境

Linux Mint、Python 3.10以上、ブラウザー、ローカルOllama、導入済みの `qwen3:4b`。
Ollama・モデル本体は同梱していません。別OSでの動作は未確認です。

## 最初の実験

1. ZIPを展開し、company-notesフォルダー内で端末を開きます。
2. `python3 setup.py` を実行します。
3. 作成された「会社の教育ノート.desktop」をダブルクリックします。
4. 教育画面の「JSONから教材を読み込む」からsamples内のJSONを1件ずつ読み込みます。
5. 状態を「承認」にして、確認後に保存します。
6. 「本店は水曜日に営業していますか？」と質問します。
7. 回答と参照元を確認し、応答ログを保存します。

サンプルの売出し期間は2026年11月7〜15日です。期間外の実験では、日付欄と日英本文の日付を合わせて変更してください。

## 保存される情報

教材と質問・回答のログは、アプリのフォルダー内に保存されます。配布ZIPに利用者の会話ログは含めていません。ログを共有する際は内容を確認してください。

## 現段階の制約

研究用の初期版です。回答の正確性は保証されません。参照元を確認しながら利用してください。利用者認証・役割別の権限制御はありません。意味検索、翻訳の自動同期、価格の自動計算は未実装です。

## English

Company Notes is a local research app for experimenting with approved knowledge and a local language model. It includes separate teaching and answering screens, Japanese/English notes, weekly store schedules, reference snapshots, response logs and five fictional sample files. It retrieves notes rather than fine-tuning model weights. Linux Mint and an existing local Ollama installation with qwen3:4b are required.

## License

MIT License. 利用・改変・再配布・商用利用が可能です。著作権表示とライセンス文を保持してください。Ollamaとモデルにはそれぞれの利用条件が適用されます。
