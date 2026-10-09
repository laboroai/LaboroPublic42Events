"""HANDSON_MOCK=1 で、APIを呼ばずに配布物の動きを確かめる。"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ["HANDSON_MOCK"] = "1"

import pytest

from lib import rag
from lib.runner import ask, load_agent

ROOT = Path(__file__).resolve().parent.parent
SECRET = ROOT / "ops" / "sample_secret_qa.csv"
SECRET_Q = "今日のハンズオンの合言葉は？"


@pytest.fixture
def data(tmp_path):
    """配布時の data/ に、学生のQAと当日配る固有QAを足した状態。"""
    d = tmp_path / "data"
    d.mkdir()
    (d / "my_qa.csv").write_text(
        "question,answer\n42の一番の魅力は？,仲間と教え合えること\n授業料はいくら？,無料\n", encoding="utf-8"
    )
    shutil.copy(SECRET, d / "secret_qa.csv")
    return d


@pytest.fixture
def index(data, tmp_path, monkeypatch):
    path = tmp_path / "out" / "index.npz"
    rag.register(data, path)
    monkeypatch.setattr(rag, "INDEX", path)
    monkeypatch.setattr(rag, "DATA", data)
    return path


def test_register_reads_every_csv_in_data(data, tmp_path):
    result = rag.register(data, tmp_path / "index.npz")
    assert result["counts"] == {"my_qa.csv": 2, "secret_qa.csv": 1}


def test_search_without_register_tells_what_to_do(tmp_path, monkeypatch):
    monkeypatch.setattr(rag, "INDEX", tmp_path / "none.npz")
    with pytest.raises(rag.RagError, match="register.py"):
        rag.search("授業料")


def test_search_returns_source_and_score(index):
    top = rag.search(SECRET_Q, k=1)[0]
    assert top["source"] == "secret_qa.csv"
    assert 0 < top["score"] <= 1


def test_index_built_in_another_mode_is_rejected(index, monkeypatch):
    monkeypatch.setenv("HANDSON_MOCK", "0")
    with pytest.raises(rag.RagError, match="register.py をやり直して"):
        rag.Index.load(index)


def test_editing_csv_after_register_is_detected(index, data):
    assert not rag.Index.load(index).is_stale(data)
    (data / "my_qa.csv").write_text("question,answer\n増やした,QA\n", encoding="utf-8")
    assert rag.Index.load(index).is_stale(data)


def test_template_agent_says_hello_without_tools():
    result = ask(load_agent("my_agent.agent"), "こんにちは")
    assert result["tool_calls"] == []
    assert "こんにちは" in result["answer"]


def test_reference_agent_answers_secret_qa_with_hits(index):
    result = ask(load_agent("ops.reference_agent"), SECRET_Q)
    [call] = result["tool_calls"]
    assert call["name"] == "search_qa"
    assert call["response"]["results"][0]["source"] == "secret_qa.csv"
    assert "そらまめ通信" in result["answer"]


def _run(*args, env=None):
    return subprocess.run(
        [sys.executable, *args], cwd=ROOT, capture_output=True, text=True,
        env={**os.environ, **(env or {})},
    )


def test_commands_stop_with_a_message_when_key_is_missing():
    res = _run("search.py", "授業料", env={"HANDSON_MOCK": "0", "HANDSON_PROVIDER": "openai", "OPENAI_API_KEY": ""})
    assert res.returncode == 2
    assert "OPENAI_API_KEY" in res.stderr


def test_ask_shows_hits_and_saves_answer(index, tmp_path, monkeypatch):
    import ask as ask_cmd

    answers = tmp_path / "out" / "answers.jsonl"
    monkeypatch.setattr(ask_cmd, "ANSWERS", answers)
    monkeypatch.setattr(sys, "argv", ["ask.py", "--save", "--agent", "ops.reference_agent", SECRET_Q])
    ask_cmd.main()
    record = json.loads(answers.read_text(encoding="utf-8").splitlines()[0])
    assert record["question"] == SECRET_Q
    assert record["tool_calls"][0]["name"] == "search_qa"


def test_real_model_calls_openai(monkeypatch):
    from lib import model

    monkeypatch.setenv("HANDSON_MOCK", "0")
    monkeypatch.delenv("HANDSON_PROVIDER", raising=False)
    monkeypatch.delenv("HANDSON_MODEL", raising=False)
    monkeypatch.delenv("HANDSON_REASONING_EFFORT", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    llm = model.get_model()
    assert llm.model == "openai/gpt-5.6-terra"
    assert "api_base" not in llm._additional_args
    assert "reasoning_effort" not in llm._additional_args


def test_real_embedding_uses_openai(monkeypatch):
    import openai

    calls = []

    class FakeEmbeddings:
        def create(self, model, input):
            calls.append((model, input))
            return SimpleNamespace(data=[SimpleNamespace(embedding=[3.0, 4.0]) for _ in input])

    monkeypatch.setenv("HANDSON_MOCK", "0")
    monkeypatch.delenv("HANDSON_PROVIDER", raising=False)
    monkeypatch.delenv("HANDSON_EMBED_MODEL", raising=False)
    monkeypatch.setattr(openai, "OpenAI", lambda: SimpleNamespace(embeddings=FakeEmbeddings()))
    vectors = rag.embed(["42の魅力"])
    assert calls == [("text-embedding-3-small", ["42の魅力"])]
    assert vectors.tolist() == [[0.6, 0.8]]


def test_bedrock_model_uses_openai_compatible_endpoint(monkeypatch):
    from lib import model

    monkeypatch.setenv("HANDSON_MOCK", "0")
    monkeypatch.setenv("HANDSON_PROVIDER", "bedrock")
    monkeypatch.delenv("HANDSON_REASONING_EFFORT", raising=False)
    monkeypatch.setenv("AWS_BEARER_TOKEN_BEDROCK", "dummy")
    monkeypatch.delenv("HANDSON_MODEL", raising=False)
    llm = model.get_model()
    assert llm.model == "openai/global.openai.gpt-5.6-terra"
    assert llm._additional_args["api_base"] == "https://bedrock-runtime.ap-northeast-1.amazonaws.com/openai/v1"
    assert llm._additional_args["reasoning_effort"] == "none"


def test_bedrock_embedding_uses_titan(monkeypatch):
    import io

    import boto3

    calls = []

    class FakeClient:
        def invoke_model(self, modelId, body):
            calls.append((modelId, json.loads(body)))
            return {"body": io.BytesIO(json.dumps({"embedding": [3.0, 4.0]}).encode())}

    monkeypatch.setenv("HANDSON_MOCK", "0")
    monkeypatch.setenv("HANDSON_PROVIDER", "bedrock")
    monkeypatch.delenv("HANDSON_EMBED_MODEL", raising=False)
    monkeypatch.setattr(boto3, "client", lambda service, region_name: FakeClient())
    vectors = rag.embed(["42の魅力"])
    assert calls == [("amazon.titan-embed-text-v2:0", {"inputText": "42の魅力"})]
    assert vectors.tolist() == [[0.6, 0.8]]
