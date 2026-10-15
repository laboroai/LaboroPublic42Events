"""エージェントに1問答えさせる（S6、S7、S8）。呼ばれたツールと、引けたQAの点数も表示する。

  python ask.py "質問"
  python ask.py --save "質問"      回答を out/answers.jsonl に残す（S7、S8）
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from lib.cli import print_hits, run
from lib.runner import ask, load_agent

ANSWERS = Path(__file__).resolve().parent / "out" / "answers.jsonl"


def find_hits(value) -> list[dict]:
    """ツールの結果の中から、検索で引けたQA（score と source を持つもの）を探す。"""
    if isinstance(value, dict):
        if "score" in value and "source" in value:
            return [value]
        return [h for v in value.values() for h in find_hits(v)]
    if isinstance(value, list):
        return [h for v in value for h in find_hits(v)]
    return []


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("question")
    parser.add_argument("--save", action="store_true", help="回答を out/answers.jsonl に追記する")
    parser.add_argument("--agent", default="my_agent.agent", help="root_agent を持つモジュール")
    args = parser.parse_args()

    result = ask(load_agent(args.agent), args.question)
    if not result["tool_calls"]:
        print("[ツール] 呼ばれていません")
    for call in result["tool_calls"]:
        print(f"[ツール] {call['name']}({json.dumps(call['args'], ensure_ascii=False)})")
        hits = find_hits(call["response"])
        if hits:
            print_hits(hits)
    print()
    print(result["answer"])

    if args.save:
        ANSWERS.parent.mkdir(parents=True, exist_ok=True)
        record = {"time": datetime.now().isoformat(timespec="seconds"), "agent": args.agent, **result}
        with ANSWERS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        print(f"\n[保存] {ANSWERS.relative_to(ANSWERS.parent.parent)} に追記しました")


if __name__ == "__main__":
    run(main)
