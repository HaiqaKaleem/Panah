"""
Deterministic Validation Engine

Loads YAML rule definitions from the rules/ directory and executes them
against a ValidationContext. No LLM calls — pure deterministic checks.

Rules follow the Sphere Handbook and structural engineering best practices.
"""
import os
import glob
import yaml
from typing import List, Optional
from .context import ValidationContext
from .result import RuleResult, Severity, ValidationReport


def _load_rules_from_directory(rules_dir: str) -> dict:
    """Load all YAML rule files from the rules directory."""
    rules = {}
    pattern = os.path.join(rules_dir, "*.yaml")
    for filepath in glob.glob(pattern):
        with open(filepath, "r") as f:
            rule_def = yaml.safe_load(f)
        if rule_def and "id" in rule_def:
            rules[rule_def["id"]] = rule_def
    return rules


class ValidationEngine:
    """
    Deterministic rule engine that evaluates a set of YAML-defined rules
    against a ValidationContext.

    Usage:
        engine = ValidationEngine()
        report = engine.validate(context)
    """

    def __init__(self, rules_dir: Optional[str] = None):
        if rules_dir is None:
            rules_dir = os.path.join(os.path.dirname(__file__), "rules")
        self.rules_dir = rules_dir
        self._rules = None

    @property
    def rules(self) -> dict:
        if self._rules is None:
            self._rules = _load_rules_from_directory(self.rules_dir)
        return self._rules

    def reload_rules(self):
        """Force reload rules from disk."""
        self._rules = _load_rules_from_directory(self.rules_dir)

    def validate(self, context: ValidationContext, rule_ids: Optional[List[str]] = None) -> ValidationReport:
        """
        Run all (or selected) rules against the context.

        Args:
            context: The validation context with design, materials, and environment data.
            rule_ids: Optional list of specific rule IDs to run. If None, runs all.

        Returns:
            ValidationReport with individual RuleResults and a summary.
        """
        results: List[RuleResult] = []
        target_rules = rule_ids or list(self.rules.keys())

        for rule_id in target_rules:
            rule_def = self.rules.get(rule_id)
            if rule_def is None:
                results.append(RuleResult(
                    rule_id=rule_id,
                    status="error",
                    message=f"Rule definition not found: {rule_id}",
                    severity=Severity.ERROR,
                ))
                continue

            result = self._evaluate_rule(rule_def, context)
            results.append(result)

        return ValidationReport.from_results(results)

    def _evaluate_rule(self, rule_def: dict, context: ValidationContext) -> RuleResult:
        """Evaluate a single rule definition against the context."""
        rule_id = rule_def["id"]
        rule_name = rule_def.get("name", rule_id)
        severity_str = str(rule_def.get("severity", "error")).upper()
        severity = Severity.ERROR
        for s in Severity:
            if s.value.upper() == severity_str:
                severity = s
                break
        rule_config = rule_def.get("rule", {})
        method = rule_config.get("method", "unknown")
        messages = rule_def.get("messages", {})

        try:
            handler = getattr(self, f"_eval_{method}", None)
            if handler is None:
                return RuleResult(
                    rule_id=rule_id, rule_name=rule_name, status="error",
                    message=f"Unknown rule method: {method}", severity=severity,
                )
            return handler(rule_id, rule_name, rule_config, severity, messages, context)
        except Exception as exc:
            return RuleResult(
                rule_id=rule_id, rule_name=rule_name, status="error",
                message=f"Rule evaluation failed: {exc}", severity=severity,
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_nested(self, obj, dotted_field):
        """Get a value from a nested object/dict using dot notation."""
        keys = dotted_field.split(".")
        current = obj
        for key in keys:
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(key)
            elif hasattr(current, key):
                current = getattr(current, key)
            else:
                try:
                    idx = int(key)
                    if isinstance(current, (list, tuple)) and idx < len(current):
                        current = current[idx]
                    else:
                        return None
                except (ValueError, TypeError):
                    return None
        return current

    def _to_number(self, value) -> Optional[float]:
        """Convert value to a number, returning None if not possible."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    # ------------------------------------------------------------------
    # Single-field methods
    # ------------------------------------------------------------------

    def _eval_min_threshold(self, rule_id, rule_name, rule_config, severity, messages, context):
        """Check that a numeric field is >= threshold."""
        field = rule_config["field"]
        threshold = float(rule_config["threshold"])
        value = self._to_number(self._get_nested(context.to_dict(), field))

        if value is None:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="skip",
                              message=f"Field '{field}' not found in context", severity=severity)

        if value >= threshold:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="pass",
                              message=messages.get("pass", f"{field}={value} >= {threshold}"),
                              severity=severity, details={"field": field, "value": value, "threshold": threshold})
        return RuleResult(rule_id=rule_id, rule_name=rule_name, status="fail",
                          message=messages.get("fail", f"{field}={value} < {threshold}").replace("{value}", str(value)).replace("{threshold}", str(threshold)),
                          severity=severity, details={"field": field, "value": value, "threshold": threshold})

    def _eval_max_threshold(self, rule_id, rule_name, rule_config, severity, messages, context):
        """Check that a numeric field is <= threshold."""
        field = rule_config["field"]
        threshold = float(rule_config["threshold"])
        value = self._to_number(self._get_nested(context.to_dict(), field))

        if value is None:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="skip",
                              message=f"Field '{field}' not found in context", severity=severity)

        if value <= threshold:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="pass",
                              message=messages.get("pass", f"{field}={value} <= {threshold}"),
                              severity=severity, details={"field": field, "value": value, "threshold": threshold})
        return RuleResult(rule_id=rule_id, rule_name=rule_name, status="fail",
                          message=messages.get("fail", f"{field}={value} > {threshold}").replace("{value}", str(value)).replace("{threshold}", str(threshold)),
                          severity=severity, details={"field": field, "value": value, "threshold": threshold})

    def _eval_min_length(self, rule_id, rule_name, rule_config, severity, messages, context):
        """Check that a list or dict has at least min_length items."""
        field = rule_config["field"]
        min_length = int(rule_config["min_length"])
        value = self._get_nested(context.to_dict(), field)

        if value is None:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="fail",
                              message=messages.get("fail", f"Field '{field}' is not a list or is empty"),
                              severity=severity)

        if isinstance(value, dict):
            count = len(value)
        elif isinstance(value, list):
            count = len(value)
        else:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="fail",
                              message=messages.get("fail", f"Field '{field}' is not a list or dict"),
                              severity=severity)

        if count >= min_length:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="pass",
                              message=messages.get("pass", f"{field} has {count} items (>= {min_length})"),
                              severity=severity, details={"field": field, "count": count, "min": min_length})
        return RuleResult(rule_id=rule_id, rule_name=rule_name, status="fail",
                          message=messages.get("fail", f"{field} has {count} items (< {min_length})"),
                          severity=severity, details={"field": field, "count": count, "min": min_length})

    def _eval_enum_exists(self, rule_id, rule_name, rule_config, severity, messages, context):
        """Check that a string field has a non-empty value."""
        field = rule_config["field"]
        value = self._get_nested(context.to_dict(), field)

        if value is not None and str(value).strip():
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="pass",
                              message=messages.get("pass", f"Field '{field}' has value: {value}"),
                              severity=severity, details={"field": field, "value": str(value)})
        return RuleResult(rule_id=rule_id, rule_name=rule_name, status="fail",
                          message=messages.get("fail", f"Field '{field}' is missing or empty"),
                          severity=severity, details={"field": field, "value": value})

    def _eval_set_membership(self, rule_id, rule_name, rule_config, severity, messages, context):
        """Check that all values in a list belong to a valid set."""
        field = rule_config["field"]
        valid_set = set(rule_config.get("valid_set", []))
        value = self._get_nested(context.to_dict(), field)

        if value is None or not isinstance(value, list):
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="fail",
                              message=messages.get("fail", f"Field '{field}' is not a list"),
                              severity=severity)

        invalid = [v for v in value if v not in valid_set]
        if not invalid:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="pass",
                              message=messages.get("pass", f"All values in '{field}' are in valid set"),
                              severity=severity, details={"field": field, "values": value})
        msg = messages.get("fail", f"Unsupported values found: {{unsupported_types}}")
        msg = msg.replace("{unsupported_types}", str(invalid))
        return RuleResult(rule_id=rule_id, rule_name=rule_name, status="fail",
                          message=msg, severity=severity,
                          details={"field": field, "invalid": invalid, "valid_set": sorted(valid_set)})

    def _eval_positive_value(self, rule_id, rule_name, rule_config, severity, messages, context):
        """Check that a numeric field is > 0."""
        field = rule_config["field"]
        value = self._to_number(self._get_nested(context.to_dict(), field))

        if value is None:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="skip",
                              message=f"Field '{field}' not found in context", severity=severity)

        if value > 0:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="pass",
                              message=messages.get("pass", f"{field}={value} is positive"),
                              severity=severity, details={"field": field, "value": value})
        return RuleResult(rule_id=rule_id, rule_name=rule_name, status="fail",
                          message=messages.get("fail", f"{field}={value} is not positive"),
                          severity=severity, details={"field": field, "value": value})

    def _eval_not_empty(self, rule_id, rule_name, rule_config, severity, messages, context):
        """Check that a field is not empty/null."""
        field = rule_config["field"]
        value = self._get_nested(context.to_dict(), field)

        if value is not None and str(value).strip():
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="pass",
                              message=messages.get("pass", f"Field '{field}' is defined"),
                              severity=severity, details={"field": field, "value": str(value)})
        return RuleResult(rule_id=rule_id, rule_name=rule_name, status="fail",
                          message=messages.get("fail", f"Field '{field}' is empty or missing"),
                          severity=severity, details={"field": field, "value": value})

    # ------------------------------------------------------------------
    # Cross-field comparison methods
    # ------------------------------------------------------------------

    def _eval_field_lte_field(self, rule_id, rule_name, rule_config, severity, messages, context):
        """Check that field_a <= field_b (both read from context)."""
        field_a = rule_config["field_a"]
        field_b = rule_config["field_b"]
        val_a = self._to_number(self._get_nested(context.to_dict(), field_a))
        val_b = self._to_number(self._get_nested(context.to_dict(), field_b))

        if val_a is None:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="skip",
                              message=f"Field '{field_a}' not found", severity=severity)
        if val_b is None:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="skip",
                              message=f"Field '{field_b}' not found", severity=severity)

        if val_a <= val_b:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="pass",
                              message=messages.get("pass", f"{field_a}={val_a} <= {field_b}={val_b}"),
                              severity=severity, details={"field_a": field_a, "value_a": val_a, "field_b": field_b, "value_b": val_b})
        return RuleResult(rule_id=rule_id, rule_name=rule_name, status="fail",
                          message=messages.get("fail", f"{field_a}={val_a} > {field_b}={val_b}").replace("{value_a}", str(val_a)).replace("{value_b}", str(val_b)),
                          severity=severity, details={"field_a": field_a, "value_a": val_a, "field_b": field_b, "value_b": val_b})

    def _eval_field_gte_field(self, rule_id, rule_name, rule_config, severity, messages, context):
        """Check that field_a >= field_b."""
        field_a = rule_config["field_a"]
        field_b = rule_config["field_b"]
        val_a = self._to_number(self._get_nested(context.to_dict(), field_a))
        val_b = self._to_number(self._get_nested(context.to_dict(), field_b))

        if val_a is None:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="skip",
                              message=f"Field '{field_a}' not found", severity=severity)
        if val_b is None:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="skip",
                              message=f"Field '{field_b}' not found", severity=severity)

        if val_a >= val_b:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="pass",
                              message=messages.get("pass", f"{field_a}={val_a} >= {field_b}={val_b}"),
                              severity=severity, details={"field_a": field_a, "value_a": val_a, "field_b": field_b, "value_b": val_b})
        return RuleResult(rule_id=rule_id, rule_name=rule_name, status="fail",
                          message=messages.get("fail", f"{field_a}={val_a} < {field_b}={val_b}"),
                          severity=severity, details={"field_a": field_a, "value_a": val_a, "field_b": field_b, "value_b": val_b})

    def _eval_connectivity_check(self, rule_id, rule_name, rule_config, severity, messages, context):
        """Check that all members appear in at least one connection."""
        field = rule_config.get("field", "design.connections")
        value = self._get_nested(context.to_dict(), field)

        if value is None or not isinstance(value, list):
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="fail",
                              message=messages.get("fail", "No connections defined"), severity=severity)

        # Collect all member IDs referenced in connections
        connected = set()
        for conn in value:
            if isinstance(conn, dict):
                connected.add(conn.get("a", ""))
                connected.add(conn.get("b", ""))
            elif hasattr(conn, "a") and hasattr(conn, "b"):
                connected.add(conn.a)
                connected.add(conn.b)

        # Check if any connections exist
        if len(connected) >= 2:
            return RuleResult(rule_id=rule_id, rule_name=rule_name, status="pass",
                              message=messages.get("pass", f"Load path has {len(connected)} connected members"),
                              severity=severity, details={"connected_count": len(connected)})
        return RuleResult(rule_id=rule_id, rule_name=rule_name, status="fail",
                          message=messages.get("fail", f"Only {len(connected)} members connected — load path incomplete"),
                          severity=severity, details={"connected_count": len(connected)})
