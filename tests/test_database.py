"""Tests for database layer 鈥?serialization and data safety."""

import json

from backend.db.database import _serialize_score


class TestSerializeScore:
    def test_dict_to_json(self):
        result = _serialize_score({"a": 1, "b": "hello"})
        parsed = json.loads(result)
        assert parsed == {"a": 1, "b": "hello"}

    def test_list_to_json(self):
        result = _serialize_score([1, 2, 3])
        parsed = json.loads(result)
        assert parsed == [1, 2, 3]

    def test_none_to_empty_string(self):
        result = _serialize_score(None)
        assert result == ""

    def test_string_passthrough(self):
        result = _serialize_score("hello world")
        assert result == "hello world"

    def test_int_to_string(self):
        result = _serialize_score(42)
        assert result == "42"
