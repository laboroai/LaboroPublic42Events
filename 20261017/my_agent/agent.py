"""あなたのエージェント。このファイルを作り変える。

いまは「こんにちは」に返事をするだけで、QAは見ていない。
  python ask.py "こんにちは"
"""

from google.adk.agents import Agent

from lib.model import get_model

# TODO(S6): 登録したQAを検索するツールを作り、エージェントにつなぐ。
#   書き方はADKのドキュメント（Function tools）を読む: https://adk.dev/tools-custom/function-tools/
#   - ツールはふつうのPython関数でよい。引数と戻り値に型を書く
#   - docstring に「何をするツールか、いつ使うか」を書く。LLMはそれを読んで、呼ぶかどうかを決める
#   - QAの検索には lib.rag の search(query, k) が使える（S5で試した検索と同じもの）
#   - search の結果は、文字列に整形せずそのまま返す。そうすると ask.py が、引けたQAの点数とファイル名を出す
#   - できたら下の tools=[...] に入れて、当日配られる固有QAの質問を python ask.py で聞いて確かめる

INSTRUCTION = "あなたは42 Tokyoについて答えるアシスタントです。日本語で答えてください。"

root_agent = Agent(
    name="my_agent",
    model=get_model(),
    instruction=INSTRUCTION,
    tools=[],
)
