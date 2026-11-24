from common import level, scored_questions


def expected(rating, d):
    return 1 / (1 + 10 ** ((d - rating) / 400))


def difficulty_score(q, cfg):
    return cfg["elo"]["base"] + level(q["difficulty"]) * cfg["elo"]["step"]


def performance_rating(items):
    ds = [d for d, _ in items]
    total = sum(s for _, s in items)
    if total <= 0:
        return min(ds) - 400
    if total >= len(items):
        return max(ds) + 400
    lo, hi = min(ds) - 1000, max(ds) + 1000
    for _ in range(100):
        mid = (lo + hi) / 2
        if sum(expected(mid, d) for d in ds) < total:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _track(questions, cfg):
    warmup = cfg["elo"]["warmup_weeks"]
    k = cfg["elo"]["k"]
    items = [(q["week"], difficulty_score(q, cfg), q["result"]["s"])
             for q in questions]
    weeks = sorted({w for w, _, _ in items})
    track = {"weeks_done": len(weeks), "warmup_weeks": warmup,
             "calibrated": len(weeks) >= warmup, "rating": None, "history": []}
    if not items:
        return track
    if not track["calibrated"]:
        track["rating"] = performance_rating([(d, s) for _, d, s in items])
        return track
    warm_weeks = set(weeks[:warmup])
    rating = performance_rating([(d, s) for w, d, s in items if w in warm_weeks])
    history = [(weeks[warmup - 1], rating)]
    for w, d, s in items:
        if w in warm_weeks:
            continue
        rating += k * (s - expected(rating, d))
        if history[-1][0] == w:
            history[-1] = (w, rating)
        else:
            history.append((w, rating))
    track["rating"] = rating
    track["history"] = history
    return track


def compute(scores, cfg):
    qs = scored_questions(scores)
    result = {t: _track([q for q in qs if q["type"] == t], cfg)
              for t in cfg["bench_types"]}
    result["overall"] = _track(qs, cfg)
    return result


def suggested_level(track, cfg):
    if not track["calibrated"]:
        return "4~6（测灵根期）"
    e = cfg["elo"]
    lv = round((track["rating"] + 100 - e["base"]) / e["step"])
    return str(min(12, max(0, lv)))
