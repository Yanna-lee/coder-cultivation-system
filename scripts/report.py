import base64
import datetime as dt
import html
import io
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import common as c  # noqa: E402

plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "Noto Sans CJK JP", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

TYPE_COLORS = {"debug": "#d62728", "read": "#1f77b4", "design": "#2ca02c",
               "overall": "#333333"}
REALM_COLORS = ["#f2f2f2", "#e6f0fa", "#fdf3d8", "#f3e5f5", "#fde0dc"]


def _png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def _empty(ax, msg):
    ax.text(0.5, 0.5, msg, ha="center", va="center", transform=ax.transAxes,
            fontsize=12, color="#888")
    ax.set_xticks([])
    ax.set_yticks([])


def _date_axis(ax):
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.grid(alpha=0.3)


def _window_rate(points, days, value):
    out = []
    for d, _, _ in points:
        win = [(n, m) for x, n, m in points if 0 <= (d - x).days < days]
        den = sum(m for _, m in win)
        if den:
            out.append((d, value(sum(n for n, _ in win), den)))
    return out


def _label(key, cfg):
    return "总修为" if key == "overall" else cfg["bench_types"][key]["label"]


def fig_elo(cfg, tracks):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    lines = {k: t["history"] for k, t in tracks.items() if t["history"]}
    if not lines:
        need = max(t["warmup_weeks"] - t["weeks_done"] for t in tracks.values())
        _empty(ax, f"灵根测定中，暂无修为曲线（还需约 {need} 周）")
        return _png(fig)
    values = [r for h in lines.values() for _, r in h]
    lo, hi = min(values) - 120, max(values) + 120
    realms = cfg["realms"]
    for i, r in enumerate(realms):
        top = realms[i + 1]["min"] if i + 1 < len(realms) else 10000
        if top < lo or r["min"] > hi:
            continue
        ax.axhspan(r["min"], top, color=REALM_COLORS[i % len(REALM_COLORS)], zorder=0)
        ax.text(1.01, (max(r["min"], lo) + min(top, hi)) / 2, r["name"],
                transform=ax.get_yaxis_transform(), va="center", fontsize=11)
    for k, h in lines.items():
        xs = [c.week_monday(w) for w, _ in h]
        ax.plot(xs, [r for _, r in h], marker="o", color=TYPE_COLORS[k],
                lw=2.5 if k == "overall" else 1.5, label=_label(k, cfg))
    ax.set_ylim(lo, hi)
    ax.set_ylabel("修为")
    ax.legend(loc="upper left")
    _date_axis(ax)
    return _png(fig)


def fig_bench_raw(cfg, scores):
    qs = c.scored_questions(scores)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.8))
    if not qs:
        _empty(a1, "尚无秘境成绩")
        _empty(a2, "尚无秘境成绩")
        return _png(fig)
    for t in cfg["bench_types"]:
        sub = [q for q in qs if q["type"] == t]
        if not sub:
            continue
        xs = [c.week_monday(q["week"]) for q in sub]
        a1.scatter(xs, [q["result"]["s"] for q in sub], color=TYPE_COLORS[t],
                   label=_label(t, cfg))
        a2.scatter(xs, [q["result"]["minutes"] / q["time_limit_min"] for q in sub],
                   color=TYPE_COLORS[t], label=_label(t, cfg))
    a1.set_title("得分 s")
    a1.set_ylim(-0.05, 1.05)
    a2.set_title("用时 / 时限")
    a2.axhline(1, color="#999", ls="--")
    for a in (a1, a2):
        a.legend()
        _date_axis(a)
    return _png(fig)


def _bucket_labels(cfg):
    return [f"{lo}-{hi}" for lo, hi in cfg["difficulty_buckets"]]


def _bucket_of(lv, cfg):
    for i, (lo, hi) in enumerate(cfg["difficulty_buckets"]):
        if lo <= lv <= hi:
            return i
    return len(cfg["difficulty_buckets"]) - 1


def fig_frontier(cfg, tasks):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    if not tasks:
        _empty(ax, "尚无宗门任务日志")
        return _png(fig)
    labels = _bucket_labels(cfg)
    quarters = sorted({c.quarter(t["date"]) for t in tasks})
    cmap = plt.get_cmap("viridis", max(len(quarters), 2))
    for qi, q in enumerate(quarters):
        xs, ys, ns = [], [], []
        for b in range(len(labels)):
            sub = [t for t in tasks if c.quarter(t["date"]) == q
                   and _bucket_of(t["level"], cfg) == b]
            if sub:
                xs.append(b)
                ys.append(sum(t["one_shot"] for t in sub) / len(sub))
                ns.append(len(sub))
        ax.plot(xs, ys, marker="o", color=cmap(qi), label=q)
        for x, y, n in zip(xs, ys, ns):
            ax.annotate(f"n={n}", (x, y), textcoords="offset points", xytext=(4, 4),
                        fontsize=8, color=cmap(qi))
    ax.set_xticks(range(len(labels)), labels)
    ax.set_xlabel("任务难度")
    ax.set_ylabel("一次做对比例")
    ax.set_ylim(-0.05, 1.1)
    ax.grid(alpha=0.3)
    ax.legend(title="季度")
    return _png(fig)


def fig_hours(cfg, tasks):
    fig, ax = plt.subplots(figsize=(8, 4))
    done = [t for t in tasks if t["done"] and t["actual_hours"]]
    if not done:
        _empty(ax, "暂无已完成且填写耗时的任务")
        return _png(fig)
    labels = _bucket_labels(cfg)
    months = sorted({t["date"].replace(day=1) for t in done})
    for b, lab in enumerate(labels):
        xs, ys = [], []
        for m in months:
            hs = [t["actual_hours"] for t in done
                  if t["date"].replace(day=1) == m and _bucket_of(t["level"], cfg) == b]
            if hs:
                xs.append(m)
                ys.append(statistics.median(hs))
        if xs:
            ax.plot(xs, ys, marker="o", label=f"难度 {lab}")
    ax.set_ylabel("耗时中位数（小时）")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.grid(alpha=0.3)
    ax.legend()
    return _png(fig)


def _weekly(tasks, fn):
    weeks = {}
    for t in tasks:
        weeks.setdefault(c.week_monday(c.iso_week(t["date"])), []).append(t)
    return sorted((w, *fn(ts)) for w, ts in weeks.items())


def fig_judgment(tasks):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.8))
    judged = [t for t in tasks if t["fjc"] is not None]
    if judged:
        pts = _weekly(judged, lambda ts: (sum(t["fjc"] for t in ts), len(ts)))
        a1.scatter([p[0] for p in pts], [p[1] / p[2] for p in pts], color="#888",
                   label="周度")
        roll = _window_rate(pts, 28, lambda n, m: n / m)
        a1.plot([d for d, _ in roll], [v for _, v in roll], color="#d62728",
                label="4 周滑动")
        a1.set_ylim(-0.05, 1.05)
        a1.legend()
        _date_axis(a1)
    else:
        _empty(a1, "暂无数据")
    a1.set_title("第一判断正确率")
    errs = [(t["date"], abs(t["actual_hours"] - t["predict_hours"]) / t["predict_hours"])
            for t in tasks if t["actual_hours"] and t["predict_hours"]]
    if errs:
        weeks = {}
        for d, e in errs:
            weeks.setdefault(c.week_monday(c.iso_week(d)), []).append(e)
        xs = sorted(weeks)
        a2.scatter(xs, [statistics.median(weeks[w]) for w in xs], color="#888",
                   label="周度中位数")
        roll = [(w, statistics.median([e for x in xs if 0 <= (w - x).days < 28
                                       for e in weeks[x]])) for w in xs]
        a2.plot([d for d, _ in roll], [v for _, v in roll], color="#1f77b4",
                label="4 周滑动")
        a2.legend()
        _date_axis(a2)
    else:
        _empty(a2, "暂无数据")
    a2.set_title("耗时预测误差（越低越准）")
    return _png(fig)


def fig_state(days):
    fig, ax = plt.subplots(figsize=(10, 3.2))
    pts = [(d["date"], d["state"]) for d in days if d["state"] is not None]
    if not pts:
        _empty(ax, "暂无状态记录")
        return _png(fig)
    ax.scatter([d for d, _ in pts], [s for _, s in pts], color="#888", s=15)
    roll = _window_rate([(d, s, 1) for d, s in pts], 7, lambda n, m: n / m)
    ax.plot([d for d, _ in roll], [v for _, v in roll], color="#ff7f0e", label="7 日均线")
    ax.set_ylim(0.5, 5.5)
    ax.set_ylabel("状态 1~5")
    ax.legend()
    _date_axis(ax)
    return _png(fig)


def _rating_at(track, day):
    vals = [r for w, r in track["history"] if c.week_monday(w) <= day]
    return vals[-1] if vals else None


def fig_radar(cfg, tasks, reviews, tracks):
    quarters = sorted({c.quarter(t["date"]) for t in tasks}
                      | {c.quarter(r["date"]) for r in reviews}
                      | {c.quarter(c.week_monday(w))
                         for t in tracks.values() for w, _ in t["history"]})
    axes_names = [_label(t, cfg) for t in cfg["bench_types"]] + ["判断正确率", "照心镜"]
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(projection="polar")
    if not quarters:
        _empty(ax, "暂无数据")
        return _png(fig)
    retro = {}
    for q in quarters:
        ws = [r["weighted"] for r in reviews if c.quarter(r["date"]) == q]
        retro[q] = sum(ws) / len(ws) if ws else 0
    retro_max = max(retro.values()) or 1
    angles = np.linspace(0, 2 * np.pi, len(axes_names), endpoint=False).tolist()
    cmap = plt.get_cmap("viridis", max(len(quarters), 2))
    for qi, q in enumerate(quarters):
        end = c.quarter_end(q)
        vals = []
        for t in cfg["bench_types"]:
            r = _rating_at(tracks[t], end)
            vals.append(0 if r is None else min(1, max(0, (r - 1000) / 1000)))
        judged = [t["fjc"] for t in tasks if c.quarter(t["date"]) == q
                  and t["fjc"] is not None]
        vals.append(sum(judged) / len(judged) if judged else 0)
        vals.append(retro[q] / retro_max)
        ax.plot(angles + angles[:1], vals + vals[:1], color=cmap(qi), label=q)
        ax.fill(angles + angles[:1], vals + vals[:1], color=cmap(qi), alpha=0.1)
    ax.set_xticks(angles, axes_names)
    ax.set_ylim(0, 1)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    return _png(fig)


def _sects(cfg, profile):
    return "、".join(f"{cfg['sects'][k]['name']}（{cfg['sects'][k]['lang']}）"
                    for k in profile["sects"])


def _cards(cfg, tracks):
    out = []
    for key in ["overall", *cfg["bench_types"]]:
        t = tracks[key]
        if t["rating"] is None:
            body = "尚无修为"
        else:
            realm = c.realm_of(t["rating"], cfg)
            body = f"<b>{realm}</b><br>{t['rating']:.0f}"
            if not t["calibrated"]:
                body += f"<br><small>测灵根 {t['weeks_done']}/{t['warmup_weeks']} 周，暂估</small>"
        out.append(f"<div class='card'><div class='k'>{_label(key, cfg)}</div>{body}</div>")
    return "".join(out)


def _retro_table(reviews):
    if not reviews:
        return "<p>暂无记录</p>"
    rows = "".join(
        f"<tr><td>{html.escape(r['month'])}</td><td>{html.escape(str(r['change']))}</td>"
        f"<td>{r['severe']}/{r['normal']}/{r['minor']}</td><td>{r['weighted']}</td>"
        f"<td>{html.escape(str(r['would_rewrite']))}</td><td>{html.escape(str(r['note']))}</td></tr>"
        for r in reviews)
    return ("<table><tr><th>月份</th><th>change</th><th>严重/一般/细节</th>"
            "<th>加权</th><th>会重写</th><th>备注</th></tr>" + rows + "</table>")


SECTIONS = [
    ("修为曲线", "测灵根结束后的周度修为（Elo），背景色为大境界。斜率即修炼速度。", "elo"),
    ("秘境战绩", "每处秘境的得分与用时占时限的比例。", "bench"),
    ("能力边界图", "每季度一条曲线。曲线整体右移，说明能一次做对的难度变高。", "frontier"),
    ("同难度耗时", "每个难度桶的月度耗时中位数。同难度耗时下降，说明速度提升。", "hours"),
    ("神识", "第一判断正确率与耗时预测误差，反映判断力。", "judgment"),
    ("心境", "日度精神状态与 7 日均线，用于区分状态波动与修为变化。", "state"),
    ("季度道基图", "修为按 (R−1000)/1000 归一；照心镜按各季度最大值归一。", "radar"),
]


def build(cfg, profile, days, tasks, reviews, scores, tracks):
    imgs = {
        "elo": fig_elo(cfg, tracks),
        "bench": fig_bench_raw(cfg, scores),
        "frontier": fig_frontier(cfg, tasks),
        "hours": fig_hours(cfg, tasks),
        "judgment": fig_judgment(tasks),
        "state": fig_state(days),
        "radar": fig_radar(cfg, tasks, reviews, tracks),
    }
    sections = "".join(
        f"<h2>{title}</h2><p class='d'>{desc}</p>"
        f"<img src='data:image/png;base64,{imgs[key]}'>"
        for title, desc, key in SECTIONS)
    page = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>修为面板</title><style>
body{{font-family:"Noto Sans CJK SC",sans-serif;max-width:1150px;margin:24px auto;color:#222}}
.cards{{display:flex;gap:12px}}
.card{{flex:1;border:1px solid #ddd;border-radius:8px;padding:12px;text-align:center;font-size:20px}}
.card .k{{font-size:14px;color:#666}}
img{{max-width:100%}} .d{{color:#666}}
table{{border-collapse:collapse}} td,th{{border:1px solid #ddd;padding:4px 8px}}
</style></head><body>
<h1>修为面板</h1>
<p>所修门派：{html.escape(_sects(cfg, profile))}</p>
<p class="d">生成于 {dt.datetime.now():%Y-%m-%d %H:%M}。宗门任务日志 {len(days)} 天，已结束任务 {len(tasks)} 条，
已评定秘境 {len(c.scored_questions(scores))} 处，照心镜 {len(reviews)} 条。</p>
<div class="cards">{_cards(cfg, tracks)}</div>
{sections}
<h2>照心镜明细</h2>{_retro_table(reviews)}
</body></html>"""
    path = c.HOME / "report" / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8")
    return path
