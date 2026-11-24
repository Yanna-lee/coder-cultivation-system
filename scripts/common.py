import datetime as dt
import os
from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "templates"
HOME = Path(os.environ.get("CULTIVATION_HOME", Path.home() / ".coder-cultivation"))
DAILY_DIR = HOME / "daily"
RETRO_DIR = HOME / "retro"
BENCH_DIR = HOME / "bench"
SCORES_PATH = BENCH_DIR / "scores.yaml"
PROFILE_PATH = HOME / "profile.yaml"


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def dump_yaml(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# 由 cultivate.py 维护，不要手工编辑\n")
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def _merge(base, override):
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
    return base


def load_config():
    cfg = load_yaml(SKILL_DIR / "config.default.yaml")
    user = HOME / "config.yaml"
    return _merge(cfg, load_yaml(user)) if user.exists() else cfg


def load_profile():
    return load_yaml(PROFILE_PATH) if PROFILE_PATH.exists() else None


def save_profile(profile):
    dump_yaml(PROFILE_PATH, profile)


def repo_registry(cfg, profile):
    out = {}
    for key in profile["sects"]:
        sect = cfg["sects"][key]
        for name, url in sect["repos"].items():
            out[name] = {"url": url, "sect": sect["name"], "lang": sect["lang"]}
    for name, spec in (cfg.get("extra_repos") or {}).items():
        out[name] = {"url": spec["url"], "sect": spec.get("sect", "散修"),
                     "lang": spec.get("lang", "")}
    return out


def iso_week(day):
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"


def week_monday(week):
    year, num = week.split("-W")
    return dt.date.fromisocalendar(int(year), int(num), 1)


def quarter(day):
    return f"{day.year}Q{(day.month - 1) // 3 + 1}"


def quarter_end(q):
    year, num = int(q[:4]), int(q[-1])
    first_of_next = dt.date(year + num // 4, num % 4 * 3 + 1, 1)
    return first_of_next - dt.timedelta(days=1)


def level(difficulty):
    return sum(difficulty.values())


def major_realm(rating, cfg):
    realms = cfg["realms"]
    idx = max(i for i, r in enumerate(realms) if rating >= r["min"] or i == 0)
    return idx, realms[idx]


def realm_of(rating, cfg):
    idx, realm = major_realm(rating, cfg)
    stages, step = cfg["minor_stages"], cfg["minor_step"]
    start = realm["min"]
    if idx == 0 and len(cfg["realms"]) > 1:
        start = cfg["realms"][1]["min"] - len(stages) * step
    stage = int(max(0, rating - start) // step)
    last = idx == len(cfg["realms"]) - 1
    stage = stage % len(stages) if last else min(stage, len(stages) - 1)
    return f"{realm['name']}{stages[stage]}"


def load_scores():
    if not SCORES_PATH.exists():
        return {"questions": []}
    data = load_yaml(SCORES_PATH)
    data.setdefault("questions", [])
    return data


def save_scores(data):
    dump_yaml(SCORES_PATH, data)


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def check_difficulty(diff, features, where, errors):
    if not isinstance(diff, dict) or set(diff) != set(features):
        errors.append(f"{where}: difficulty 必须恰好包含 {features}")
        return False
    bad = [k for k, v in diff.items()
           if not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 3]
    if bad:
        errors.append(f"{where}: difficulty {bad} 必须是 0~3 的整数")
        return False
    return True


def load_daily(cfg, errors, warnings):
    days, tasks = [], []
    for path in sorted(DAILY_DIR.glob("*.yaml")):
        where = path.name
        try:
            data = load_yaml(path)
        except yaml.YAMLError as e:
            errors.append(f"{where}: YAML 解析失败 {e}")
            continue
        date = data.get("date")
        if not isinstance(date, dt.date) or date.strftime("%Y%m%d") != path.stem:
            errors.append(f"{where}: date 缺失或与文件名不一致")
            continue
        state = data.get("state")
        if state is not None and (not isinstance(state, int) or not 1 <= state <= 5):
            errors.append(f"{where}: state 必须是 1~5 的整数")
            state = None
        days.append({"date": date, "state": state})
        for i, t in enumerate(data.get("tasks") or []):
            task = _parse_task(t, date, cfg, f"{where} tasks[{i}]", errors, warnings)
            if task:
                tasks.append(task)
    return days, tasks


def _parse_task(t, date, cfg, where, errors, warnings):
    if not isinstance(t, dict) or not t.get("title"):
        return None
    if not check_difficulty(t.get("difficulty"), cfg["daily_features"], where, errors):
        return None
    predict = t.get("predict") or {}
    actual = t.get("actual") or {}
    done = actual.get("done")
    if done is None:
        return None
    if not isinstance(done, bool):
        errors.append(f"{where}: actual.done 必须是 true/false")
        return None
    fjc = actual.get("first_judgment_correct")
    if fjc is not None and not isinstance(fjc, bool):
        errors.append(f"{where}: first_judgment_correct 必须是 true/false")
        fjc = None
    if fjc is None:
        warnings.append(f"{where}: 已结束但 first_judgment_correct 未填")
    p_hours, a_hours = predict.get("hours"), actual.get("hours")
    for name, v in (("predict.hours", p_hours), ("actual.hours", a_hours)):
        if v is not None and (not _is_num(v) or v <= 0):
            errors.append(f"{where}: {name} 必须是正数")
            return None
    if a_hours is None:
        warnings.append(f"{where}: 已结束但 actual.hours 未填")
    stuck = actual.get("stuck_30min") or 0
    if not isinstance(stuck, int) or stuck < 0:
        errors.append(f"{where}: stuck_30min 必须是非负整数")
        stuck = 0
    return {
        "date": date,
        "id": t.get("id"),
        "title": t["title"],
        "level": level(t["difficulty"]),
        "predict_hours": p_hours,
        "actual_hours": a_hours,
        "fjc": fjc,
        "stuck": stuck,
        "done": done,
        "one_shot": done and fjc is True,
    }


def load_retro(errors):
    reviews = []
    for path in sorted(RETRO_DIR.glob("*.yaml")):
        where = path.name
        try:
            data = load_yaml(path)
        except yaml.YAMLError as e:
            errors.append(f"{where}: YAML 解析失败 {e}")
            continue
        month = str(data.get("month", ""))
        try:
            day = dt.datetime.strptime(month, "%Y-%m").date()
        except ValueError:
            errors.append(f"{where}: month 必须是 YYYY-MM")
            continue
        for i, r in enumerate(data.get("reviews") or []):
            if not isinstance(r, dict) or r.get("change") is None:
                continue
            issues = r.get("issues") or {}
            vals = [issues.get(k, 0) for k in ("severe", "normal", "minor")]
            if not all(isinstance(v, int) and v >= 0 for v in vals):
                errors.append(f"{where} reviews[{i}]: issues 必须是非负整数")
                continue
            severe, normal, minor = vals
            reviews.append({
                "month": month,
                "date": day,
                "change": r["change"],
                "severe": severe,
                "normal": normal,
                "minor": minor,
                "weighted": 3 * severe + 2 * normal + minor,
                "would_rewrite": r.get("would_rewrite"),
                "note": r.get("note") or "",
            })
    return reviews


def check_scores(data, cfg, errors):
    types = cfg["bench_types"]
    seen = set()
    for q in data["questions"]:
        qid = q.get("id")
        if qid in seen:
            errors.append(f"scores.yaml: 秘境 id 重复 {qid}")
        seen.add(qid)
        if q.get("type") not in types:
            errors.append(f"scores.yaml {qid}: 未知秘境类型 {q.get('type')}")
            continue
        check_difficulty(q.get("difficulty"), types[q["type"]]["features"],
                         f"scores.yaml {qid}", errors)
        if q.get("status") == "scored":
            s = (q.get("result") or {}).get("s")
            if not _is_num(s) or not 0 <= s <= 1:
                errors.append(f"scores.yaml {qid}: result.s 必须在 0~1")


def scored_questions(data):
    qs = [q for q in data["questions"] if q.get("status") == "scored"]
    return sorted(qs, key=lambda q: (q["week"], q["result"]["scored_at"], q["id"]))
