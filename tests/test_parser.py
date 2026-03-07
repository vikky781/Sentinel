"""Tests for the sentinel.parser.ast_extractor module."""

import ast
from pathlib import Path

import pytest

from sentinel.parser.ast_extractor import (
    SentinelSyntaxError,
    extract_classes,
    extract_functions,
    extract_imports,
    parse_python_file,
)


class TestParsePythonFile:
    """Tests for parse_python_file."""

    def test_valid_file(self, tmp_path: Path) -> None:
        source = "x = 1\n"
        target = tmp_path / "valid.py"
        target.write_text(source, encoding="utf-8")

        tree = parse_python_file(target)
        assert isinstance(tree, ast.Module)

    def test_syntax_error_raises_sentinel_syntax_error(self, tmp_path: Path) -> None:
        target = tmp_path / "bad.py"
        target.write_text("def broken(\n", encoding="utf-8")

        with pytest.raises(SentinelSyntaxError) as exc_info:
            parse_python_file(target)

        assert exc_info.value.file_path == target
        assert exc_info.value.line_number is not None

    def test_file_not_found(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent.py"

        with pytest.raises(FileNotFoundError):
            parse_python_file(missing)

    def test_non_python_extension(self, tmp_path: Path) -> None:
        target = tmp_path / "data.txt"
        target.write_text("hello", encoding="utf-8")

        with pytest.raises(ValueError, match=r"\.py"):
            parse_python_file(target)


class TestExtractFunctions:
    """Tests for extract_functions."""

    def test_no_functions(self) -> None:
        tree = ast.parse("x = 1\n")
        result = extract_functions(tree)
        assert result == []

    def test_single_function(self) -> None:
        source = "def foo():\n    pass\n"
        tree = ast.parse(source)
        result = extract_functions(tree)

        assert len(result) == 1
        assert result[0]["name"] == "foo"
        assert result[0]["lineno"] == 1

    def test_multiple_functions(self) -> None:
        source = (
            "def alpha():\n"
            "    pass\n"
            "\n"
            "def beta():\n"
            "    pass\n"
            "\n"
            "async def gamma():\n"
            "    pass\n"
        )
        tree = ast.parse(source)
        result = extract_functions(tree)

        assert len(result) == 3
        names = [f["name"] for f in result]
        assert names == ["alpha", "beta", "gamma"]

    def test_nested_function(self) -> None:
        source = (
            "def outer():\n"
            "    def inner():\n"
            "        pass\n"
        )
        tree = ast.parse(source)
        result = extract_functions(tree)

        assert len(result) == 2
        names = [f["name"] for f in result]
        assert "outer" in names
        assert "inner" in names

    def test_method_inside_class(self) -> None:
        source = (
            "class Foo:\n"
            "    def method(self):\n"
            "        pass\n"
        )
        tree = ast.parse(source)
        result = extract_functions(tree)

        assert len(result) == 1
        assert result[0]["name"] == "method"


class TestExtractImports:
    """Tests for extract_imports."""

    def test_no_imports(self) -> None:
        tree = ast.parse("x = 1\n")
        result = extract_imports(tree)
        assert result == []

    def test_import_statement(self) -> None:
        tree = ast.parse("import os\nimport sys\n")
        result = extract_imports(tree)
        assert result == ["os", "sys"]

    def test_from_import_statement(self) -> None:
        tree = ast.parse("from pathlib import Path\n")
        result = extract_imports(tree)
        assert result == ["pathlib"]

    def test_mixed_imports(self) -> None:
        source = (
            "import json\n"
            "from collections import defaultdict\n"
            "import os\n"
        )
        tree = ast.parse(source)
        result = extract_imports(tree)
        assert result == ["json", "collections", "os"]

    def test_multi_name_import(self) -> None:
        tree = ast.parse("import os, sys, json\n")
        result = extract_imports(tree)
        assert result == ["os", "sys", "json"]


class TestExtractClasses:
    """Tests for extract_classes."""

    def test_no_classes(self) -> None:
        tree = ast.parse("x = 1\n")
        result = extract_classes(tree)
        assert result == []

    def test_single_class(self) -> None:
        source = "class Foo:\n    pass\n"
        tree = ast.parse(source)
        result = extract_classes(tree)

        assert len(result) == 1
        assert result[0]["name"] == "Foo"
        assert result[0]["lineno"] == 1

    def test_multiple_classes(self) -> None:
        source = (
            "class Alpha:\n"
            "    pass\n"
            "\n"
            "class Beta:\n"
            "    pass\n"
        )
        tree = ast.parse(source)
        result = extract_classes(tree)

        assert len(result) == 2
        names = [c["name"] for c in result]
        assert names == ["Alpha", "Beta"]

    def test_nested_class(self) -> None:
        source = (
            "class Outer:\n"
            "    class Inner:\n"
            "        pass\n"
        )
        tree = ast.parse(source)
        result = extract_classes(tree)

        assert len(result) == 2
        names = [c["name"] for c in result]
        assert "Outer" in names
        assert "Inner" in names
