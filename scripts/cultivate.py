#!/usr/bin/env python3
import argparse
import datetime as dt
import subprocess
import sys

import common as c
import elo

OVERALL = "overall"


def track_label(key, cfg):
    return "总修为" if key == OVERALL else f"{cfg['bench_types'][key]['label']}修为"


def rating_text(track, cfg):
    if track["rating"] is None:
        return "尚无修为"
    r = track["rating"]
    if track["calibrated"]:
        return f"{c.realm_of(r, cfg)}（{r:.0f}）"
    return (f"测灵根中 {track['weeks_done']}/{track['warmup_weeks']} 周，"
            f"暂估 {c.realm_of(r, cfg)}（{r:.0f}）")


def require_profile(cfg):
    profile = c.load_profile()
    if profile is None:
        print("【叮！未检测到宿主绑定记录】请先走首次绑定流程：介绍世界、选择门派，"
              "再运行 cultivate.py init --sects <门派>")
        sys.exit(2)
    return profile


def sect_names(profile, cfg):
    return "、".join(f"{cfg['sects'][k]['name']}（{cfg['sects'][k]['lang']}）"
                    for k in profile["sects"])


def cmd_sects(args, cfg):
    for key, s in cfg["sects"].items():
        print(f"{key:7s} {s['name']:6s} {s['lang']:22s} 秘境素材: {', '.join(s['repos'])}")


def cmd_init(args, cfg):
    keys = [k.strip() for k in args.sects.split(",") if k.strip()]
    bad = [k for k in keys if k not in cfg["sects"]]
    if not keys or bad:
        sys.exit(f"未知门派 {bad}，可选: {', '.join(cfg['sects'])}")
    profile = c.load_profile() or {"bound_at": dt.date.today().isoformat()}
    profile["sects"] = keys
    for sub in (c.DAILY_DIR, c.RETRO_DIR, c.BENCH_DIR):
        sub.mkdir(parents=True, exist_ok=True)
    c.save_profile(profile)
    print(f"【叮！宿主绑定成功】所修门派：{sect_names(profile, cfg)}")
    print(f"修行档案：{c.HOME}")


def parse_date(s):
    return dt.date.fromisoformat(s) if s else dt.date.today()


def cmd_day(args, cfg):
    require_profile(cfg)
    day = parse_date(args.date)
    path = c.DAILY_DIR / f"{day:%Y%m%d}.yaml"
    if not path.exists():
        text = (c.TEMPLATE_DIR / "daily.yaml").read_text(encoding="utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text.format(date=day.isoformat(), compact=f"{day:%Y%m%d}"),
                        encoding="utf-8")
    print(path)


def cmd_retro(args, cfg):
    require_profile(cfg)
    month = args.month or f"{dt.date.today():%Y-%m}"
    dt.datetime.strptime(month, "%Y-%m")
    path = c.RETRO_DIR / f"{month}.yaml"
    if not path.exists():
        text = (c.TEMPLATE_DIR / "retro.yaml").read_text(encoding="utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text.format(month=month), encoding="utf-8")
    print(path)


def cmd_week(args, cfg):
    profile = require_profile(cfg)
    week = args.week or c.iso_week(dt.date.today())
    c.week_monday(week)
    for sub in ("weekly", "answers", "sealed"):
        (c.BENCH_DIR / sub / week).mkdir(parents=True, exist_ok=True)
    scores = c.load_scores()
    tracks = elo.compute(scores, cfg)
    print(f"周次: {week}  所修门派: {sect_names(profile, cfg)}")
    for t, spec in cfg["bench_types"].items():
        tr = tracks[t]
        print(f"  {spec['label']}秘境({t}): {rating_text(tr, cfg)}  "
              f"建议品阶 level={elo.suggested_level(tr, cfg)}  "
              f"默认时限 {spec['time_limit_min']} 分钟")
    qs = [q for q in scores["questions"] if q["week"] == week]
    print(f"本周已开启秘境 {len(qs)} 处")
    for q in qs:
        print(f"  {q['id']}  {q['status']}  {q['project']}  {q['title']}")
    recent = [q["project"] for q in scores["questions"]][-9:]
    if recent:
        print(f"近期用过的素材: {', '.join(recent)}")


def cmd_repo(args, cfg):
    profile = require_profile(cfg)
    repos = c.repo_registry(cfg, profile)
    if args.action == "list":
        for name, spec in repos.items():
            cloned = "已克隆" if (c.BENCH_DIR / "repos" / name).exists() else "-"
            print(f"{name:16s} {spec['sect']:6s} {spec['lang']:22s} {cloned}")
        return
    if args.name not in repos:
        sys.exit(f"所修门派中没有素材 {args.name}，可选: {', '.join(repos)}")
    dest = c.BENCH_DIR / "repos" / args.name
    if dest.exists():
        subprocess.run(["git", "-C", str(dest), "fetch", "--all", "--tags", "-q"],
                       check=True)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--filter=blob:none",
                        repos[args.name]["url"], str(dest)], check=True)
    print(dest)


def cmd_snapshot(args, cfg):
    require_profile(cfg)
    repo = c.BENCH_DIR / "repos" / args.repo
    if not repo.exists():
        sys.exit(f"{repo} 不存在，先运行 cultivate.py repo clone {args.repo}")
    dest = c.HOME / args.dest
    if dest.exists() and any(dest.iterdir()):
        sys.exit(f"{dest} 已存在且非空")
    dest.mkdir(parents=True, exist_ok=True)
    archive = subprocess.Popen(["git", "-C", str(repo), "archive", "--format=tar",
                                args.commit], stdout=subprocess.PIPE)
    subprocess.run(["tar", "-x", "-C", str(dest)], stdin=archive.stdout, check=True)
    archive.stdout.close()
    if archive.wait() != 0:
        sys.exit("git archive 失败")
    if args.patch:
        subprocess.run(["patch", "-p1", "-d", str(dest), "-i", args.patch], check=True)
    print(dest)


def parse_kv(text):
    out = {}
    for part in text.split(","):
        k, v = part.split("=")
        out[k.strip()] = int(v)
    return out


def cmd_add(args, cfg):
    profile = require_profile(cfg)
    spec = cfg["bench_types"][args.type]
    difficulty = parse_kv(args.difficulty)
    errors = []
    c.check_difficulty(difficulty, spec["features"], "difficulty", errors)
    if errors:
        sys.exit("\n".join(errors))
    if args.project != "none" and args.project not in c.repo_registry(cfg, profile):
        sys.exit(f"所修门派中没有素材 {args.project}。可在 {c.HOME}/config.yaml 的 "
                 f"extra_repos 中添加；与素材无关的题用 none")
    week = args.week or c.iso_week(dt.date.today())
    c.week_monday(week)
    scores = c.load_scores()
    ids = {q["id"] for q in scores["questions"]}
    qid, n = f"{week}-{args.type}", 2
    while qid in ids:
        qid, n = f"{week}-{args.type}-{n}", n + 1
    limit = args.time_limit or spec["time_limit_min"]
    q = {
        "id": qid,
        "week": week,
        "type": args.type,
        "project": args.project,
        "source": args.source,
        "title": args.title,
        "difficulty": difficulty,
        "level": c.level(difficulty),
        "time_limit_min": limit,
        "issued_at": dt.datetime.now().isoformat(timespec="seconds"),
        "status": "open",
    }
    scores["questions"].append(q)
    c.save_scores(scores)
    qdir = c.BENCH_DIR / "weekly" / week / qid
    qdir.mkdir(parents=True, exist_ok=True)
    (c.BENCH_DIR / "sealed" / week).mkdir(parents=True, exist_ok=True)
    (c.BENCH_DIR / "answers" / week).mkdir(parents=True, exist_ok=True)
    readme = qdir / "README.md"
    if not readme.exists():
        text = (c.TEMPLATE_DIR / "question.md").read_text(encoding="utf-8")
        readme.write_text(text.format(
            qid=qid, title=args.title, type_label=spec["label"], level=q["level"],
            project=args.project, time_limit=limit, code_dir=qdir / "src",
            answer_path=c.BENCH_DIR / "answers" / week / f"{qid}.md"), encoding="utf-8")
    print(f"已开启秘境 {qid}  品阶 level={q['level']}  D={elo.difficulty_score(q, cfg)}")
    print(f"题面: {readme}")
    print(f"天机: {c.BENCH_DIR / 'sealed' / week / (qid + '.md')}")


def _snapshot_realms(tracks, keys, cfg):
    return {k: c.realm_of(tracks[k]["rating"], cfg)
            if tracks[k]["calibrated"] and tracks[k]["rating"] is not None else None
            for k in keys}


def cmd_score(args, cfg):
    require_profile(cfg)
    if not 0 <= args.s <= 1:
        sys.exit("s 必须在 0~1")
    if args.minutes <= 0:
        sys.exit("minutes 必须为正数")
    scores = c.load_scores()
    q = next((q for q in scores["questions"] if q["id"] == args.qid), None)
    if q is None:
        sys.exit(f"找不到秘境 {args.qid}")
    if q["status"] == "scored" and not args.force:
        sys.exit(f"{args.qid} 已评分，覆盖请加 --force")
    keys = (q["type"], OVERALL)
    before_tracks = elo.compute(scores, cfg)
    before = _snapshot_realms(before_tracks, keys, cfg)
    q["status"] = "scored"
    q["result"] = {
        "s": args.s,
        "minutes": args.minutes,
        "scored_at": dt.datetime.now().isoformat(timespec="seconds"),
        "grader": args.grader,
        "note": args.note or "",
    }
    c.save_scores(scores)
    tracks = elo.compute(scores, cfg)
    after = _snapshot_realms(tracks, keys, cfg)
    print(f"{args.qid}: s={args.s} 用时 {args.minutes} 分钟")
    for key in keys:
        print(f"  {track_label(key, cfg)}: {rating_text(tracks[key], cfg)}")
        if not before_tracks[key]["calibrated"] and tracks[key]["calibrated"]:
            print(f"  【灵根测定完成】{track_label(key, cfg)}定为 {after[key]}")
        elif before[key] and after[key] and before[key] != after[key]:
            up = tracks[key]["rating"] > before_tracks[key]["rating"]
            print(f"  【{'突破' if up else '跌境'}】{track_label(key, cfg)}："
                  f"{before[key]} → {after[key]}")


def run_check(cfg):
    errors, warnings = [], []
    days, tasks = c.load_daily(cfg, errors, warnings)
    reviews = c.load_retro(errors)
    scores = c.load_scores()
    c.check_scores(scores, cfg, errors)
    return days, tasks, reviews, scores, errors, warnings


def cmd_check(args, cfg):
    require_profile(cfg)
    days, tasks, reviews, scores, errors, warnings = run_check(cfg)
    print(f"宗门任务日志 {len(days)} 天，已结束任务 {len(tasks)} 条；"
          f"照心镜 {len(reviews)} 条；秘境 {len(scores['questions'])} 处")
    for w in warnings:
        print(f"[警告] {w}")
    for e in errors:
        print(f"[错误] {e}")
    if errors:
        sys.exit(1)


def cmd_status(args, cfg):
    profile = require_profile(cfg)
    days, tasks, reviews, scores, errors, warnings = run_check(cfg)
    tracks = elo.compute(scores, cfg)
    print(f"== 宿主档案 ==\n  绑定于 {profile['bound_at']}，所修门派：{sect_names(profile, cfg)}")
    print("== 修为 ==")
    for key in [OVERALL, *cfg["bench_types"]]:
        print(f"  {track_label(key, cfg)}: {rating_text(tracks[key], cfg)}")
    open_qs = [q for q in scores["questions"] if q["status"] == "open"]
    print(f"== 未评定秘境 {len(open_qs)} 处 ==")
    for q in open_qs:
        print(f"  {q['id']}  {q['project']}  {q['title']}")
    since = dt.date.today() - dt.timedelta(days=6)
    recent_days = [d for d in days if d["date"] >= since]
    recent_tasks = [t for t in tasks if t["date"] >= since]
    print(f"== 近 7 天 ==\n  任务日志 {len(recent_days)} 天，已结束任务 {len(recent_tasks)} 条")
    last_retro = max((r["month"] for r in reviews), default="无")
    print(f"== 最近一次照心镜: {last_retro} ==")
    if errors or warnings:
        print(f"记录文件有 {len(errors)} 个错误、{len(warnings)} 个警告，"
              f"运行 cultivate.py check 查看")


def cmd_report(args, cfg):
    import report
    profile = require_profile(cfg)
    days, tasks, reviews, scores, errors, warnings = run_check(cfg)
    if errors:
        print("\n".join(f"[错误] {e}" for e in errors))
        sys.exit("记录文件有错误，修正后再生成修为面板")
    path = report.build(cfg, profile, days, tasks, reviews, scores,
                        elo.compute(scores, cfg))
    print(path)


def main():
    p = argparse.ArgumentParser(prog="cultivate.py", description="程序员修仙系统")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("sects", help="列出全部门派")
    s = sub.add_parser("init", help="绑定宿主并选择门派")
    s.add_argument("--sects", required=True, help="门派 key，逗号分隔，如 cpp,python")
    s = sub.add_parser("day", help="生成宗门任务日志")
    s.add_argument("--date")
    s = sub.add_parser("retro", help="生成照心镜记录")
    s.add_argument("--month")
    s = sub.add_parser("week", help="创建本周秘境目录并显示建议品阶")
    s.add_argument("--week")

    s = sub.add_parser("repo", help="管理秘境素材仓库")
    s.add_argument("action", choices=["list", "clone"])
    s.add_argument("name", nargs="?")

    s = sub.add_parser("snapshot", help="导出不含 .git 的代码快照")
    s.add_argument("--repo", required=True)
    s.add_argument("--commit", required=True)
    s.add_argument("--dest", required=True, help="相对修行档案目录或绝对路径")
    s.add_argument("--patch")

    s = sub.add_parser("add", help="开启秘境（登记题目）")
    s.add_argument("--type", required=True, choices=["debug", "read", "design"])
    s.add_argument("--project", required=True)
    s.add_argument("--source", required=True, choices=["real", "injected", "na"])
    s.add_argument("--title", required=True)
    s.add_argument("--difficulty", required=True, help="如 distance=2,bug_kind=1,...")
    s.add_argument("--time-limit", type=int)
    s.add_argument("--week")

    s = sub.add_parser("score", help="评定秘境成绩")
    s.add_argument("qid")
    s.add_argument("--s", type=float, required=True)
    s.add_argument("--minutes", type=float, required=True)
    s.add_argument("--grader", required=True, help="评分者，填模型名")
    s.add_argument("--note")
    s.add_argument("--force", action="store_true")

    sub.add_parser("check", help="校验记录文件")
    sub.add_parser("status", help="宿主状态")
    sub.add_parser("report", help="生成修为面板 HTML")

    args = p.parse_args()
    if args.cmd == "repo" and args.action == "clone" and not args.name:
        p.error("repo clone 需要素材名")
    cfg = c.load_config()
    globals()[f"cmd_{args.cmd}"](args, cfg)


if __name__ == "__main__":
    main()
