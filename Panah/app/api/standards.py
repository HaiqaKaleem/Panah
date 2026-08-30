from fastapi import APIRouter, Query

from app.rules import (
    extract_sphere_rules,
    get_rule,
    rules_by_category,
    get_sphere_rules,
)

router = APIRouter(prefix="/standards", tags=["Standards"])


@router.get("/rules")
def list_rules(category: str | None = Query(default=None)):
    """Return Sphere Handbook rules, optionally filtered by category."""
    if category:
        rules = rules_by_category(category)
        return {
            "standard": "Sphere Handbook",
            "version": "V24.1",
            "count": len(rules),
            "rules": [r.to_dict() for r in rules],
        }

    return {
        "standard": "Sphere Handbook",
        "version": "V24.1",
        "count": len(get_sphere_rules()),
        "rules": extract_sphere_rules(),
    }


@router.get("/rules/{rule_id}")
def get_rule_detail(rule_id: str):
    """Return a single rule by ID."""
    try:
        rule = get_rule(rule_id)
    except KeyError:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")

    return rule.to_dict()


@router.get("/categories")
def list_categories():
    """Return available rule categories."""
    rules = get_sphere_rules()
    categories = sorted(set(r.category for r in rules))
    return {
        "categories": [
            {
                "category": cat,
                "count": len(rules_by_category(cat)),
            }
            for cat in categories
        ]
    }
