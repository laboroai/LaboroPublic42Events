# 企画書v0.5 配布リポジトリの試作

`../検討資料/企画書_v0.5.md` のハンズオンで、学生に配るリポジトリの試作。QAの登録と検索（S5）、ツールをつなぐ最小エージェント（S6）、回答の保存（S7、S9）を含む。

## 準備

```bash
cp .env.example .env   # OPENAI_API_KEY を入れる。キーなしで試すときは HANDSON_MOCK=1
docker compose build
```

イメージは教室PCに合わせてx86_64（`linux/amd64`）で作る。Apple SiliconのMacで速く試すときは、`HANDSON_PLATFORM=linux/arm64 docker compose build` のようにアーキテクチャを切り替える。そのときは `HANDSON_IMAGE` も別の名前にして、配布用のイメージを上書きしないようにする。

## 学生が使うコマンド

`docker compose run --rm app` に続けて実行する。

| ステップ | コマンド | 中身 |
| :-- | :-- | :-- |
| 開場 | `python ask.py "こんにちは"` | テンプレートのエージェントが返事をするかを確かめる |
| S5 | `python register.py` | `data/` のCSVをすべて登録する。ファイルごとの件数を出す |
| S5 | `python search.py "質問"` | 登録したQAを検索し、上位3件を点数・ファイル名つきで出す。登録のあとにCSVが変わっていれば注意を出す |
| S6 | `python ask.py "固有QAの質問"` | エージェントに1問答えさせる。呼ばれたツールと、引けたQAの点数・ファイル名も出す（付録Aの合格条件1、2を画面で確かめられる） |
| S7、S9 | `python ask.py --save "質問"` | 回答を `out/answers.jsonl` に追記する |

キーがないときは、何をすればよいかを出して止まる。QAを登録する前に検索したときも同じ。

## 運営が使うコマンド

| 場面 | コマンド | 中身 |
| :-- | :-- | :-- |
| S2のデモ | `python ask.py --agent ops.reference_agent "質問"` | 解答例のエージェントで答えさせる |
| S6の救済策（15:20） | 同上 | 解答例は本人の `data/` を登録した索引をそのまま使うので、本人のQAで答える。`ops/` は配布しないので、運営が本人の環境に `ops/reference_agent.py` を置く |
| 動作確認 | `docker compose run --rm -e HANDSON_MOCK=1 app pytest -q` | APIを呼ばずに一通りの動作を確かめる（11件） |

## 構成

| パス | 中身 | 学生 |
| :-- | :-- | :-- |
| `my_agent/agent.py` | 「こんにちは」と返すだけの最小エージェント。ツールをつなぐ場所にTODOがある | **作り変える** |
| `data/my_qa.csv` | 学生が書く魅力QA | **書く** |
| `data/shakaijin_qa.csv` | 社会人向けのメリットのQA（全員に配る共通のQA。5問） | 触らない |
| `data/secret_qa.csv` | 当日配る固有QA（リポジトリには入れない） | 置くだけ |
| `register.py`、`search.py`、`ask.py` | 上のコマンド | 使う |
| `lib/rag.py` | QAの登録（`out/index.npz` に保存）と検索 `search(query, k)`。埋め込みはOpenAIの `text-embedding-3-small`（`HANDSON_PROVIDER=bedrock` ならTitan Text Embeddings V2） | 触らない |
| `lib/model.py` | OpenAIのモデル（`HANDSON_MODEL`）をLiteLLM経由で呼ぶ。`HANDSON_PROVIDER=bedrock` ならBedrockのOpenAI互換APIで呼ぶ。`HANDSON_MOCK=1` ではモック | 触らない |
| `lib/runner.py` | ADKの Runner で1問答えさせ、回答とツールの呼び出し・結果を返す | 触らない |
| `claude-settings.example.json` | Claude Code を Bedrock で使う設定のひな形。当日は `settings.json` として配る | 使う |
| `ops/` | 解答例と、当日配る固有QA（`sample_secret_qa.csv`。合言葉のQA） | **配布しない** |
| `tests/` | モックでの動作確認 | 配布しない |

v0.4からの主な変更: 登録と検索をコマンドに分けて索引を保存するようにした。`ask.py` で引けたQAの点数を出し、`--save` で回答を残せるようにした。代表提出と見比べ（`answer.py`、`ops/compare.py`、`data/questions.json`）と、旧固有QAを外した。

## キーとモデル

10/9に、エージェントと埋め込みをOpenAIのAPIに切り替えた。`.env` の `OPENAI_API_KEY` にキーを書く。Claude Code はOpenAIのキーでは動かないので、Bedrockのキーを `settings.json` で別に配る。

| 用途 | モデル（既定） | 呼び方 |
| :-- | :-- | :-- |
| エージェント | `gpt-5.6-terra`（`HANDSON_MODEL`。OpenAIでのモデルIDは要確認） | OpenAIのChat Completions（LiteLLM経由） |
| 埋め込み | `text-embedding-3-small`（`HANDSON_EMBED_MODEL`） | OpenAIのEmbeddings |

埋め込みのモデルが変わったので、前に作った `out/index.npz` は使えない。`python register.py` をやり直す（やり直すようにエラーで促される）。

Bedrockに戻すときは `.env` に `HANDSON_PROVIDER=bedrock` と `AWS_BEARER_TOKEN_BEDROCK` を書き、`HANDSON_MODEL` と `HANDSON_EMBED_MODEL` の行を消す。既定は次のとおり。

| 用途 | モデル | 呼び方 | 処理される場所 |
| :-- | :-- | :-- | :-- |
| エージェント | `global.openai.gpt-5.6-terra` | `bedrock-runtime` のOpenAI互換API（Chat Completions） | 東京からはGlobalの推論のみ。世界のどこかのリージョン |
| 埋め込み | `amazon.titan-embed-text-v2:0` | `bedrock-runtime` の InvokeModel | 東京リージョン内 |

キーを発行するIAMロールに要る権限（案）: `bedrock:InvokeModel` と `bedrock:InvokeModelWithResponseStream` を、次に対して許可する。

- GPT-5.6 Terra のGlobal推論プロファイルと、その行き先の基盤モデル
- アカウントの既定プロジェクト（`arn:aws:bedrock:ap-northeast-1:{アカウントID}:project/default`）。OpenAIのモデルを `bedrock-runtime` で呼ぶときに要る
- Titan Text Embeddings V2（東京）
- Claude Code が使うモデル

本物のキーでの確認（10/7、Bedrock、Macのコンテナ、サンドボックスのAWSアカウント。OpenAIに切り替えたあとはまだ確かめていない）:

- Titanの埋め込みで登録と検索ができる。固有QAの質問で `secret_qa.csv` が1位（0.908）
- 解答例がツールを呼び、付録Aの合格条件3つを満たす
- 同じ質問（「42 Tokyoの魅力とは何ですか？」）を2回聞くと、内容は同じで言い回しが変わる（「グローバルな学習環境の一部」と「国際的なネットワークの一員」など）
- BedrockのChat Completionsでは、ツールと推論を同時に使えない。そのため `HANDSON_REASONING_EFFORT` の既定を `none` にしている

## 10/9（金）に42の教室PCで確かめること

教室PCはUbuntu 22.04、Intel Core i5（第8世代）、メモリ16GB。学生のアカウントで、上から順に試す。

持っていくもの（現地の通信に頼らずに試せるようにする）:

- このリポジトリのzip（GitHubから取得できない場合に備える）
- ビルド済みのイメージのファイル（予備）。当日はDockerfileから教室PCでビルドしてもらうが、会場の回線でビルドできないときに使う。Macで `docker save handson-42tokyo:0.5 | gzip > handson-42tokyo-0.5.tar.gz` として作り、教室PCで `docker load -i handson-42tokyo-0.5.tar.gz` で読み込む

| # | 確かめること | やり方 | だめだったとき |
| :-- | :-- | :-- | :-- |
| 1 | Dockerを学生アカウントで使えるか。`docker compose` のバージョン | `docker compose version`、`docker run --rm hello-world` | 社員PCの貸し出しか私物PCに切り替える（企画書5章） |
| 2 | イメージをビルドできるか | `time docker compose build` を実行し、かかった時間を控える。失敗したらエラーも控える。あわせて、持参したファイルを `docker load` できるかも試す | 当日は持参したファイルで配る |
| 2b | 25台が同時にビルドしても通るか | 教室のPCが、外から見て同じIPアドレスになるかを42側に聞く。同じなら、Docker Hubの匿名での取得回数の上限に当たるおそれがある | 前もってビルドを済ませるか、持参したファイルで配る |
| 3 | モックで一通り動くか | `.env` に `HANDSON_MOCK=1` を書き、`ops/sample_secret_qa.csv` を `data/secret_qa.csv` にコピーする。`register.py` → `search.py` → `ask.py --agent ops.reference_agent "今日のハンズオンの合言葉は？"` の順に実行し、付録Aの合格条件3つが画面で確かめられるかを見る。`pytest -q` | |
| 3b | コンテナが書いたファイルの持ち主 | 3のあとで `ls -l out/` を見る。rootの持ち物になっていると、学生が消したり書き換えたりできない | compose のサービスに `user: "${UID}:${GID}"` を足す |
| 4 | 外部に通信できるか | コンテナからOpenAIの接続先（`api.openai.com`）に届くか。`docker compose run --rm app python -c "import openai; openai.OpenAI(api_key='x').models.list()"` で `AuthenticationError`（401）が出れば届いている。`APIConnectionError` なら届いていない | 42側に開けてもらう |
| 5 | 本物のキーで動くか | 下の「本物のキーでの確認手順」 | |
| 6 | Claude Code を入れられるか | 学生アカウントでネイティブの導入手順を試し、`settings.json` でBedrockにつながるか | イメージに Claude Code を入れる案に切り替える |
| 7 | ホームの容量、夜間の初期化、取得したイメージが別のアカウントからも見えるか | 42側に聞く | |

### 本物のキーでの確認手順

`.env` に `OPENAI_API_KEY` を書き、`HANDSON_MOCK=0` にする。`ops/sample_secret_qa.csv` を `data/secret_qa.csv` にコピーしておく。コマンドの前には、すべて `docker compose run --rm app` を付ける（`docker compose run --rm app bash` で中に入れば付けなくてよい）。

| # | 見ること | コマンド | 合格の目安 |
| :-- | :-- | :-- | :-- |
| 1 | 埋め込みで登録できるか | `python register.py` | 「登録しました（埋め込み: text-embedding-3-small）」とファイルごとの件数が出る |
| 2 | 検索できるか | `python search.py "今日のハンズオンの合言葉は？"` | `secret_qa.csv` が1位 |
| 3 | エージェントが答えられるか | `python ask.py --agent ops.reference_agent "今日のハンズオンの合言葉は？"` | `search_qa` が呼ばれ、`secret_qa.csv` が引け、回答に「そらまめ通信」が入る（付録Aの合格条件3つ） |
| 4 | 回答の言い回しが変わるか | `python ask.py --agent ops.reference_agent "42 Tokyoの魅力とは何ですか？"` を2回 | 内容は同じで、言い回しが変わる |

チャットでモデルのIDのエラーが出たら、`python -c "import openai; print(sorted(m.id for m in openai.OpenAI().models.list()))"` で使えるIDを出し、`.env` の `HANDSON_MODEL` を直す。エラーの詳細を見るときは、コマンドの頭に `HANDSON_DEBUG=1` を付ける。

10/9にMacで確かめた結果（OpenAI）: 1〜3は合格。検索の点数は、1位の `secret_qa.csv` が0.829、2位が0.115。

## 配布前に決めること・確かめること

- いつビルドするか。10/9の#2の時間と#7の答えで決める。イメージが夜間に消えず、アカウントをまたいで見えるなら、前もって42側か運営がビルドしておける。そうでなければ、開場で学生がビルドする
- Dockerfileの `ghcr.io/astral-sh/uv:latest` を、10/9に確かめた版に固定する（当日に別の版が入らないように）
- 実際のモデル（GPT-5.6 Terra）で、解答例が固有QAに答えられるか、同じ質問で回答の文面が変わるか（通し試作）
