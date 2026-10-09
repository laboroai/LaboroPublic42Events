"""運営用の解答例（配布しない）。冒頭のデモと、詰まった人の支援に使う。

  python ask.py --agent ops.reference_agent "質問"

詰まった人の救済策（S6、15:20）: 本人の data/ で register したあと、この解答例で答えさせる。
"""

from google.adk.agents import Agent

from lib.model import get_model
from lib.rag import search


def search_qa(query: str) -> dict:
    """42 Tokyoに関するQA集を検索する。42 Tokyoについての質問に答える前に必ず使う。

    Args:
        query: 調べたいこと。質問文をそのまま渡してよい。
    """
    return {"results": search(query, k=3)}


INSTRUCTION = """あなたは42 Tokyoについて答えるアシスタントです。
質問に答える前に、必ず search_qa でQA集を調べてください。
QA集に書かれていることをもとに、日本語で答えてください。QA集にないことは、ないと伝えてください。"""

root_agent = Agent(
    name="reference_agent",
    model=get_model(),
    instruction=INSTRUCTION,
    tools=[search_qa],
)
