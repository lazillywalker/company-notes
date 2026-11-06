"""Versioned teaching material: many question variants, one answer."""
import json
import re
import secrets
import threading
import time
import unicodedata

SCHEMA = '''
CREATE TABLE IF NOT EXISTS materials(
  id INTEGER PRIMARY KEY, created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS material_revisions(
  id INTEGER PRIMARY KEY,
  material_id INTEGER NOT NULL REFERENCES materials(id),
  created TEXT NOT NULL, title TEXT NOT NULL, answer TEXT NOT NULL,
  questions TEXT NOT NULL, source TEXT NOT NULL, reviewer TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('approved','pending','rejected')));
CREATE INDEX IF NOT EXISTS material_revision_item ON material_revisions(material_id,id);
'''


def normalized(text):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', text).casefold())


def text(value, name, maximum, required=True):
    if not isinstance(value, str):
        raise ValueError(f'{name}は文字列で指定してください')
    value = value.strip()
    if (required and not value) or len(value) > maximum:
        raise ValueError(f'{name}は{1 if required else 0}〜{maximum}文字にしてください')
    return value


def validate(items):
    if not isinstance(items, list) or not 1 <= len(items) <= 50:
        raise ValueError('教材は1〜50件のJSON配列で指定してください')
    cleaned, all_questions = [], {}
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict) or set(item) - {'title', 'answer', 'questions', 'source'}:
            raise ValueError(f'教材{index}: 項目はtitle・answer・questions・sourceだけを使ってください')
        title = text(item.get('title'), '教材名', 150)
        answer = text(item.get('answer'), '正解', 3000)
        if re.search(r'</?think\b', answer, re.IGNORECASE):
            raise ValueError('正解に思考タグを入れないでください')
        questions = item.get('questions')
        if not isinstance(questions, list) or not 1 <= len(questions) <= 100:
            raise ValueError(f'{title}: 言い回しは1〜100件にしてください')
        unique, seen = [], set()
        for value in questions:
            question = text(value, '言い回し', 1000)
            key = normalized(question)
            if not key:
                raise ValueError('言い回しは空にできません')
            if key in all_questions and all_questions[key] != normalized(answer):
                raise ValueError(f'同じ言い回しに異なる正解があります: {question[:80]}')
            all_questions[key] = normalized(answer)
            if key not in seen:
                unique.append(question)
                seen.add(key)
        cleaned.append({'title': title, 'answer': answer, 'questions': unique,
                        'source': text(item.get('source', ''), '根拠・出典', 500, required=False)})
    if sum(len(item['questions']) for item in cleaned) > 500:
        raise ValueError('一度の取り込みは言い回し合計500件までです')
    return cleaned


def latest(db):
    return db.execute('''SELECT * FROM material_revisions r
      WHERE r.id=(SELECT MAX(id) FROM material_revisions WHERE material_id=r.material_id)
      ORDER BY r.material_id DESC''').fetchall()


def save(db, items, status, reviewer, created, material_id=None, expected_revision=None):
    """Caller owns transaction. Append a revision; never overwrite earlier teaching."""
    items = validate(items)
    reviewer = text(reviewer, '承認者', 100)
    if status not in ('approved', 'pending', 'rejected'):
        raise ValueError('承認状態が不正です')
    if material_id is not None:
        row = db.execute('SELECT MAX(id) FROM material_revisions WHERE material_id=?',
                         (material_id,)).fetchone()
        if len(items) != 1 or row[0] is None or row[0] != expected_revision:
            raise ValueError('教材が更新されています。再読み込みして編集し直してください')
    # Conflicting approved materials require a person to resolve them first.
    if status == 'approved':
        existing = {}
        for row in latest(db):
            if row['status'] == 'approved' and row['material_id'] != material_id:
                for question in json.loads(row['questions']):
                    existing[normalized(question)] = normalized(row['answer'])
        for item in items:
            for question in item['questions']:
                if normalized(question) in existing and existing[normalized(question)] != normalized(item['answer']):
                    raise ValueError('既存の承認済み教材と正解が衝突しています。既存教材を編集するか保留で登録してください')
    ids = []
    for item in items:
        key = material_id
        if key is None:
            key = db.execute('INSERT INTO materials(created) VALUES(?)', (created,)).lastrowid
        db.execute('''INSERT INTO material_revisions
          (material_id,created,title,answer,questions,source,reviewer,status) VALUES(?,?,?,?,?,?,?,?)''',
          (key, created, item['title'], item['answer'], json.dumps(item['questions'], ensure_ascii=False),
           item['source'], reviewer, status))
        ids.append(key)
    return ids


def candidates(db):
    for row in latest(db):
        if row['status'] == 'approved':
            yield dict(row, variants=json.loads(row['questions']))


def export_records(db):
    for row in candidates(db):
        for question in row['variants']:
            yield {'messages': [{'role': 'user', 'content': question},
                                {'role': 'assistant', 'content': row['answer']}],
                   'provenance': {'material_id': row['material_id'], 'material_revision_id': row['id'],
                                  'reviewer': row['reviewer'], 'approved_at': row['created'],
                                  'source': row['source']}}


class Drafts:
    def __init__(self):
        self.lock = threading.Lock()
        self.entries = {}

    def prepare(self, items, material_id=None, expected_revision=None):
        items = validate(items)
        with self.lock:
            self.entries = {k: v for k, v in self.entries.items() if time.monotonic() - v['time'] < 1800}
            if len(self.entries) >= 20:
                raise ValueError('確認待ちの取り込みが多すぎます。登録するか、30分後にやり直してください')
            key = secrets.token_hex(24)
            self.entries[key] = {'items': items, 'material_id': material_id,
                                 'expected_revision': expected_revision, 'time': time.monotonic()}
            return key

    def get(self, key):
        draft = self.entries.get(key)
        if draft is None or time.monotonic() - draft['time'] >= 1800:
            raise ValueError('確認画面の期限が切れました。取り込みをやり直してください')
        return draft

    def commit(self, db, key, status, reviewer, created):
        with self.lock:
            draft = self.get(key)
            if 'saved' in draft:
                return draft['saved']
            with db:
                db.execute('BEGIN IMMEDIATE')
                ids = save(db, draft['items'], status, reviewer, created,
                           draft['material_id'], draft['expected_revision'])
            draft['saved'] = ids
            return ids
