"""배치 결과 HTML 그리드 리포트 생성.

행 = 프롬프트 케이스(종류별 필터), 열 = 입력 이미지 × 반복 회차.
셀을 클릭하면 원본/결과 비교, 사용된 프롬프트 전문, AI 채점 상세를 보여준다.
같은 이미지의 반복(r1, r2, ...)이 나란히 배치되므로 편차를 한눈에 비교할 수 있다.

사용:
  uv run python experiments/report.py experiments/runs/<run_id>
"""

# ruff: noqa: E501

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

KIND_LABELS = {
    "system": "시스템",
    "copy": "문구",
    "user": "유저 입력",
    "mixed": "혼합",
}

CSS = """
:root { --line:#e3e3e3; --muted:#777; font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif; }
body { margin:0; padding:24px; background:#fafafa; color:#222; }
h1 { font-size:20px; margin:0 0 4px; }
.meta { color:var(--muted); font-size:13px; margin-bottom:16px; }
.chips { display:flex; gap:8px; margin-bottom:16px; flex-wrap:wrap; }
.chip { border:1px solid var(--line); background:#fff; border-radius:16px; padding:6px 14px;
  font-size:13px; cursor:pointer; }
.chip.active { background:#222; color:#fff; border-color:#222; }
.grid-wrap { overflow-x:auto; background:#fff; border:1px solid var(--line); border-radius:8px; }
table { border-collapse:collapse; font-size:12px; }
th, td { border:1px solid var(--line); padding:6px; text-align:center; vertical-align:top; }
th.case-col { position:sticky; left:0; background:#fff; min-width:200px; max-width:260px;
  text-align:left; z-index:2; }
thead th { background:#f4f4f4; position:sticky; top:0; z-index:3; }
thead img { width:72px; height:72px; object-fit:cover; border-radius:4px; display:block; margin:4px auto; }
.kind-badge { display:inline-block; font-size:11px; border-radius:4px; padding:2px 6px;
  color:#fff; margin-right:6px; }
.kind-system{background:#5470c6}.kind-copy{background:#fac858;color:#222}
.kind-user{background:#ee6666}.kind-mixed{background:#73c0de}
.case-id { font-weight:600; font-size:13px; }
.case-sub { color:var(--muted); margin-top:4px; line-height:1.5; word-break:break-all; }
details summary { cursor:pointer; color:#5470c6; margin-top:4px; }
details pre { white-space:pre-wrap; text-align:left; font-size:11px; background:#f7f7f7;
  padding:8px; border-radius:4px; max-height:240px; overflow:auto; }
.cell img { width:148px; height:148px; object-fit:cover; border-radius:4px; cursor:zoom-in;
  display:block; }
.cell { position:relative; }
.score { position:absolute; top:10px; right:10px; font-size:11px; font-weight:700;
  border-radius:10px; padding:2px 7px; color:#fff; }
.s-good{background:#2e7d32}.s-mid{background:#ef6c00}.s-bad{background:#c62828}
.cell-error { width:148px; height:148px; display:flex; align-items:center; justify-content:center;
  background:#fdecea; color:#c62828; border-radius:4px; font-size:11px; padding:6px; box-sizing:border-box; }
.cell-dry { width:148px; height:148px; display:flex; align-items:center; justify-content:center;
  background:#f0f0f0; color:var(--muted); border-radius:4px; cursor:zoom-in; }
.elapsed { color:var(--muted); font-size:11px; margin-top:3px; }
dialog { border:none; border-radius:10px; max-width:1100px; width:92vw; padding:20px; }
dialog::backdrop { background:rgba(0,0,0,.55); }
.cmp { display:flex; gap:16px; flex-wrap:wrap; }
.cmp figure { margin:0; }
.cmp img { max-width:420px; max-height:60vh; border-radius:6px; }
.cmp figcaption { font-size:12px; color:var(--muted); margin-top:4px; text-align:center; }
.judge-box { background:#f7f7f7; border-radius:6px; padding:10px 14px; margin-top:12px; font-size:13px; }
.judge-box ul { margin:6px 0 0 18px; padding:0; }
dialog pre { white-space:pre-wrap; font-size:12px; background:#f7f7f7; padding:10px;
  border-radius:6px; max-height:300px; overflow:auto; }
.close { float:right; cursor:pointer; border:none; background:#eee; border-radius:6px; padding:6px 12px; }
tr.hidden { display:none; }
"""

JS = """
const RECORDS = __RECORDS__;
function filterKind(kind, btn) {
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('tr[data-kind]').forEach(tr => {
    tr.classList.toggle('hidden', kind !== 'all' && tr.dataset.kind !== kind);
  });
}
function scoreBlock(j) {
  if (!j) return '<div class="judge-box">AI 채점 전입니다. judge.py를 실행하세요.</div>';
  if (j.error) return `<div class="judge-box">채점 실패: ${j.error}</div>`;
  const rows = [
    ['제품 보존', j.product_preserved], ['구도/레이아웃', j.composition],
    ['문구 정확도', j.copy_text_accuracy],
    ['금지 요소 없음', j.no_unwanted_elements], ['종합', j.overall],
  ].filter(([, v]) => v !== null && v !== undefined)
   .map(([k, v]) => `${k}: <b>${v}</b>/5`).join(' · ');
  const issues = (j.issues || []).map(i => `<li>${i}</li>`).join('');
  return `<div class="judge-box"><b>AI 채점 — ${j.verdict || ''}</b><br>${rows}
    ${issues ? '<ul>' + issues + '</ul>' : ''}</div>`;
}
function openCell(idx) {
  const r = RECORDS[idx];
  const dlg = document.getElementById('dlg');
  const out = r.output
    ? `<figure><img src="${r.output}"><figcaption>결과 (${r.target}, ${r.elapsed_s ?? '-'}s)</figcaption></figure>`
    : '<figure><div class="cell-dry" style="width:300px;height:300px">dry-run</div></figure>';
  document.getElementById('dlg-body').innerHTML = `
    <h3 style="margin:0 0 10px">${r.case_id} × ${r.image} (r${r.rep})</h3>
    <div class="cmp">
      <figure><img src="inputs/${r.image}"><figcaption>원본</figcaption></figure>${out}
    </div>
    ${scoreBlock(r.judge)}
    <details open><summary>사용된 프롬프트 전문</summary><pre>${r.prompt
      .replaceAll('&', '&amp;').replaceAll('<', '&lt;')}</pre></details>`;
  dlg.showModal();
}
"""


def score_badge(record: dict[str, Any]) -> str:
    judge = record.get("judge") or {}
    overall = judge.get("overall")
    if not isinstance(overall, int | float):
        return ""
    cls = "s-good" if overall >= 4 else ("s-mid" if overall >= 3 else "s-bad")
    return f'<span class="score {cls}">{overall}</span>'


def cell_html(record: dict[str, Any] | None, index: int | None) -> str:
    if record is None:
        return "<td>-</td>"
    if record["status"] == "error":
        body = f'<div class="cell-error">{html.escape((record["error"] or "")[:120])}</div>'
        return f'<td class="cell">{body}</td>'
    if record["status"] == "dry_run":
        return (
            f'<td class="cell"><div class="cell-dry" onclick="openCell({index})">dry-run<br>'
            "프롬프트 보기</div></td>"
        )
    elapsed = f'<div class="elapsed">{record["elapsed_s"]}s</div>' if record.get("elapsed_s") else ""
    return (
        f'<td class="cell"><img loading="lazy" src="{record["output"]}" '
        f'onclick="openCell({index})">{score_badge(record)}{elapsed}</td>'
    )


def case_header(record: dict[str, Any]) -> str:
    kind = record["kind"]
    parts: list[str] = []
    parts.append(f"{record['preset']}/{record['detail']}")
    if record.get("copy"):
        copy_def = record["copy"]
        joined = " / ".join(str(v) for v in copy_def.values() if v)
        parts.append(f"문구: {joined}")
    if record.get("user_prompt"):
        parts.append(f"유저: {record['user_prompt']}")
    if record.get("system_append"):
        parts.append(f"시스템 추가: {record['system_append']}")
    if record.get("system_override"):
        parts.append("시스템 전체 교체")
    sub = "<br>".join(html.escape(p) for p in parts)
    return (
        f'<th class="case-col"><span class="kind-badge kind-{kind}">{KIND_LABELS.get(kind, kind)}'
        f'</span><span class="case-id">{html.escape(record["case_id"])}</span>'
        f'<div class="case-sub">{sub}</div>'
        f"<details><summary>프롬프트 전문</summary><pre>{html.escape(record['prompt'])}</pre>"
        f"</details></th>"
    )


def build_report(run_dir: Path) -> Path:
    payload = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = payload["records"]

    # 열 축: (이미지, 반복) — 입력 이미지 순서 유지, 반복은 오름차순으로 인접 배치.
    images = list(dict.fromkeys(r["image"] for r in records))
    reps = sorted({r["rep"] for r in records})
    case_ids = list(dict.fromkeys(r["case_id"] for r in records))
    kind_order = ["system", "copy", "user", "mixed"]
    case_ids.sort(
        key=lambda cid: kind_order.index(
            next(r["kind"] for r in records if r["case_id"] == cid)
        )
    )
    lookup = {(r["case_id"], r["image"], r["rep"]): (i, r) for i, r in enumerate(records)}

    head_cells = "".join(
        f'<th colspan="{len(reps)}"><img src="inputs/{html.escape(img)}">'
        f"{html.escape(img)}</th>"
        for img in images
    )
    rep_cells = (
        "<tr><th></th>" + "".join(f"<th>r{rep}</th>" for img in images for rep in reps) + "</tr>"
        if len(reps) > 1
        else ""
    )

    rows: list[str] = []
    for case_id in case_ids:
        first = next(r for r in records if r["case_id"] == case_id)
        cells = "".join(
            cell_html(*(lookup.get((case_id, img, rep)) or (None, None))[::-1])
            for img in images
            for rep in reps
        )
        rows.append(f'<tr data-kind="{first["kind"]}">{case_header(first)}{cells}</tr>')

    kinds_present = list(dict.fromkeys(r["kind"] for r in records))
    chips = '<button class="chip active" onclick="filterKind(\'all\', this)">전체</button>' + "".join(
        f'<button class="chip" onclick="filterKind(\'{k}\', this)">'
        f"{KIND_LABELS.get(k, k)}</button>"
        for k in kinds_present
    )

    ok = sum(1 for r in records if r["status"] == "ok")
    err = sum(1 for r in records if r["status"] == "error")
    judged = [
        r["judge"]["overall"]
        for r in records
        if isinstance((r.get("judge") or {}).get("overall"), int | float)
    ]
    avg = f" | 평균 점수 {sum(judged) / len(judged):.1f}" if judged else ""

    records_json = json.dumps(
        [
            {k: r.get(k) for k in ("case_id", "image", "rep", "output", "prompt", "judge", "target", "elapsed_s")}
            for r in records
        ],
        ensure_ascii=False,
    )
    page = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>{html.escape(payload["run_name"])} — 프롬프트 배치 리포트</title>
<style>{CSS}</style></head><body>
<h1>{html.escape(payload["run_name"])}</h1>
<div class="meta">{payload["created_at"]} | model {payload["model"]} ({payload["quality"]})
 | 성공 {ok} / 실패 {err} / 전체 {len(records)}{avg}
 | 케이스 {len(case_ids)} × 이미지 {len(images)} × 반복 {len(reps)}</div>
<div class="chips">{chips}</div>
<div class="grid-wrap"><table>
<thead><tr><th class="case-col">케이스 \\ 입력 이미지</th>{head_cells}</tr>{rep_cells}</thead>
<tbody>{"".join(rows)}</tbody>
</table></div>
<dialog id="dlg"><button class="close" onclick="document.getElementById('dlg').close()">닫기</button>
<div id="dlg-body"></div></dialog>
<script>{JS.replace("__RECORDS__", records_json)}</script>
</body></html>"""

    report_path = run_dir / "report.html"
    report_path.write_text(page, encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description="배치 결과 HTML 리포트 생성")
    parser.add_argument("run_dir", help="experiments/runs/<run_id> 경로")
    args = parser.parse_args()
    run_dir = Path(args.run_dir)
    if not run_dir.is_absolute():
        run_dir = ROOT_DIR / run_dir
    report_path = build_report(run_dir)
    print(f"리포트 생성 완료: {report_path}")
    print("브라우저로 열어 확인하세요 (이미지 상대경로라 폴더째 공유 가능).")


if __name__ == "__main__":
    main()
