import math
import uuid
from collections import defaultdict
from typing import Any

from backend.models.repository import load_graph_snapshot, save_recommendation_run


ALGORITHM_NAME = "graph_hybrid_v1"

INTERACTION_WEIGHTS = {
    "view": 0.15,
    "click": 0.35,
    "like": 1.0,
    "share": 0.75,
    "purchase": 1.35,
    "dismiss": -1.0,
}


def _positive_weighted_jaccard(left: dict[int, float], right: dict[int, float]) -> float:
    left_positive = {item: weight for item, weight in left.items() if weight > 0}
    right_positive = {item: weight for item, weight in right.items() if weight > 0}
    union = left_positive.keys() | right_positive.keys()
    if not union:
        return 0.0
    shared = sum(min(left_positive.get(item, 0), right_positive.get(item, 0)) for item in union)
    total = sum(max(left_positive.get(item, 0), right_positive.get(item, 0)) for item in union)
    return shared / total if total else 0.0


def recommend_for_user(user_id: int, limit: int = 8) -> dict[str, Any]:
    graph = load_graph_snapshot(user_id)
    edges: dict[int, dict[int, float]] = defaultdict(lambda: defaultdict(float))
    seen_by_user: dict[int, set[int]] = defaultdict(set)
    dismissed_by_user: dict[int, set[int]] = defaultdict(set)

    for interaction in graph["interactions"]:
        owner = int(interaction["user_id"])
        item_id = int(interaction["item_id"])
        kind = interaction["interaction_type"]
        seen_by_user[owner].add(item_id)
        if kind == "dismiss":
            dismissed_by_user[owner].add(item_id)
            continue
        edges[owner][item_id] += (
            INTERACTION_WEIGHTS[kind] * float(interaction["strength"])
        )

    for rating in graph["ratings"]:
        owner = int(rating["user_id"])
        item_id = int(rating["item_id"])
        seen_by_user[owner].add(item_id)
        preference = (int(rating["rating"]) - 3) * 0.45
        if preference > 0:
            edges[owner][item_id] += preference

    for saved in graph["saved_items"]:
        owner = int(saved["user_id"])
        item_id = int(saved["item_id"])
        seen_by_user[owner].add(item_id)
        edges[owner][item_id] += 1.1

    target_edges = edges.get(user_id, {})
    similarities = {
        other_user: _positive_weighted_jaccard(target_edges, other_edges)
        for other_user, other_edges in edges.items()
        if other_user != user_id
    }
    similarities = {owner: score for owner, score in similarities.items() if score > 0}

    collaborative: dict[int, float] = defaultdict(float)
    for neighbor_id, similarity in similarities.items():
        for item_id, weight in edges[neighbor_id].items():
            if item_id not in seen_by_user[user_id] and weight > 0:
                collaborative[item_id] += similarity * weight

    interest_weights: dict[int, dict[int, float]] = defaultdict(dict)
    for interest in graph["interests"]:
        interest_weights[int(interest["user_id"])][int(interest["category_id"])] = float(
            interest["interest_weight"]
        )
    target_interests = interest_weights[user_id]

    categories = {
        int(category["category_id"]): category
        for category in graph["categories"]
    }
    popularity_max = max(
        (int(item["interaction_count"]) + int(item["rating_count"]) for item in graph["items"]),
        default=0,
    )
    collaboration_max = max(collaborative.values(), default=0.0)
    run_id = str(uuid.uuid4())
    ranked: list[dict[str, Any]] = []

    for item in graph["items"]:
        item_id = int(item["item_id"])
        if item_id in seen_by_user[user_id] or item_id in dismissed_by_user[user_id]:
            continue

        interest_score = 0.0
        matched_category = None
        category_id = int(item["category_id"])
        depth = 0
        while category_id in categories:
            weight = target_interests.get(category_id, 0.0) * (0.8**depth)
            if weight > interest_score:
                interest_score = weight
                matched_category = categories[category_id]["name"]
            parent_id = categories[category_id]["parent_category_id"]
            if parent_id is None:
                break
            category_id = int(parent_id)
            depth += 1

        collaborative_score = (
            collaborative.get(item_id, 0.0) / collaboration_max
            if collaboration_max
            else 0.0
        )
        popularity = int(item["interaction_count"]) + int(item["rating_count"])
        popularity_score = (
            math.log1p(popularity) / math.log1p(popularity_max)
            if popularity_max
            else 0.0
        )
        quality_score = float(item["average_rating"]) / 5.0
        score = (
            0.56 * collaborative_score
            + 0.27 * interest_score
            + 0.11 * popularity_score
            + 0.06 * quality_score
        )
        if collaborative_score >= 0.2:
            reason = "Graph match from people with similar activity"
        elif matched_category:
            reason = f"Matches your interest in {matched_category}"
        else:
            reason = "Popular with the community"

        ranked.append(
            {
                **item,
                "score": round(min(score, 1.0), 7),
                "reason": reason,
            }
        )

    ranked.sort(key=lambda item: (-item["score"], item["title"].casefold()))
    recommendations = ranked[:limit]
    for position, item in enumerate(recommendations, start=1):
        item["rank_position"] = position

    save_recommendation_run(
        [
            (
                run_id,
                user_id,
                item["item_id"],
                item["score"],
                item["rank_position"],
                ALGORITHM_NAME,
            )
            for item in recommendations
        ]
    )
    return {
        "run_id": run_id,
        "algorithm": ALGORITHM_NAME,
        "recommendations": recommendations,
    }
