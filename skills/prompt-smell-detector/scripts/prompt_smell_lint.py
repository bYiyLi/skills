#!/usr/bin/env python3
"""Deterministic pre-checks for prompt and Skill bad smells.

This script is intentionally heuristic. It checks structural signals that are easy
for code to verify, then leaves semantic judgment to ChatGPT.

Language policy: English and Chinese are first-class for signal detection.
The semantic review performed by ChatGPT remains authoritative; this script is a
pre-check, not the final judge.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

GENERIC_DESC = [
    "helps with tasks", "help users", "be helpful", "best answer", "various tasks",
    "any task", "writing", "analysis", "帮助用户", "完成各种任务", "尽可能帮助",
    "强大的.*助手", "最佳答案", "写作", "分析", "各种需求", "通用助手",
]

REQUIRED_SEMANTIC_SECTIONS = {
    "workflow": [
        "workflow", "process", "steps", "procedure", "decision tree",
        "工作流", "流程", "步骤", "操作步骤", "执行步骤", "处理流程", "决策树", "分支",
    ],
    "output_contract": [
        "output contract", "return", "output must", "required output", "schema", "format",
        "输出契约", "输出格式", "必须输出", "返回", "结果格式", "字段", "结构", "模板",
    ],
    "failure_handling": [
        "failure", "fallback", "missing input", "if .* missing", "validation fails", "tool fails", "not available",
        "失败", "兜底", "降级", "缺少.*输入", "信息不足", "验证失败", "工具失败", "不可用", "无法获取", "假设",
    ],
    "safety_boundary": [
        "safety", "permission", "confirmation", "do not", "never", "refuse", "destructive", "external",
        "安全", "权限", "确认", "不要", "不得", "禁止", "拒绝", "破坏性", "外部", "发送", "发布", "部署", "删除",
    ],
    "tests_validation": [
        "test", "validation", "red-team", "self-check", "verify", "release gate",
        "测试", "验证", "红队", "自检", "校验", "回归", "发布门", "验收门",
    ],
    "non_goals": [
        "do not use", "do not", "non-goal", "out of scope", "not use",
        "不使用", "不要使用", "不适用", "不做", "不应该", "非目标", "范围外", "除非",
    ],
}

ONE_VOTE_GATES = [
    "trigger_clarity", "workflow", "output_contract", "failure_handling",
    "safety_boundary", "validation_honesty",
]


def read_target(path: Path) -> Tuple[str, str]:
    if path.is_dir():
        skill_md = path / "SKILL.md"
        if skill_md.exists():
            return str(skill_md), skill_md.read_text(encoding="utf-8", errors="replace")
        texts = []
        for p in sorted(path.rglob("*.md")):
            texts.append(f"\n\n<!-- file: {p.relative_to(path)} -->\n" + p.read_text(encoding="utf-8", errors="replace"))
        return str(path), "".join(texts)
    return str(path), path.read_text(encoding="utf-8", errors="replace")


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], List[str]]:
    issues: List[str] = []
    data: Dict[str, str] = {}
    if not text.startswith("---\n"):
        issues.append("missing_yaml_frontmatter")
        return data, issues
    end = text.find("\n---", 4)
    if end == -1:
        issues.append("unterminated_yaml_frontmatter")
        return data, issues
    raw = text[4:end].strip().splitlines()
    for line in raw:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"\'')
    if "name" not in data:
        issues.append("missing_name")
    if "description" not in data:
        issues.append("missing_description")
    return data, issues


def contains_any(text_l: str, patterns: List[str]) -> bool:
    for pattern in patterns:
        if re.search(pattern, text_l):
            return True
    return False


def has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def analyze(text: str, source: str) -> Dict[str, object]:
    text_l = text.lower()
    frontmatter, fm_issues = parse_frontmatter(text)
    findings: List[Dict[str, str]] = []
    gates: Dict[str, Dict[str, str]] = {}
    language = "mixed/zh" if has_cjk(text) else "en/unknown"

    def add(severity: str, smell: str, evidence: str, fix: str) -> None:
        findings.append({"severity": severity, "smell": smell, "evidence": evidence, "fix": fix})

    is_skill = "SKILL.md" in source
    if fm_issues and is_skill:
        for issue in fm_issues:
            add("blocker", issue, "SKILL.md frontmatter is absent or incomplete", "Add YAML frontmatter with lowercase name and detailed description.")

    desc = frontmatter.get("description", "")
    desc_l = desc.lower()
    if is_skill:
        if not desc:
            gates["trigger_clarity"] = {"pass": "fail", "evidence": "description is missing"}
        elif len(desc.split()) < 18 and len(desc) < 90:
            gates["trigger_clarity"] = {"pass": "fail", "evidence": "description is very short"}
            add("blocker", "unclear trigger", desc, "Expand description with trigger cases, non-trigger cases, inputs, and outputs.")
        elif any(re.search(x, desc_l) for x in GENERIC_DESC) and not contains_any(desc_l, ["use when", "when the user", "用于", "当用户", "使用于", "触发"]):
            gates["trigger_clarity"] = {"pass": "fail", "evidence": desc}
            add("blocker", "generic description", desc, "Replace broad helper language with exact trigger and non-trigger conditions.")
        else:
            gates["trigger_clarity"] = {"pass": "pass", "evidence": desc[:180]}
        if not contains_any(desc_l, ["do not use", "unless", "不要使用", "不适用", "除非", "不用于"]):
            add("major", "missing non-trigger condition in description", desc, "Add do-not-use or handoff conditions to description.")

    for key, patterns in REQUIRED_SEMANTIC_SECTIONS.items():
        present = contains_any(text_l, patterns)
        severity = "blocker" if key in {"workflow", "output_contract", "failure_handling", "safety_boundary"} else "major"
        if key in {"workflow", "output_contract", "failure_handling", "safety_boundary"}:
            gates[key] = {"pass": "pass" if present else "fail", "evidence": "matched bilingual signal" if present else "no matching English or Chinese signal"}
        if not present:
            add(severity, f"missing {key.replace('_', ' ')}", "required bilingual signal not found", f"Add an explicit {key.replace('_', ' ')} section or rule.")

    vague_terms = [
        "professional", "accurate", "comprehensive", "detailed", "high quality", "best", "helpful",
        "专业", "准确", "全面", "详细", "高质量", "最佳", "有帮助", "友好", "认真", "深度",
    ]
    vague_hits = [t for t in vague_terms if t in text_l]
    if len(vague_hits) >= 3 and not contains_any(text_l, ["evidence", "validation", "rubric", "output contract", "workflow", "证据", "验证", "评分", "输出契约", "工作流", "流程"]):
        add("major", "principle pile", ", ".join(vague_hits), "Convert vague principles into observable actions and checks.")

    if re.search(r"todo|\[todo|placeholder|replace with actual|待补充|占位|稍后补充|这里填写", text_l):
        add("major", "unresolved template residue", "TODO/placeholder wording detected", "Remove template residue before packaging or approval.")

    source_path = Path(source)
    if source_path.name == "SKILL.md":
        skill_root = source_path.parent
        refs = sorted(set(re.findall(r"references/[A-Za-z0-9_.-]+\.md", text)))
        missing_refs = [ref for ref in refs if not (skill_root / ref).exists()]
        if missing_refs:
            add("major", "broken reference links", ", ".join(missing_refs), "Create missing reference files or remove stale links.")
        if not (skill_root / "agents" / "openai.yaml").exists():
            add("major", "missing agent metadata", "agents/openai.yaml not found", "Add agents/openai.yaml with display name and short description.")

    validation_claim = re.search(r"tests? passed|validation passed|verified successfully|测试通过|验证通过|已验证|已完成验证|校验通过", text_l)
    named_check = re.search(r"\bscript\b|\bmanual\b|\blint\b|red-team|not performed|\bperformed\b|脚本|手动|人工|红队|未执行|已执行|运行|检查项|测试项", text_l)
    if validation_claim and not named_check:
        gates["validation_honesty"] = {"pass": "fail", "evidence": "claims validation without named checks"}
        add("blocker", "fake validation risk", "validation claim lacks named checks", "Name the checks actually performed and list checks not performed.")
    else:
        gates.setdefault("validation_honesty", {"pass": "pass", "evidence": "no unsupported validation claim detected"})

    blockers = sum(1 for f in findings if f["severity"] == "blocker")
    majors = sum(1 for f in findings if f["severity"] == "major")
    minors = sum(1 for f in findings if f["severity"] == "minor")
    score = 100 - blockers * 25 - majors * 8 - minors * 2
    score = max(0, min(100, score))
    if blockers >= 2:
        score = min(score, 49)
    elif blockers == 1:
        score = min(score, 69)
    verdict = "approve" if score >= 90 and blockers == 0 else "needs revision" if score >= 70 and blockers == 0 else "reject"

    return {
        "source": source,
        "language_detected": language,
        "score": score,
        "verdict": verdict,
        "gates": gates,
        "findings": findings,
        "summary": {"blockers": blockers, "major": majors, "minor": minors},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Heuristic prompt/skill smell lint")
    parser.add_argument("path", help="Path to prompt file, SKILL.md, or skill folder")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(json.dumps({"error": f"path not found: {path}"}, indent=2), file=sys.stderr)
        return 2

    source, text = read_target(path)
    result = analyze(text, source)
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"# Prompt Smell Lint\n\nVerdict: {result['verdict']}\n\nScore: {result['score']} / 100\n\nLanguage: {result['language_detected']}\n")
        print("## Findings")
        for f in result["findings"]:
            print(f"- **{f['severity']}** {f['smell']}: {f['evidence']} -> {f['fix']}")
    return 0 if result["verdict"] == "approve" else 1


if __name__ == "__main__":
    raise SystemExit(main())
