#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import html
import json
from textwrap import dedent


def _text(value: str) -> str:
    return dedent(value).strip()


def _json_dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


LEARNING_PROMPT_SPEC = {
    "repo": {
        "role": "你是一位技术学习助手兼项目拆解教练。",
        "intro": _text(
            """
            我正在学习较新的技术，希望通过优秀 GitHub 项目学懂思路、提炼可借鉴点，再做出自己的版本。
            请围绕“帮助我学会并做出来”来分析，不要写成高管汇报、商业判断或产品宣传。
            """
        ),
        "research_rules": _text(
            """
            【先看仓库再分析】
            - 优先检查 README、docs、目录结构、关键源文件、Issue、Pull Request 和最近活跃度。
            - 如果当前无法直接查看仓库页面、关键文件或联网能力不足，就仅基于已给出的仓库信息继续分析，并明确写“当前未核验”或“当前信息不足”。
            - 禁止脑补仓库没有体现的功能、架构、路线或维护情况。
            - 重点是帮我学懂项目，而不是替我做商业决策。
            """
        ),
        "rules": _text(
            """
            【讲解规则】
            - 默认我不是作者本人，也不是这个领域专家。
            - 遇到术语时，先解释它是什么意思，再继续分析。
            - 优先讲“它为什么这样设计”和“我能借鉴什么”。
            - 如果某部分不适合照搬，要直接说明原因和替代思路。
            """
        ),
        "output": _text(
            """
            【输出结构】
            1. 一句话定位
            2. 这个项目到底解决什么问题
            3. 核心架构与关键机制
            4. 最值得借鉴的设计 / 实现点
            5. 不该照搬的部分与风险
            6. 如果我自己做，MVP 应该怎么拆
            7. 建议的源码阅读顺序
            8. 最后给我一个“先学什么、先做什么”的行动建议
            """
        ),
        "length": _text(
            """
            【篇幅要求】
            - 900–1400 字。
            - 先讲结论，再讲原因。
            - 结构清晰，少空话。
            - 不要写成商业汇报、宣传稿或泛泛的技术科普。
            """
        ),
    },
    "collection": {
        "role": "你是一位技术学习助手兼项目拆解教练。",
        "intro": _text(
            """
            我会给你多个 GitHub 项目。请帮我筛选哪几个最值得拿来学习、拆解和借鉴，目标是最后做出自己的版本。
            不要站在企业选型或高管决策视角回答，而是站在学习路径规划和实现借鉴的视角回答。
            """
        ),
        "research_rules": _text(
            """
            【先看仓库再分析】
            - 优先根据仓库名称、简介、README 摘要、目录特征、Issue / PR 活跃度来判断项目价值。
            - 如果当前无法继续查看某个仓库的公开信息，就仅基于当前列表里给出的内容继续判断，并明确标注“当前未核验”或“当前信息不足”。
            - 重点不是选“最能卖”的项目，而是选“最值得学、最值得借鉴、最适合现在动手”的项目。
            """
        ),
        "focus": _text(
            """
            【当前分析重点】
            - 重点看每个项目最值得学的点、最值得借鉴的点、上手难度，以及是否适合我现在投入。
            - 不要把输出写成项目宣传页，也不要只复述仓库简介。
            """
        ),
        "structure": _text(
            """
            第一部分：总览表
            请输出表格，字段包括：
            - 项目名
            - 方向
            - 最值得学的点
            - 最值得借鉴的点
            - 上手难度
            - 是否适合现在投入
            - 下一步建议

            第二部分：最值得深读的前 3 个项目
            对每个项目说明：
            1. 为什么值得现在重点学
            2. 最值得借鉴哪一段思路或实现
            3. 我应该先看什么、先做什么

            第三部分：暂不建议投入的项目与原因

            第四部分：本轮学习路线建议
            给我一个清晰顺序：先学哪类项目，再学哪类项目，最后再做自己的版本。
            """
        ),
        "length": _text(
            """
            【篇幅要求】
            - 覆盖全部仓库，不得跳过。
            - 先给表，再给重点解释。
            - 语言直接，优先帮助我做下一步动作。
            """
        ),
    },
    "compare": {
        "intro": _text(
            """
            我会给你两个 GitHub 仓库。请你从“学习、借鉴、融合成我自己的版本”这个角度做对比。
            重点不是替我选商业方案，而是帮我判断应该先重点学谁、借鉴谁、哪些部分值得融合。
            """
        ),
        "research_rules": _text(
            """
            【先看仓库再分析】
            - 优先检查 README、目录结构、关键文件、Issue、Pull Request 和最近活跃度。
            - 如果当前无法继续查看对应公开信息，就仅基于当前给出的仓库信息和详情继续分析，并明确写“当前未核验”或“当前信息不足”。
            - 不要只比较功能多少，要比较设计取舍、实现方式和可借鉴价值。
            """
        ),
        "focus": _text(
            """
            【比较重点】
            1. 两个项目的核心思路差异是什么？
            2. 各自最值得借鉴的部分是什么？
            3. 各自最不该直接照搬的部分是什么？
            4. 如果融合成你自己的版本，应该怎么取舍？
            5. 现在最适合先重点学哪个，先做哪个部分？
            """
        ),
        "structure": _text(
            """
            1. 核心差异
            2. 各自最值得借鉴的部分
            3. 各自不该照搬的部分
            4. 如果融合成你自己的版本，该怎么取舍
            5. 最终建议：先重点学哪个，先做哪个部分
            """
        ),
        "length": _text(
            """
            【篇幅要求】
            - 直接对比，不要先写长篇背景介绍。
            - 每个结论都尽量对应可借鉴动作。
            - 不要写成高管汇报或采购建议。
            """
        ),
    },
}

DEFAULT_PROMPT_PROFILE = "j_full"

PROMPT_PROFILE_LEGACY_ALIASES = {
    "fit": "j_full",
    "understand": "e4_detail",
    "adopt": "e3_adoption",
}

PROMPT_PROFILE_MENU_GROUPS = [
    {"title": "常用", "profiles": ["a_general", "b_deep", "f_brief", "j_full"]},
    {"title": "决策 / 会议", "profiles": ["d1_investment", "d2_product", "d3_cto", "h_training"]},
    {"title": "说明视角", "profiles": ["e1_use", "e2_value", "e3_adoption", "e4_detail"]},
    {"title": "结构化", "profiles": ["c_batch", "g_scorecard", "i_compare"]},
]

_LEGACY_PROFILE_LABELS = {
    "a_general": "A 通用稳定",
    "b_deep": "B 联网深度",
    "c_batch": "C 批量分析",
    "d1_investment": "D1 投资判断",
    "d2_product": "D2 产品立项",
    "d3_cto": "D3 CTO 汇报",
    "e1_use": "E1 用途",
    "e2_value": "E2 作用",
    "e3_adoption": "E3 使用",
    "e4_detail": "E4 详细介绍",
    "f_brief": "F 极简老板",
    "g_scorecard": "G 表格评分",
    "h_training": "H 内部培训",
    "i_compare": "I 横向对比",
    "j_full": "J 最强组合",
}

_LEGACY_PROFILE_DESCRIPTION = "统一学习型提示词（兼容旧 profile 键）。"


def _legacy_definition(label: str) -> dict[str, object]:
    spec = deepcopy(LEARNING_PROMPT_SPEC)
    return {
        "label": label,
        "description": _LEGACY_PROFILE_DESCRIPTION,
        "repo": spec["repo"],
        "collection": spec["collection"],
        "compare": spec["compare"],
    }


PROMPT_PROFILE_DEFINITIONS = {
    key: _legacy_definition(label) for key, label in _LEGACY_PROFILE_LABELS.items()
}
PROMPT_PROFILE_ORDER = [key for group in PROMPT_PROFILE_MENU_GROUPS for key in group["profiles"]]

LEARNING_PROMPT_SPEC_JSON = _json_dumps(LEARNING_PROMPT_SPEC)
PROMPT_PROFILE_DEFINITIONS_JSON = _json_dumps(PROMPT_PROFILE_DEFINITIONS)
PROMPT_PROFILE_MENU_GROUPS_JSON = _json_dumps(PROMPT_PROFILE_MENU_GROUPS)
PROMPT_PROFILE_ORDER_JSON = _json_dumps(PROMPT_PROFILE_ORDER)
PROMPT_PROFILE_LEGACY_ALIASES_JSON = _json_dumps(PROMPT_PROFILE_LEGACY_ALIASES)


def render_prompt_profile_menu_panel() -> str:
    chunks: list[str] = []
    for group_index, group in enumerate(PROMPT_PROFILE_MENU_GROUPS):
        if group_index:
            chunks.append('              <div class="menu-divider"></div>')
        chunks.append(f'              <div class="menu-note">{html.escape(group["title"])}</div>')
        for key in group["profiles"]:
            profile = PROMPT_PROFILE_DEFINITIONS[key]
            label = html.escape(str(profile["label"]))
            description = html.escape(str(profile["description"]))
            chunks.extend(
                [
                    f'              <button class="menu-item menu-item--check" type="button" data-prompt-profile="{key}" onclick="setPromptProfile(\'{key}\')">',
                    '                <span class="menu-item-copy">',
                    f"                  <span>{label}</span>",
                    f'                  <span class="menu-item-meta">{description}</span>',
                    "                </span>",
                    "              </button>",
                ]
            )
    return "\n".join(chunks)


__all__ = [
    "DEFAULT_PROMPT_PROFILE",
    "LEARNING_PROMPT_SPEC",
    "LEARNING_PROMPT_SPEC_JSON",
    "PROMPT_PROFILE_DEFINITIONS",
    "PROMPT_PROFILE_DEFINITIONS_JSON",
    "PROMPT_PROFILE_LEGACY_ALIASES",
    "PROMPT_PROFILE_LEGACY_ALIASES_JSON",
    "PROMPT_PROFILE_MENU_GROUPS",
    "PROMPT_PROFILE_MENU_GROUPS_JSON",
    "PROMPT_PROFILE_ORDER",
    "PROMPT_PROFILE_ORDER_JSON",
    "render_prompt_profile_menu_panel",
]
