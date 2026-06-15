"""
顶妈（dingma）Prompt 调试日志

将最终送入 LLM 的完整提示词写入文件，便于复制联调与优化。
文件内只保留一份完整 payload，分层区块不重复打印合并结果。
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

# 完整 Prompt 落盘目录（相对 backend/）
_PROMPT_DUMP_DIR = Path(__file__).resolve().parent.parent.parent / "logs" / "dingma_prompts"


def _section(title: str, content: Optional[str], border: str = "=" * 72) -> str:
    """格式化一个 prompt 区块"""
    text = (content or "").strip()
    if not text:
        return f"{border}\n[{title}] （空）\n{border}"
    return (
        f"{border}\n[{title}] ({len(text)} chars)\n"
        f"{border}\n{text}\n{border}"
    )


def _format_messages_once(messages: List[Dict[str, Any]]) -> str:
    """格式化完整 messages（仅输出一次，作为最终 payload）"""
    lines = [f"【实际送入 LLM 的 messages】共 {len(messages)} 条", "=" * 72]
    for idx, msg in enumerate(messages):
        role = msg.get("role", "?")
        content = str(msg.get("content") or "")
        lines.append(f"--- message[{idx}] role={role} len={len(content)} ---")
        lines.append(content)
        lines.append("")
    return "\n".join(lines)


def _build_full_dump(
    tag: str,
    *,
    messages: List[Dict[str, Any]],
    user_input: Optional[str] = None,
    agent_id: Optional[int] = None,
    agent_name: Optional[str] = None,
    ip_persona_prompt: Optional[str] = None,
    skills_prompt: Optional[str] = None,
    knowledge_block: Optional[str] = None,
    extra_user_prompt: Optional[str] = None,
    routing_info: Optional[Dict[str, Any]] = None,
    skills_detail: Optional[List[Dict[str, Any]]] = None,
    inject_meta: Optional[Dict[str, Any]] = None,
) -> str:
    """组装完整调试报告：分层明细 + 一份最终 messages，无重复内容"""
    meta_lines = [
        "顶妈 Prompt 调试报告",
        f"标签: {tag}",
        f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    if agent_id is not None:
        meta_lines.append(f"智能体 ID: {agent_id}")
    if agent_name:
        meta_lines.append(f"智能体名称: {agent_name}")
    if user_input:
        meta_lines.append(f"本轮用户输入 ({len(user_input)} chars): {user_input}")

    parts = ["\n".join(meta_lines), ""]

    # 注入诊断（便于排查 IP 人设为何为空）
    if inject_meta:
        parts.append(_section(f"{tag} 注入诊断", json.dumps(inject_meta, ensure_ascii=False, indent=2)))
        parts.append("")

    if routing_info:
        parts.append(_section(f"{tag} 路由信息", json.dumps(routing_info, ensure_ascii=False, indent=2)))
        parts.append("")

    if skills_detail:
        parts.append(_section(f"{tag} 命中技能", json.dumps(skills_detail, ensure_ascii=False, indent=2)))
        parts.append("")

    # 组装分层（各层只出现一次，不重复 FINAL / message[0]）
    parts.append(_section(f"{tag} LAYER 1 · IP 人设", ip_persona_prompt))
    parts.append("")
    parts.append(_section(f"{tag} LAYER 2 · 智能体/技能", skills_prompt))
    parts.append("")
    parts.append(_section(f"{tag} LAYER 3 · 成分护栏", knowledge_block))
    parts.append("")

    if extra_user_prompt:
        parts.append(_section(f"{tag} USER PROMPT (task)", extra_user_prompt))
        parts.append("")

    # 最终 payload 只在此处完整输出一次
    parts.append(_format_messages_once(messages))

    return "\n".join(parts)


def _dump_to_file(tag: str, content: str, agent_id: Optional[int]) -> Path:
    """将完整 prompt 写入文件"""
    _PROMPT_DUMP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    agent_part = f"_agent{agent_id}" if agent_id is not None else ""
    filename = f"{tag.lower()}_{ts}{agent_part}.txt"
    filepath = _PROMPT_DUMP_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    return filepath


def log_dingma_prompt(
    tag: str,
    *,
    system_prompt: str,
    user_input: Optional[str] = None,
    agent_id: Optional[int] = None,
    agent_name: Optional[str] = None,
    knowledge_block: Optional[str] = None,
    messages: Optional[List[Dict[str, Any]]] = None,
    extra_user_prompt: Optional[str] = None,
    ip_persona_prompt: Optional[str] = None,
    agent_core_prompt: Optional[str] = None,
    routing_info: Optional[Dict[str, Any]] = None,
    skills_detail: Optional[List[Dict[str, Any]]] = None,
    inject_meta: Optional[Dict[str, Any]] = None,
) -> None:
    """
    写入完整 Prompt 调试文件，终端仅输出摘要（避免重复刷屏）。

    Args:
        system_prompt: 最终 system prompt（用于终端摘要字符数）
        agent_core_prompt: 技能/智能体层（不含 IP 人设与成分护栏）
        inject_meta: 注入诊断信息（project_id、人设是否命中等）
        其余参数见 _build_full_dump
    """
    if not messages:
        messages = [{"role": "system", "content": system_prompt}]
        if user_input:
            messages.append({"role": "user", "content": user_input})

    meta_parts = [f"[{tag}] Prompt 调试"]
    if agent_id is not None:
        meta_parts.append(f"agent_id={agent_id}")
    if agent_name:
        meta_parts.append(f"agent={agent_name}")
    logger.info(" | ".join(meta_parts))

    full_dump = _build_full_dump(
        tag,
        messages=messages,
        user_input=user_input,
        agent_id=agent_id,
        agent_name=agent_name,
        ip_persona_prompt=ip_persona_prompt,
        skills_prompt=agent_core_prompt,
        knowledge_block=knowledge_block,
        extra_user_prompt=extra_user_prompt,
        routing_info=routing_info,
        skills_detail=skills_detail,
        inject_meta=inject_meta,
    )
    dump_path = _dump_to_file(tag, full_dump, agent_id)

    # 终端只打摘要，完整内容看文件
    persona_len = len((ip_persona_prompt or "").strip())
    skills_len = len((agent_core_prompt or "").strip())
    kb_len = len((knowledge_block or "").strip())
    sys_len = len(system_prompt or "")
    logger.info(
        f"[{tag}] ✅ 完整 Prompt 已写入: {dump_path} | "
        f"IP人设={persona_len} + 技能={skills_len} + 护栏={kb_len} → system={sys_len} chars, "
        f"messages={len(messages)}条"
    )
    if inject_meta:
        logger.info(f"[{tag}] 注入诊断: {json.dumps(inject_meta, ensure_ascii=False)}")
    if skills_detail:
        skill_names = [s.get("name") or s.get("skill_name") or s.get("id") for s in skills_detail]
        logger.info(f"[{tag}] 命中技能: {skill_names}")
