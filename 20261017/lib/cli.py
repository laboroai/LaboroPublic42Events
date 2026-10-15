"""コマンドの共通処理（触らない）。"""

import os
import sys

from lib.rag import RagError, api_key_name, is_mock


def fail(message: str, code: int = 1):
    print(f"[エラー] {message}", file=sys.stderr)
    sys.exit(code)


def check_keys():
    """APIキーがなければ、何をすればよいかを伝えて止める。"""
    if not is_mock() and not os.getenv(api_key_name()):
        fail(f".env に {api_key_name()} がありません。当日配られたキーを .env に書いてください。"
             "キーなしで試すときは .env の HANDSON_MOCK=1 にします。", code=2)


def run(main):
    """main() を実行し、エラーは短いメッセージにして止める。HANDSON_DEBUG=1 なら詳細をそのまま出す。"""
    check_keys()
    try:
        main()
    except RagError as e:
        fail(str(e))
    except Exception as e:
        if os.getenv("HANDSON_DEBUG") == "1":
            raise
        first = (str(e).strip().splitlines() or [""])[0]
        fail(f"{type(e).__name__}: {first}\n詳しく見るときは HANDSON_DEBUG=1 を付けて実行する。")


def print_hits(hits: list[dict]):
    """検索結果を「点数・ファイル・質問」の表にして出す。"""
    for rank, h in enumerate(hits, 1):
        print(f"  {rank}. {h['score']:.3f}  {h['source']:<16}  {h['question']}")
