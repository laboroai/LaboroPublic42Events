# タイムスケジュール

2026年10月17日（土）、42 Tokyo AIエージェント開発ハンズオン。コマンドは、どれもリポジトリの `20261017/` で実行します。`python` で始まるコマンドは、`docker compose run --rm app` の後ろに付けます。

| 時刻 | ステップ | すること |
| :-- | :-- | :-- |
| 14:00〜14:20 | 環境準備 | リポジトリを取得してビルドし、エージェントが返事をするのを確かめる |
| 14:20〜14:30 | S1 オープニング | チームで自己紹介する |
| 14:30〜14:40 | S2 お題とデモ | 42 Tokyoをお客さんに見立て、42 Tokyoの魅力を答える営業エージェントを作る、というお題を聞く |
| 14:40〜14:55 | S3 仕組みの説明 | 説明ページを開き、LLM、RAG、ベクトル検索、ツール呼び出しの話を聞く |
| 14:55〜15:15 | S4 QAを書く | 42の魅力QAを書く |
| 15:15〜15:45 | S5 登録して検索する | QAを登録して検索する。途中で固有QAを足す |
| 15:45〜15:55 | 休憩 | |
| 15:55〜16:55 | S6 ツールを作る | 検索をツールにして、エージェントにつなぐ |
| 16:55〜17:10 | S7 判定する | 同じ質問への回答をチームで見せ合い、公式サイトに載せてよいかを話し合う |
| 17:10〜17:25 | S8 再度同じ質問をエージェントに聞いてみる | 同じ質問をもう一度聞き、前の回答と見比べる |
| 17:25〜17:35 | S9 総括 | 「次に何かを作るとき、最初に誰と何を決めるか」を1文、チームで言う |
| 17:35〜19:00 | S10 交流 | 後片付けをして、社員と話す |

## ステップごとのコマンド

### 環境準備（14:00〜14:20）

Discordに貼られるコマンドとキーを使います。ビルドには5〜15分かかります。

```bash
git clone https://github.com/laboroai/LaboroPublic42Events.git
cd LaboroPublic42Events/20261017
cp .env.example .env
nano .env              # OPENAI_API_KEY= のあとにキーを貼る。Ctrl+O、Enter で保存、Ctrl+X で閉じる
docker compose build
docker compose run --rm app python ask.py "こんにちは"
```

最後に返事が返れば準備完了です。

### S3 仕組みの説明（14:40〜14:55）

```bash
xdg-open docs/shikumi.html
```

ページの中の「ためしてみる」を、話を聞きながら押してみてください。

### S4 QAを書く（14:55〜15:15）

`data/my_qa.csv` に、全員共通の3問が入っています。まず3問の `,` のあとに自分の答えを書き、そのあと自由な質問と答えを足して、合わせて5〜10問にします。書き方は [data/README.md](../data/README.md) にあります。

1. 公式サイトには載っていない、42 Tokyoの魅力は何ですか？
2. 正直なところ、42 Tokyoの大変なところは何ですか？
3. プログラミング未経験でも、ついていけますか？

個人情報や、ほかの人の名前、勤め先の名前は書かないでください。QAは外部のAIサービスに送られます。

### S5 登録して検索する（15:15〜15:45）

```bash
docker compose run --rm app python register.py
docker compose run --rm app python search.py "質問"
```

どのQAが何点で返るか、言い回しを変えても引けるかを試します。15:25ごろ、固有QAを足します。

```bash
cp ops/sample_secret_qa.csv data/secret_qa.csv
docker compose run --rm app python register.py
docker compose run --rm app python search.py "今日のハンズオンの合言葉は？"
```

`secret_qa.csv` が1位に出れば成功です。

### S6 ツールを作る（15:55〜16:55）

`my_agent/agent.py` のTODOに沿って、検索をツールにしてエージェントにつなぎます。書き方はADKのドキュメント（[Function tools](https://adk.dev/tools-custom/function-tools/)）を読んで、自分の手で書いてください。

```bash
docker compose run --rm app python ask.py "今日のハンズオンの合言葉は？"
```

次の3つがそろえば合格です。

1. ツールが呼ばれている
2. 引けたQAのファイル名と点数が画面に出ている
3. 回答に合言葉が入っている

合格したら、[発展課題](challenges.md) でほかのツールも作ってみてください。

### S7 判定する（16:55〜17:10）

```bash
docker compose run --rm app python ask.py --save "社会人ですが、42 Tokyoで学ぶ価値はありますか？"
```

1回だけ聞いて、回答を画面でチームに見せます。チームで話し合う回答を2〜3個選び、「42 Tokyoの公式サイトに載せてOKか」を、一人ずつOKかNGかと理由を言って話し合います。

### S8 再度同じ質問をエージェントに聞いてみる（17:10〜17:25）

S7と同じコマンドを、もう一度だけ実行します。前の回答（ターミナルを上にたどるか、`out/answers.jsonl`）と見比べて、変わったところをチームに一言ずつ伝えます。判定はしません。

### S10 交流（17:35〜19:00）

アンケートに答えたら、教室のPCから今日のリポジトリを消します。

```bash
docker compose run --rm app sh -c 'rm -rf out .pytest_cache .mypy_cache && find . -name __pycache__ -prune -exec rm -rf {} +'
docker compose down --rmi all
cd ../.. && rm -rf LaboroPublic42Events
```

書いたQA、保存した回答、キーを書いた `.env`、ビルドしたイメージがすべて消えます。
