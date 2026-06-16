from html import escape

import streamlit as st

from frontend.work.copy import copy_mode_label

_FIELD_KEYS = ("headline", "subcopy", "cta")
_COPY_TEXT_KEYS = ("text", "content", "body", "message")
_SEPARATORS = (":", "：", "->", "=>")
_MANUAL_LABELS = {
    "headline": "headline",
    "head": "headline",
    "title": "headline",
    "제목": "headline",
    "헤드라인": "headline",
    "subcopy": "subcopy",
    "sub copy": "subcopy",
    "subtitle": "subcopy",
    "description": "subcopy",
    "body": "subcopy",
    "본문": "subcopy",
    "서브카피": "subcopy",
    "cta": "cta",
    "button": "cta",
    "버튼": "cta",
}
_DISPLAY_LABELS = {
    "headline": "헤드라인",
    "subcopy": "서브카피",
    "cta": "CTA",
}


def _line(label: str, value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return (
        '<div class="result-copy-line">'
        f"<span>{escape(label)}</span>"
        f"<strong>{escape(text)}</strong>"
        "</div>"
    )


def _label_key(raw_label: str) -> str | None:
    normalized = raw_label.strip().lower().replace("_", " ").replace("-", " ")
    normalized = " ".join(normalized.split())
    return _MANUAL_LABELS.get(normalized)


def _split_labeled_line(line: str) -> tuple[str | None, str]:
    for separator in _SEPARATORS:
        if separator in line:
            raw_label, value = line.split(separator, 1)
            return _label_key(raw_label), value.strip()
    return None, line.strip()


def _fields_from_text(text: object) -> dict[str, str]:
    prompt = str(text or "").strip()
    if not prompt:
        return {}

    fields: dict[str, str] = {}
    unlabeled: list[str] = []
    for raw_line in prompt.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        key, value = _split_labeled_line(line)
        if key and value:
            fields[key] = value
        else:
            unlabeled.append(line)

    for key, value in zip(_FIELD_KEYS, unlabeled, strict=False):
        fields.setdefault(key, value)
    return fields


def _copy_fields(copy: dict[str, object] | None) -> dict[str, object]:
    if not isinstance(copy, dict):
        return {}

    fields = {key: copy.get(key) for key in _FIELD_KEYS if copy.get(key)}
    if fields:
        return fields

    for text_key in _COPY_TEXT_KEYS:
        text_fields = _fields_from_text(copy.get(text_key))
        if text_fields:
            return text_fields
    return {}


def _copy_body(copy_fields: dict[str, object]) -> str:
    lines = [_line(_DISPLAY_LABELS[key], copy_fields.get(key)) for key in _FIELD_KEYS]
    return "".join(line for line in lines if line)


def result_copy_html(
    copy: dict[str, object] | None,
    *,
    result_context: dict[str, object] | None = None,
) -> str:
    ad_copy_enabled = bool(result_context.get("adCopyEnabled")) if result_context else False

    mode = copy.get("copyMode") if isinstance(copy, dict) else None
    if not mode and result_context:
        mode = result_context.get("copyMode")

    body = _copy_body(_copy_fields(copy))

    if not body and not ad_copy_enabled:
        return ""

    return (
        '<div class="result-copy-panel">'
        f'<div class="result-copy-mode">{escape(copy_mode_label(mode))}</div>'
        f"{body}"
        "</div>"
    )


def render_result_copy(
    copy: dict[str, object] | None,
    *,
    result_context: dict[str, object] | None = None,
) -> None:
    html = result_copy_html(copy, result_context=result_context)
    if html:
        st.markdown(html, unsafe_allow_html=True)
