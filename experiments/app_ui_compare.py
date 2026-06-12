"""Multi-test comparison tab UI for the experiments Streamlit console."""

# ruff: noqa: E501

import asyncio
import json

import streamlit as st
from app_evaluation import COMPARE_MODEL, compare_cost_estimate, compare_prompts
from app_prompting import COPY_MODE_LABELS, LOGO_POSITION_LABELS
from app_state import list_runs
from runner import load_settings

from backend.app.services.costs import calculate_image_cost, calculate_text_cost


def render_compare_tab() -> None:
    compare_runs = list_runs("results.json")
    if not compare_runs:
        st.info("아직 결과가 없습니다. '새 테스트' 탭에서 생성하기를 눌러주세요.")
    else:
        compare_map = {}
        for cmp_id, cmp_dir in compare_runs:
            try:
                cmp_results = json.loads((cmp_dir / "results.json").read_text(encoding="utf-8"))
            except ValueError:
                continue
            cmp_oks = sorted(
                [r for r in cmp_results.get("records", []) if r.get("status") == "ok"],
                key=lambda r: r.get("rep", 0),
            )
            compare_map[f"{cmp_results.get('run_name', cmp_id)}  ·  {cmp_id[:15]}"] = {
                "run_id": cmp_id,
                "run_dir": cmp_dir,
                "results": cmp_results,
                "ok_records": cmp_oks,
            }

        selected_tests = st.multiselect(
            "모아볼 테스트 선택 (여러 개)", list(compare_map.keys()), key="tab3_selected"
        )
        if not selected_tests:
            st.caption("위에서 테스트를 선택하면 한 줄에 하나씩 이미지가 나란히 표시됩니다.")
        else:
            size_col3, _ = st.columns([1, 3])
            with size_col3:
                img_width3 = st.slider(
                    "이미지 너비(px)", 240, 800, 500, 20, key="imgw_tab3"
                )

            try:
                grid_box3 = st.container(key="tab3grid")
                scoped3 = True
            except TypeError:
                grid_box3 = st.container()
                scoped3 = False
            if scoped3:
                st.markdown(
                    f"""<style>
.st-key-tab3grid {{ overflow-x: auto; padding-bottom: 8px; }}
.st-key-tab3grid div[data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap; width: max-content; }}
.st-key-tab3grid div[data-testid="stHorizontalBlock"] > div {{ flex: 0 0 auto !important; }}
.st-key-tab3grid div[data-testid="stHorizontalBlock"] > div:nth-child(1) {{ width: 230px !important; min-width: 230px !important; position: sticky; left: 0; z-index: 3; background: var(--background-color); }}
.st-key-tab3grid div[data-testid="stHorizontalBlock"] > div:nth-child(n+2) {{ width: {img_width3}px !important; min-width: {img_width3}px !important; }}
</style>""",
                    unsafe_allow_html=True,
                )

            with grid_box3:
                for label in selected_tests:
                    entry = compare_map[label]
                    ok_list = entry["ok_records"]
                    row_cols = st.columns([1.4] + [2.0] * max(len(ok_list), 1), gap="small")
                    with row_cols[0]:
                        st.markdown(f"**{entry['results'].get('run_name', entry['run_id'])}**")
                        st.caption(
                            f"{entry['results'].get('created_at', '')} · "
                            f"{len(ok_list)}장 · {entry['results'].get('quality', '')}"
                        )
                    if not ok_list:
                        row_cols[1].caption("성공한 이미지 없음")
                    else:
                        for i, record in enumerate(ok_list):
                            row_cols[1 + i].image(
                                str(entry["run_dir"] / record["output"]),
                                use_container_width=True,
                            )

            # ── 테스트별 설정값·평가 요약 (한 번에 하나) ──────────────────
            st.divider()
            st.subheader("테스트별 설정 · 평가 요약")
            info_label = st.selectbox(
                "정보를 볼 테스트", selected_tests, key="tab3_info_select"
            )
            info = compare_map[info_label]
            info_cfg_path = info["run_dir"] / "config.json"
            if info_cfg_path.exists():
                info_cfg = json.loads(info_cfg_path.read_text(encoding="utf-8"))
                st.markdown(
                    f"- 채널: **{info_cfg.get('channel_label')}** / 유형: "
                    f"**{info_cfg.get('detail_label')}** (API {info_cfg.get('api_size')})\n"
                    f"- 로고: {'있음 · ' + ('직접입력 프롬프트' if info_cfg.get('logo_prompt_custom') else '기본 · 위치 ' + LOGO_POSITION_LABELS.get(info_cfg.get('logo_position'), '-')) if info_cfg.get('has_logo') else '없음'}\n"
                    f"- 문구: {('적용 · ' + COPY_MODE_LABELS.get(info_cfg.get('copy_mode'), '-') + ' · 「' + info_cfg.get('copy_text', '') + '」') if info_cfg.get('copy_on') else '미적용'}\n"
                    f"- 유저 프롬프트: {('「' + info_cfg.get('user_prompt') + '」') if info_cfg.get('user_prompt') else '없음'}\n"
                    f"- 장수/품질: {info_cfg.get('count')}장 · {info_cfg.get('quality')} · "
                    f"모델 {info['results'].get('model')} · "
                    f"텍스트 모델 {info['results'].get('text_model') or '기록 없음(구버전 실행)'}"
                )
            else:
                st.caption("설정 스냅샷(config.json)이 없는 테스트입니다 (CLI 실행 등).")

            info_oks = info["ok_records"]
            if info_oks:
                info_quality = info["results"].get("quality", "medium")
                info_gen_cost = sum(
                    r["cost_usd"]
                    if isinstance(r.get("cost_usd"), int | float)
                    else calculate_image_cost(r.get("usage") or None, quality=info_quality)
                    for r in info_oks
                )
                info_times = [
                    r["elapsed_s"]
                    for r in info_oks
                    if isinstance(r.get("elapsed_s"), int | float)
                ]
                time_text = (
                    f"**{sum(info_times) / len(info_times):.1f}초** "
                    f"(누적 {sum(info_times):.0f}초 / {len(info_times)}장)"
                    if info_times
                    else "-"
                )
                st.markdown(
                    f"- 이미지당 비용: **${info_gen_cost / len(info_oks):.4f}** "
                    f"(총 ${info_gen_cost:.4f} / {len(info_oks)}장)\n"
                    f"- 이미지당 생성 시간: {time_text}"
                )

            info_records = info["results"].get("records", [])
            info_prompt = info_records[0].get("prompt", "") if info_records else ""
            with st.expander("이 테스트에 쓰인 프롬프트 전문"):
                if info_prompt:
                    st.code(info_prompt, language=None)
                else:
                    st.caption("프롬프트 기록이 없습니다.")

            info_eval_path = info["run_dir"] / "evaluation.json"
            if info_eval_path.exists():
                try:
                    info_eval = json.loads(info_eval_path.read_text(encoding="utf-8"))
                except ValueError:
                    info_eval = {"items": []}
                summary_rows = []
                item_averages = []
                for item in info_eval.get("items", []):
                    if not item.get("criterion") and not item.get("scores"):
                        continue
                    values = [
                        v
                        for v in item.get("scores", {}).values()
                        if isinstance(v, int | float)
                    ]
                    item_avg = round(sum(values) / len(values), 1) if values else None
                    if item_avg is not None:
                        item_averages.append(item_avg)
                    summary_rows.append(
                        (item.get("evaluator", "사람"), item.get("criterion", ""), item_avg)
                    )
                if summary_rows:
                    table_md = "| 평가자 | 평가 항목 | 평균 |\n|---|---|---|\n" + "\n".join(
                        f"| {evaluator} | {criterion or '-'} | "
                        f"{f'{item_avg:.1f}' if item_avg is not None else '-'} |"
                        for evaluator, criterion, item_avg in summary_rows
                    )
                    st.markdown(table_md)
                    if item_averages:
                        st.markdown(
                            f"**총점: {round(sum(item_averages) / len(item_averages), 1)} / 10**"
                        )
                    else:
                        st.caption("입력된 점수가 없습니다.")
                else:
                    st.caption("평가 항목이 비어 있습니다.")
                memo_text = (info_eval.get("memo") or "").strip()
                st.markdown("**메모**")
                if memo_text:
                    st.text(memo_text)
                else:
                    st.caption("저장된 메모가 없습니다.")
            else:
                st.caption("저장된 평가가 없습니다 ('결과 · 평가' 탭에서 저장하기).")

            # ── 프롬프트 비교 (AI) ────────────────────────────────────────
            st.divider()
            st.subheader("프롬프트 비교 (AI)")
            pair = st.multiselect(
                "비교할 테스트 2개 선택",
                selected_tests,
                max_selections=2,
                key="tab3_pair",
            )
            if len(pair) != 2:
                st.caption("두 개를 선택하면 비교 버튼이 나타납니다.")
            else:
                entry_a, entry_b = compare_map[pair[0]], compare_map[pair[1]]
                records_a, records_b = entry_a["results"].get("records", []), entry_b[
                    "results"
                ].get("records", [])
                prompt_a = records_a[0].get("prompt", "") if records_a else ""
                prompt_b = records_b[0].get("prompt", "") if records_b else ""
                if not prompt_a or not prompt_b:
                    st.warning("프롬프트 기록이 없는 테스트가 있어 비교할 수 없습니다.")
                else:
                    cmp_key = "cmp_" + "_".join(
                        sorted([entry_a["run_id"], entry_b["run_id"]])
                    )
                    estimated = compare_cost_estimate(prompt_a, prompt_b, COMPARE_MODEL)
                    if st.button("프롬프트 차이 분석 (AI)"):
                        compare_settings = load_settings()
                        if not compare_settings.openai_api_key:
                            st.error("OPENAI_API_KEY가 없습니다 (.env 확인).")
                        else:
                            with st.spinner(f"비교 중 ({COMPARE_MODEL})"):
                                try:
                                    explanation, usage = asyncio.run(
                                        compare_prompts(
                                            entry_a["results"].get("run_name", ""),
                                            prompt_a,
                                            entry_b["results"].get("run_name", ""),
                                            prompt_b,
                                            compare_settings,
                                            COMPARE_MODEL,
                                        )
                                    )
                                    actual = calculate_text_cost(usage, model=COMPARE_MODEL)
                                    st.session_state[cmp_key] = {
                                        "text": explanation,
                                        "cost": actual if actual > 0 else estimated,
                                    }
                                except Exception as exc:
                                    st.error(f"비교 실패: {type(exc).__name__}: {exc}")
                    stored = st.session_state.get(cmp_key)
                    if stored:
                        st.markdown(stored["text"])
                        st.caption(
                            f"이번 비교 비용(토큰 기반) ≈ ${stored['cost']:.4f} · 모델 {COMPARE_MODEL}"
                        )
                    else:
                        st.caption(
                            f"프롬프트 비교 1회 예상 비용 ≈ ${estimated:.4f} "
                            f"(모델 {COMPARE_MODEL}, costs.py 단가표 기준)"
                        )
