"""Results and scoring tab UI for the experiments Streamlit console."""

# ruff: noqa: E501

import asyncio
import json

import streamlit as st
from app_evaluation import default_eval_items, load_evaluation, run_ai_eval, save_evaluation
from app_prompting import COPY_MODE_LABELS, LOGO_POSITION_LABELS
from app_state import list_runs
from runner import load_settings

from backend.app.services.costs import calculate_image_cost


def render_results_tab() -> None:
    result_runs = list_runs("results.json")
    if not result_runs:
        st.info("아직 결과가 없습니다. '새 테스트' 탭에서 생성하기를 눌러주세요.")
    else:
        run_label_map = {}
        for run_id, run_dir in result_runs:
            try:
                results = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
            except ValueError:
                continue
            run_label_map[f"{results.get('run_name', run_id)}  ·  {run_id[:15]}"] = (
                run_dir,
                results,
            )

        selected = st.selectbox("테스트 선택", list(run_label_map.keys()), key="result_select")
        run_dir, results = run_label_map[selected]
        run_id = run_dir.name
        test_name = results.get("run_name", run_id)
        records = results.get("records", [])
        ok_records = sorted(
            [r for r in records if r.get("status") == "ok"], key=lambda r: r.get("rep", 0)
        )
        error_count = sum(1 for r in records if r.get("status") == "error")
        image_numbers = [str(i + 1) for i in range(len(ok_records))]

        # 세션에 평가표 적재. 그리드 위젯의 초기값 원본은 items(dict 리스트)다.
        # 다른 테스트로 전환했다 돌아오면 Streamlit이 위젯 상태를 청소하므로,
        # '전환'을 감지하면 evaluation.json(저장된 평가·메모)을 디스크에서 다시 읽는다.
        items_key = f"eval_items_{run_id}"
        ver_key = f"eval_grid_ver_{run_id}"
        costs_key = f"eval_costs_{run_id}"
        switched = st.session_state.get("_results_active_run") != run_id
        if switched or items_key not in st.session_state:
            saved_eval = load_evaluation(run_dir)
            st.session_state[items_key] = saved_eval["items"] or default_eval_items()
            st.session_state[ver_key] = st.session_state.get(ver_key, 0) + 1
            st.session_state[costs_key] = saved_eval.get(
                "costs", {"eval_usd": 0.0, "eval_calls": 0}
            )
            st.session_state[f"memo_{run_id}"] = saved_eval.get("memo", "")
            st.session_state["_results_active_run"] = run_id
        grid_ver = st.session_state[ver_key]

        def gkey(*parts) -> str:
            """그리드 위젯 세션 키. 버전을 올리면 그리드 전체가 새 값으로 다시 그려진다."""
            return f"grid_{run_id}_v{grid_ver}_" + "_".join(str(p) for p in parts)

        def current_items() -> list[dict]:
            """위젯 현재값으로 평가표를 재구성한다 (위젯 미생성 시 저장값 폴백)."""
            rebuilt: list[dict] = []
            for row, item in enumerate(st.session_state[items_key]):
                scores: dict[str, int] = {}
                for number in image_numbers:
                    score_key = gkey("sc", row, number)
                    if score_key in st.session_state:
                        value = st.session_state[score_key]
                        if value is not None:
                            scores[number] = int(value)
                    else:
                        saved = item.get("scores", {}).get(number)
                        if saved is not None:
                            scores[number] = int(saved)
                rebuilt.append(
                    {
                        "evaluator": st.session_state.get(
                            gkey("ev", row), item.get("evaluator", "사람")
                        ),
                        "criterion": str(
                            st.session_state.get(gkey("cr", row), item.get("criterion", ""))
                            or ""
                        ).strip(),
                        "scores": scores,
                    }
                )
            return rebuilt

        def apply_items(new_items: list[dict]) -> None:
            """평가표를 교체하고 위젯 버전을 올려 그리드를 새로 초기화한다."""
            st.session_state[items_key] = new_items
            st.session_state[ver_key] += 1

        # ── 상단 바: 테스트명 + AI가 평가하기 + 저장하기 ──────────────────
        col_title, col_ai, col_save = st.columns([2, 1, 1])
        with col_title:
            st.subheader(test_name)
        with col_ai:
            ai_clicked = st.button("AI가 평가하기", use_container_width=True)
        with col_save:
            save_clicked = st.button("저장하기", type="primary", use_container_width=True)
        st.caption(
            "저장된 평가·메모는 테스트를 선택하면 자동으로 불러와집니다. "
            "다른 테스트로 전환하면 저장하지 않은 변경은 사라지니, 전환 전에 저장하기를 누르세요."
        )

        if ai_clicked:
            items_now = current_items()
            criteria = {
                str(idx): item["criterion"]
                for idx, item in enumerate(items_now)
                if item["evaluator"] == "AI" and item["criterion"]
            }
            settings = load_settings()
            if not criteria:
                st.warning("평가자가 'AI'이고 내용이 입력된 항목이 없습니다.")
            elif not ok_records:
                st.warning("평가할 성공 이미지가 없습니다.")
            elif not settings.openai_api_key:
                st.error("OPENAI_API_KEY가 없습니다 (.env 확인).")
            else:
                prompt_text = ok_records[0].get("prompt", "")
                with st.spinner(
                    f"AI 평가 중 — 항목 {len(criteria)}개 × 이미지 {len(ok_records)}장 "
                    f"(Responses API, {settings.openai_text_model})"
                ):
                    scores_by_image, calls, errors, eval_cost_usd = asyncio.run(
                        run_ai_eval(run_dir, ok_records, criteria, prompt_text, settings)
                    )
                for number, crit_scores in scores_by_image.items():
                    for crit_key, score in crit_scores.items():
                        if crit_key in criteria:
                            items_now[int(crit_key)]["scores"][number] = score
                apply_items(items_now)
                grid_ver = st.session_state[ver_key]
                costs = st.session_state[costs_key]
                costs["eval_calls"] = costs.get("eval_calls", 0) + calls
                costs["eval_usd"] = round(costs.get("eval_usd", 0.0) + eval_cost_usd, 6)
                for message in errors:
                    st.warning(message)
                st.success(
                    f"AI 평가 완료 — 이미지 {len(scores_by_image)}장 채점됨. "
                    "'저장하기'를 눌러 보관하세요."
                )

        # ── 1·2행: 이미지 번호 + 생성 이미지 (가로 스크롤) ─────────────────
        error_messages = list(
            dict.fromkeys(
                r.get("error") for r in records if r.get("status") == "error" and r.get("error")
            )
        )
        if not ok_records:
            st.warning("성공한 이미지가 없습니다." + (f" (실패 {error_count}건)" if error_count else ""))
            for message in error_messages:
                st.error(f"실패 사유: {message}")
        else:
            if error_count:
                with st.expander(f"실패 {error_count}건 — 사유 보기 (표에서는 제외됨)"):
                    for message in error_messages:
                        st.error(message)

            size_col, _ = st.columns([1, 3])
            with size_col:
                img_width = st.slider(
                    "이미지 너비(px)", 240, 800, 500, 20, key=f"imgw_{run_id}"
                )

            # 고정 폭 컬럼 + 컨테이너 좌우 스크롤. 이미지(1·2행)와 점수 입력칸이 같은
            # 컬럼 그리드를 공유하고, 모든 행이 한 스크롤 컨테이너 안에 있어
            # 줌·스크롤에도 열 정렬이 유지된다.
            try:
                grid_box = st.container(key=f"evalgrid_{run_id}")
                scoped = True
            except TypeError:
                # 구버전 Streamlit(container key 미지원) 폴백: 비율 컬럼으로 표시.
                grid_box = st.container()
                scoped = False
            if scoped:
                st.markdown(
                    f"""<style>
.st-key-evalgrid_{run_id} {{ overflow-x: auto; padding-bottom: 8px; }}
.st-key-evalgrid_{run_id} div[data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap; width: max-content; }}
.st-key-evalgrid_{run_id} div[data-testid="stHorizontalBlock"] > div {{ flex: 0 0 auto !important; }}
.st-key-evalgrid_{run_id} div[data-testid="stHorizontalBlock"] > div:nth-child(1) {{ width: 130px !important; min-width: 130px !important; position: sticky; left: 0; z-index: 3; background: var(--background-color); }}
.st-key-evalgrid_{run_id} div[data-testid="stHorizontalBlock"] > div:nth-child(2) {{ width: 230px !important; min-width: 230px !important; position: sticky; left: 138px; z-index: 3; background: var(--background-color); }}
.st-key-evalgrid_{run_id} div[data-testid="stHorizontalBlock"] > div:nth-child(n+3) {{ width: {img_width}px !important; min-width: {img_width}px !important; }}
.st-key-evalgrid_{run_id} div[data-testid="stHorizontalBlock"] > div:last-child {{ width: 90px !important; min-width: 90px !important; }}
</style>""",
                    unsafe_allow_html=True,
                )

            col_spec = [0.9, 1.8] + [2.0] * len(ok_records) + [0.7]
            row_averages: list[float | None] = []
            with grid_box:
                header = st.columns(col_spec, gap="small")
                header[0].markdown("**평가자**")
                header[1].markdown("**평가 항목**")
                for i, record in enumerate(ok_records):
                    with header[2 + i]:
                        st.markdown(
                            f"<div style='text-align:center;font-weight:700'>{i + 1}</div>",
                            unsafe_allow_html=True,
                        )
                        st.image(str(run_dir / record["output"]), use_container_width=True)
                header[-1].markdown("**평균**")

                for row, item in enumerate(st.session_state[items_key]):
                    cols = st.columns(col_spec, gap="small")
                    cols[0].selectbox(
                        "평가자",
                        ["사람", "AI"],
                        index=1 if item.get("evaluator") == "AI" else 0,
                        key=gkey("ev", row),
                        label_visibility="collapsed",
                    )
                    cols[1].text_input(
                        "평가 항목",
                        value=item.get("criterion", ""),
                        key=gkey("cr", row),
                        label_visibility="collapsed",
                        placeholder=f"평가 항목 {row + 1}",
                    )
                    values: list[int] = []
                    for i, number in enumerate(image_numbers):
                        saved = item.get("scores", {}).get(number)
                        value = cols[2 + i].number_input(
                            f"이미지 {number} 점수",
                            min_value=0,
                            max_value=10,
                            step=1,
                            value=int(saved) if saved is not None else None,
                            key=gkey("sc", row, number),
                            label_visibility="collapsed",
                            placeholder="-",
                        )
                        if value is not None:
                            values.append(int(value))
                    average = round(sum(values) / len(values), 1) if values else None
                    row_averages.append(average)
                    cols[-1].markdown(
                        f"<div style='text-align:center;padding-top:8px;font-weight:700'>{average}</div>"
                        if average is not None
                        else "<div style='text-align:center;padding-top:8px;color:#999'>-</div>",
                        unsafe_allow_html=True,
                    )

            valid_averages = [a for a in row_averages if a is not None]
            total = (
                round(sum(valid_averages) / len(valid_averages), 1) if valid_averages else None
            )
            col_add, col_del, col_total = st.columns([1, 1, 4])
            with col_add:
                if st.button("항목 추가", use_container_width=True):
                    apply_items(
                        current_items() + [{"evaluator": "사람", "criterion": "", "scores": {}}]
                    )
                    st.rerun()
            with col_del:
                if st.button("항목 삭제", use_container_width=True):
                    items_now = current_items()
                    if len(items_now) > 1:
                        apply_items(items_now[:-1])
                        st.rerun()
                    else:
                        st.warning("최소 1개 항목은 남겨야 합니다.")
            with col_total:
                if total is not None:
                    st.markdown(f"**총점 (각 항목 평균의 평균): {total} / 10**")
                else:
                    st.caption("점수를 입력하면 항목별 평균(마지막 열)과 총점이 계산됩니다.")

            with st.expander("다른 테스트의 평가자·평가 항목 가져오기 (점수는 제외)"):
                eval_runs = [
                    (other_id, other_dir)
                    for other_id, other_dir in list_runs("evaluation.json")
                    if other_id != run_id
                ]
                if not eval_runs:
                    st.caption("평가가 저장된 다른 테스트가 없습니다. (저장하기를 누른 테스트만 나타납니다)")
                else:
                    import_labels = {}
                    for other_id, other_dir in eval_runs:
                        try:
                            other_eval = json.loads(
                                (other_dir / "evaluation.json").read_text(encoding="utf-8")
                            )
                        except ValueError:
                            continue
                        criterion_count = sum(
                            1 for it in other_eval.get("items", []) if it.get("criterion")
                        )
                        import_labels[
                            f"{other_eval.get('test_name', other_id)} · 항목 {criterion_count}개"
                            f" · {other_id[:15]}"
                        ] = other_eval
                    chosen_label = st.selectbox(
                        "가져올 테스트", list(import_labels.keys()), key=f"import_{run_id}"
                    )
                    chosen_eval = import_labels.get(chosen_label)
                    if chosen_eval:
                        preview = " / ".join(
                            f"[{it.get('evaluator', '사람')}] {it.get('criterion', '')}"
                            for it in chosen_eval.get("items", [])
                            if it.get("criterion")
                        )
                        st.caption(preview or "입력된 항목 내용이 없습니다.")
                        if st.button("평가자·평가 항목 가져오기 (점수 미포함)"):
                            imported = [
                                {
                                    "evaluator": it.get("evaluator", "사람"),
                                    "criterion": it.get("criterion", ""),
                                    "scores": {},
                                }
                                for it in chosen_eval.get("items", [])
                            ]
                            if imported:
                                apply_items(imported)
                                st.rerun()
                            else:
                                st.warning("가져올 항목이 없습니다.")

        if save_clicked:
            items = current_items()
            save_evaluation(
                run_dir,
                test_name,
                items,
                st.session_state.get(f"memo_{run_id}", ""),
                st.session_state[costs_key],
            )
            # 세션 캐시도 저장본과 동기화해 전환·복귀 시 어긋남을 막는다.
            st.session_state[items_key] = items
            st.success("저장 완료 — evaluation.json에 보관되었습니다.")

        # ── 설정값 정리 ────────────────────────────────────────────────────
        st.divider()
        with st.expander("이 테스트의 설정값", expanded=False):
            config_path = run_dir / "config.json"
            if config_path.exists():
                saved_cfg = json.loads(config_path.read_text(encoding="utf-8"))
                st.markdown(
                    f"- 채널: **{saved_cfg.get('channel_label')}** / 유형: "
                    f"**{saved_cfg.get('detail_label')}** (API {saved_cfg.get('api_size')})\n"
                    f"- 로고: {'있음 · ' + ('직접입력 프롬프트' if saved_cfg.get('logo_prompt_custom') else '기본 · 위치 ' + LOGO_POSITION_LABELS.get(saved_cfg.get('logo_position'), '-')) if saved_cfg.get('has_logo') else '없음'}\n"
                    f"- 문구: {('적용 · ' + COPY_MODE_LABELS.get(saved_cfg.get('copy_mode'), '-') + ' · 「' + saved_cfg.get('copy_text', '') + '」') if saved_cfg.get('copy_on') else '미적용'}\n"
                    f"- 유저 프롬프트: {('「' + saved_cfg.get('user_prompt') + '」') if saved_cfg.get('user_prompt') else '없음'}\n"
                    f"- 장수/품질: {saved_cfg.get('count')}장 · {saved_cfg.get('quality')} · "
                    f"모델 {results.get('model')}"
                )
            if records:
                st.text("사용된 프롬프트 전문:")
                st.code(records[0].get("prompt", ""), language=None)

        # ── 비용 ───────────────────────────────────────────────────────────
        run_quality = results.get("quality", "medium")
        generation_cost = sum(
            record["cost_usd"]
            if isinstance(record.get("cost_usd"), int | float)
            else calculate_image_cost(record.get("usage") or None, quality=run_quality)
            for record in ok_records
        )
        token_based = any(record.get("usage") for record in ok_records)
        eval_costs = st.session_state[costs_key]
        col_c1, col_c2, col_c3 = st.columns(3)
        col_c1.metric(
            "이미지 생성 비용" + (" (토큰 기반)" if token_based else " (품질 단가 추정)"),
            f"${generation_cost:.4f}",
        )
        col_c2.metric(
            "AI 평가 비용 (토큰 기반)",
            f"${eval_costs.get('eval_usd', 0.0):.4f}",
            f"호출 {eval_costs.get('eval_calls', 0)}회",
            delta_color="off",
        )
        col_c3.metric("합계", f"${generation_cost + eval_costs.get('eval_usd', 0.0):.4f}")
        st.caption(
            "백엔드와 동일한 토큰 단가표(backend/app/services/costs.py)로 계산합니다 — "
            "이미지: 응답 usage 토큰 기반(없으면 품질별 단가 폴백), AI 평가: Responses usage 토큰 기반. "
            "문구 '다듬기/바꾸기'의 텍스트 생성 비용은 합계에 포함되지 않습니다(백엔드 로그에서 확인)."
        )

        # ── 메모 ───────────────────────────────────────────────────────────
        st.text_area(
            "메모", key=f"memo_{run_id}", height=100,
            placeholder="이 테스트에서 발견한 점, 다음에 시도할 것 등을 기록하세요. 저장하기를 누르면 함께 저장됩니다.",
        )

        # ── AI 평가 가이드 ─────────────────────────────────────────────────
        st.caption(
            "**AI 평가에 적합한 항목** — 시각적으로 판별 가능한 객관 기준: "
            "「로고가 오른쪽 상단에 있다」 「지정한 문구와 가격이 정확히 표기됐다」 "
            "「사람·손이 등장하지 않는다」 「제품 형태가 원본과 동일하다」 "
            "「불필요한 텍스트·워터마크가 없다」 「여백이 충분하다」.  \n"
            "**AI 평가에 부적합한 항목** — 주관·감성·맥락 의존 기준: "
            "「예쁘다」 「트렌디하다」 「구매욕구를 자극한다」 「우리 브랜드 감성에 맞다」 "
            "「실제 클릭률이 높을 것이다」. 이런 항목은 '사람' 평가를 권장합니다."
        )
