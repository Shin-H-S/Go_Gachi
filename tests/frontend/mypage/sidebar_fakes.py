from frontend.mypage import folder_management, sidebar


class FakeContext:
    def __init__(self, on_enter=None, on_exit=None) -> None:
        self._on_enter = on_enter
        self._on_exit = on_exit

    def __enter__(self) -> "FakeContext":
        if self._on_enter:
            self._on_enter()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self._on_exit:
            self._on_exit()
        return None


class FakeStreamlit:
    def __init__(
        self,
        *,
        clicked_keys: set[str] | None = None,
        submitted_forms: set[str] | None = None,
        text_values: dict[str, str] | None = None,
        session_state: dict[str, object] | None = None,
    ) -> None:
        self.clicked_keys = clicked_keys or set()
        self.submitted_forms = submitted_forms or set()
        self.text_values = text_values or {}
        self.session_state = session_state or {}
        self.buttons: list[dict[str, object]] = []
        self.columns_calls: list[tuple[object, str]] = []
        self.forms: list[dict[str, object]] = []
        self.form_submits: list[dict[str, object]] = []
        self.markdowns: list[str] = []
        self.dialogs: list[dict[str, object]] = []
        self.popovers: list[dict[str, object]] = []
        self.text_inputs: list[dict[str, object]] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.rerun_called = False
        self._current_form_key = ""

    def markdown(self, body: str, *, unsafe_allow_html: bool = False) -> None:
        self.markdowns.append(body)

    def button(self, label: str, **kwargs) -> bool:
        self.buttons.append({"label": label, **kwargs})
        return str(kwargs.get("key") or "") in self.clicked_keys

    def columns(self, spec: object, gap: str) -> list[FakeContext]:
        self.columns_calls.append((spec, gap))
        count = len(spec) if isinstance(spec, list) else int(spec)
        return [FakeContext() for _ in range(count)]

    def container(self, **kwargs) -> FakeContext:
        return FakeContext()

    def popover(self, label: str, **kwargs) -> FakeContext:
        self.popovers.append({"label": label, **kwargs})
        return FakeContext()

    def dialog(self, title: str, **kwargs):
        def decorator(callback):
            def wrapper(*args, **inner_kwargs):
                self.dialogs.append({"title": title, **kwargs})
                return callback(*args, **inner_kwargs)

            return wrapper

        return decorator

    def form(self, key: str, **kwargs) -> FakeContext:
        self.forms.append({"key": key, **kwargs})
        return FakeContext(
            on_enter=lambda: setattr(self, "_current_form_key", key),
            on_exit=lambda: setattr(self, "_current_form_key", ""),
        )

    def text_input(self, label: str, **kwargs) -> str:
        key = str(kwargs.get("key") or "")
        self.text_inputs.append({"label": label, **kwargs})
        return self.text_values.get(key, str(kwargs.get("value") or ""))

    def form_submit_button(self, label: str, **kwargs) -> bool:
        self.form_submits.append(
            {"label": label, "form_key": self._current_form_key, **kwargs}
        )
        return self._current_form_key in self.submitted_forms

    def warning(self, body: str) -> None:
        self.warnings.append(body)

    def error(self, body: str) -> None:
        self.errors.append(body)

    def rerun(self) -> None:
        self.rerun_called = True


def patch_sidebar(monkeypatch, fake_st: FakeStreamlit) -> None:
    monkeypatch.setattr(sidebar, "st", fake_st)
    monkeypatch.setattr(folder_management, "st", fake_st)
    monkeypatch.setattr(sidebar, "_render_sidebar_icon_visual", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        sidebar,
        "set_view",
        lambda view: fake_st.session_state.__setitem__("mypage_view", view),
    )
    monkeypatch.setattr(
        folder_management,
        "set_view",
        lambda view: fake_st.session_state.__setitem__("mypage_view", view),
    )
