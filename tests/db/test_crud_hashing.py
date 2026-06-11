from backend.app.db import crud


def test_image_sha256_is_stable() -> None:
    first = crud.image_sha256(b"same-image")
    second = crud.image_sha256(b"same-image")
    different = crud.image_sha256(b"different-image")

    assert first == second
    assert first != different
    assert len(first) == 64


def test_normalize_instruction_collapses_blank_inputs() -> None:
    assert crud.normalize_instruction(None) == ""
    assert crud.normalize_instruction("") == ""
    assert crud.normalize_instruction("   ") == ""
    assert crud.normalize_instruction("\n\t  \n") == ""


def test_normalize_instruction_compacts_whitespace() -> None:
    assert crud.normalize_instruction("  hello   world  ") == "hello world"
    assert crud.normalize_instruction("a\n\nb\t c") == "a b c"


def test_instruction_sha256_is_stable_for_blank_inputs() -> None:
    empty = crud.instruction_sha256("")
    none_hash = crud.instruction_sha256(None)
    blanks = crud.instruction_sha256("   \n  ")

    assert empty == none_hash == blanks
    assert len(empty) == 64


def test_instruction_sha256_differs_for_distinct_text() -> None:
    assert crud.instruction_sha256("make it bright") != crud.instruction_sha256(
        "make it dark"
    )
