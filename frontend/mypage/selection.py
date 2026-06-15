from collections.abc import MutableMapping, Sequence

SELECTED_GENERATION_IDS_KEY = "mypage_selected_generation_ids"


def selected_generation_ids(session_state: MutableMapping[str, object]) -> list[str]:
    raw_value = session_state.get(SELECTED_GENERATION_IDS_KEY, [])
    if not isinstance(raw_value, Sequence) or isinstance(raw_value, str | bytes | bytearray):
        return []
    return [str(value) for value in raw_value if str(value)]


def set_selected_generation_ids(
    session_state: MutableMapping[str, object],
    request_ids: Sequence[str],
) -> None:
    session_state[SELECTED_GENERATION_IDS_KEY] = [str(value) for value in request_ids if str(value)]


def toggle_generation_selection(
    session_state: MutableMapping[str, object],
    request_id: str,
) -> None:
    clean_request_id = str(request_id or "").strip()
    if not clean_request_id:
        return

    selected_ids = selected_generation_ids(session_state)
    if clean_request_id in selected_ids:
        selected_ids = [value for value in selected_ids if value != clean_request_id]
    else:
        selected_ids.append(clean_request_id)
    set_selected_generation_ids(session_state, selected_ids)


def selected_generation_items(items: list[dict], selected_ids: Sequence[str]) -> list[dict]:
    selected_lookup = {str(value) for value in selected_ids}
    return [
        item
        for item in items
        if str(item.get("request_id") or "") in selected_lookup
    ]


def generation_item_ids(items: Sequence[dict]) -> list[str]:
    request_ids = []
    for item in items:
        request_id = str(item.get("request_id") or "")
        if request_id:
            request_ids.append(request_id)
    return request_ids


def all_generation_page_items_selected(
    session_state: MutableMapping[str, object],
    page_items: Sequence[dict],
) -> bool:
    page_ids = generation_item_ids(page_items)
    if not page_ids:
        return False
    selected_lookup = set(selected_generation_ids(session_state))
    return set(page_ids).issubset(selected_lookup)


def toggle_generation_page_selection(
    session_state: MutableMapping[str, object],
    page_items: Sequence[dict],
) -> None:
    page_ids = generation_item_ids(page_items)
    if not page_ids:
        return

    selected_ids = selected_generation_ids(session_state)
    page_lookup = set(page_ids)
    selected_lookup = set(selected_ids)
    if page_lookup.issubset(selected_lookup):
        set_selected_generation_ids(
            session_state,
            [request_id for request_id in selected_ids if request_id not in page_lookup],
        )
        return

    set_selected_generation_ids(
        session_state,
        selected_ids + [request_id for request_id in page_ids if request_id not in selected_lookup],
    )


def action_availability(selected_count: int) -> dict[str, bool]:
    count = max(0, int(selected_count))
    return {
        "single": count == 1,
        "download": count >= 1,
        "folder": count >= 1,
        "multi": count > 1,
    }
