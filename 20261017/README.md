# 42 Tokyo AIエージェント開発ハンズオン（2026年10月17日）

ハンズオンで使うリポジトリです。QAを登録して検索し（S5）、その検索をツールにしてエージェントにつなぎます（S6）。回答はファイルに残せます（S7、S8）。

## 当日の流れ

| 時刻 | ステップ | すること |
| :-- | :-- | :-- |
| 14:00 | 環境準備 | リポジトリを取得してイメージをビルドし、「こんにちは」が返るのを確かめる |
| 14:20 | S1 オープニング | チームで自己紹介 |
| 14:30 | S2 お題とデモ | 42 Tokyoをお客さんに見立て、42 Tokyoの魅力を答える営業エージェントを作る、というお題を聞く |
| 14:40 | S3 仕組みの説明 | `docs/shikumi.html` をブラウザで開き、LLM、RAG、ベクトル検索、ツール呼び出しの話を聞く |
| 14:55 | S4 QAを書く | `data/my_qa.csv` にある全員共通の3問に答えを書き、自由な質問を足して5〜10問にする |
| 15:15 | S5 登録して検索する | QAを登録して検索する。途中で固有QAを足す |
| 15:45 | 休憩 | |
| 15:55 | S6 ツールを作る | 検索をツールにして、エージェントにつなぐ。ADKのドキュメント: [Function tools](https://adk.dev/tools-custom/function-tools/) |
| 16:55 | 休憩 | |
| 17:05 | S7 判定する | 同じ質問への回答をチームで見せ合い、公式サイトに載せてよいかを話し合って判定する |
| 17:20 | S8 もう一度聞く | 同じ質問をもう一度聞き、回答を見比べる |
| 17:35 | S9 総括 | 「次に何かを作るとき、最初に誰と何を決めるか」を1文、チームで言う |
| 17:45 | S10 交流 | 後片付けをして、社員と話す。19:00まで |

S3の説明ページは、コンテナの外で `xdg-open docs/shikumi.html` を実行するか、ファイルをブラウザにドラッグして開きます。

## 準備

```bash
git clone https://github.com/laboroai/LaboroPublic42Events.git
cd LaboroPublic42Events/20261017
cp .env.example .env
nano .env              # OPENAI_API_KEY= のあとに、Discordで配るキーを貼る
docker compose build   # 5〜15分かかる
```

キーがなくても `.env` に `HANDSON_MOCK=1` と書けば、APIを呼ばずに動きを試せます。

イメージは教室PC（x86_64）向けに作ります。Apple SiliconのMacで試すときは、`HANDSON_PLATFORM=linux/arm64 docker compose build` で作ってください。

## コマンド

どれも `docker compose run --rm app` の後ろに付けて実行します。`docker compose run --rm app bash` でコンテナに入れば、付けなくてもかまいません。

| ステップ | コマンド | すること |
| :-- | :-- | :-- |
| 環境準備 | `python ask.py "こんにちは"` | エージェントが返事をするかを確かめる |
| S5 | `python register.py` | `data/` のCSVをすべて登録する。ファイルごとの件数が出る |
| S5 | `python search.py "質問"` | 登録したQAを検索し、上位3件を点数とファイル名つきで出す |
| S5 | `cp ops/sample_secret_qa.csv data/secret_qa.csv` | 固有QAを足す（コンテナの外で実行する）。足したら `register.py` をやり直す |
| S6 | `python ask.py "質問"` | エージェントに1問答えさせる。ツールがつながったかは、`secret_qa.csv` にある質問で確かめる。呼ばれたツールと、検索で引けたQAの点数とファイル名も出る |
| S7、S8 | `python ask.py --save "質問"` | 回答を `out/answers.jsonl` に追記する |

キーが設定されていないときや、QAを登録する前に検索したときは、次に何をすればよいかを表示して止まります。CSVを書き直したら、もう一度 `python register.py` を実行してください。

## ファイル

| パス | 中身 | あなたがすること |
| :-- | :-- | :-- |
| `my_agent/agent.py` | あなたのエージェント。今は返事をするだけで、QAは見ていない | **S6で作り変える**（TODOを参照） |
| `data/my_qa.csv` | あなたが書く42の魅力QA | **書く** |
| `data/shakaijin_qa.csv` | 社会人向けのメリットのQA（全員共通） | 触らない |
| `data/secret_qa.csv` | 固有QA | S5でコピーして作る |
| `ops/sample_secret_qa.csv` | 固有QAのもと | S5で `data/secret_qa.csv` にコピーする |
| `register.py`、`search.py`、`ask.py` | 上のコマンド | 使う |
| `lib/rag.py` | QAの登録と検索。S6では `search(query, k)` を使う | 触らない |
| `lib/model.py`、`lib/runner.py`、`lib/cli.py` | モデルの呼び出しと、エージェントの実行 | 触らない |
| `claude-settings.example.json` | Claude Code の設定のひな形。当日は `settings.json` として配る | 使う |

QAの書き方は [data/README.md](data/README.md) にあります。

## 後片付け（S10）

コンテナが作ったファイルは、教室PCのアカウントでは消せないので、先にコンテナで消します。

```bash
docker compose run --rm app sh -c 'rm -rf out .pytest_cache .mypy_cache && find . -name __pycache__ -prune -exec rm -rf {} +'
docker compose down --rmi all
cd ../.. && rm -rf LaboroPublic42Events
```

書いたQA、保存した回答、キーを書いた `.env`、ビルドしたイメージがすべて消えます。

## 動作確認

キーがなくても、次のコマンドで一通りの動きを確かめられます。

```bash
docker compose run --rm -e HANDSON_MOCK=1 app pytest -q
```
