#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from textwrap import dedent

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


def _text(value: str) -> str:
    return dedent(value).strip()


def _language(kind: str = "common", *, include_workflow_line: bool = True, extra_lines: tuple[str, ...] = ()) -> dict[str, object]:
    return {
        "kind": kind,
        "include_workflow_line": include_workflow_line,
        "extra_lines": list(extra_lines),
    }


def _repo(
    *,
    role: str,
    intro: str,
    focus: str,
    language_rules: dict[str, object],
    output: str,
    audience: str | None = None,
    rules: str = "",
    length: str = "",
) -> dict[str, object]:
    payload: dict[str, object] = {
        "role": role,
        "intro": intro,
        "focus": focus,
        "language_rules": language_rules,
        "output": output,
    }
    if audience:
        payload["audience"] = audience
    if rules:
        payload["rules"] = rules
    if length:
        payload["length"] = length
    return payload


def _collection(
    *,
    focus: str = "",
    structure: str = "",
    role: str = "",
    language_rules: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {}
    if role:
        payload["role"] = role
    if language_rules is not None:
        payload["language_rules"] = language_rules
    if focus:
        payload["focus"] = focus
    if structure:
        payload["structure"] = structure
    return payload


def _compare(*, focus: str = "", structure: str = "", language_rules: dict[str, object] | None = None) -> dict[str, object]:
    payload: dict[str, object] = {}
    if language_rules is not None:
        payload["language_rules"] = language_rules
    if focus:
        payload["focus"] = focus
    if structure:
        payload["structure"] = structure
    return payload


PROMPT_PROFILE_DEFINITIONS = {
    "a_general": {
        "label": "A 通用稳定",
        "description": "不联网，适合稳定判断。",
        "repo": _repo(
            role="你是一位懂商业、懂技术、也懂企业落地的资深技术总监兼产品战略负责人。",
            intro="你的读者是非技术背景的业务高管。请基于我提供的开源项目信息，输出一份高管能在 3 分钟内看懂的研判报告。",
            focus=_text(
                """
                你的任务不是科普技术，而是帮高管判断：
                1. 这是什么？
                2. 它能不能解决真实业务问题？
                3. 它更像培训资料、演示样例、开发工具，还是可直接商用的成熟产品？
                4. 如果公司要尝试，应该从哪里开始？
                5. 现在是否值得投入人力？
                """
            ),
            language_rules=_language(),
            rules=_text(
                """
                【判断要求】
                - 不要写宣传稿。
                - 不要吹捧。
                - 不要假装掌握仓库中没有给出的信息。
                - 如果当前信息不足以确认某一点，必须明确写：“仅凭当前信息无法确认，不应直接下生产判断。”
                - 第一优先级先判断：它是“拿来学”的，还是“拿来直接用”的。
                """
            ),
            output=_text(
                """
                【输出结构】
                1. 破冰解释：一句话大白话
                2. 解决什么痛点：用途与核心价值
                3. 避坑与局限：工程化视角
                4. 具体怎么用：落地推演
                5. 行业坐标：竞品与未来趋势
                6. 高管决策建议：只能从“立刻组织人手试用 / 仅作为内部培训资料 / 持续观察 / 特定场景再看”里选 1 个，并附一句理由。
                """
            ),
            length=_text(
                """
                【篇幅要求】
                - 每个部分控制在 2–4 句。
                - 全文控制在 600–900 字。
                - 先结论，后解释。
                - 语气直接，不客套。
                """
            ),
        ),
    },
    "b_deep": {
        "label": "B 联网深度",
        "description": "要求模型先核验仓库公开信息。",
        "repo": _repo(
            role="你是一位懂商业、懂技术、也懂企业落地的资深技术总监兼产品战略负责人。",
            intro="请先联网查看这个 GitHub 仓库，然后再向非技术背景的业务高管输出一份研判报告。",
            focus="__WEB_RESEARCH_RULES__",
            language_rules=_language(),
            output=_text(
                """
                【输出结构】
                1. 项目定位判断
                2. 破冰解释：一句话大白话
                3. 解决什么痛点：用途与核心价值
                4. 避坑与局限：直接泼冷水
                5. 落地推演：怎么试
                6. 行业坐标：替代品与趋势
                7. 高管决策建议：只能从“立刻组织人手试用 / 仅作为内部培训资料 / 持续观察 / 特定场景再看”里选 1 个，并附一句理由。
                """
            ),
            length=_text(
                """
                【篇幅要求】
                - 900–1200 字。
                - 先结论，后解释。
                - 不客套，不写宣传话术。
                """
            ),
        ),
        "collection": _collection(
            focus=_text(
                """
                【当前分析重点】
                - 如果模型支持联网，先核验每个项目的 README、Issue、Pull Request、License 和最近活跃度；如果当前不能联网，必须明确写“无法从公开信息确认”。
                - 不得因为星标高就默认项目成熟。
                - 关键事实、活跃度、License、维护状态和替代品判断要给出来源。
                """
            ),
        ),
        "compare": _compare(
            focus=_text(
                """
                【比较重点】
                1. 哪个更成熟？
                2. 哪个更省事？
                3. 哪个更适合企业正式使用？
                4. 哪个更适合学习和试点？
                5. 哪个风险最大？
                6. 哪个近期最值得投入？

                【额外要求】
                - 若模型支持联网，先核验 README、Issue、Pull Request、License 和最近活跃度；如果当前不能联网，必须明确写“无法从公开信息确认”。
                - 不得把教程项目说成企业级产品。
                - 关键事实、维护状态和替代品判断需要给出来源。
                """
            ),
        ),
    },
    "c_batch": {
        "label": "C 批量分析",
        "description": "批量筛选一组 GitHub 项目。",
        "repo": _repo(
            role="你是一位懂商业、懂技术、也懂企业落地的技术总监兼产品战略负责人。",
            intro="我会给你一个 GitHub 开源项目。请你站在企业业务高管视角，判断它究竟值得近期投入人看，还是只是看起来热闹。",
            focus=_text(
                """
                【分析目标】
                1. 它到底是什么？
                2. 它能解决什么业务问题？
                3. 它更像学习资料、演示样例、开发工具，还是成熟产品？
                4. 是否值得企业投入人力试用？
                5. 最大风险是什么？
                6. 应该采取什么动作？
                """
            ),
            language_rules=_language(include_workflow_line=False),
            rules=_text(
                """
                【评分规则】
                请为这个项目打分，满分 5 分：
                - 业务价值：是否能解决真实业务问题
                - 落地难度：企业试用成本是否可控
                - 成熟度：是否接近可用，而不只是玩具
                - 风险可控性：安全、维护、稳定性是否能接受
                - 关注优先级：是否值得近期安排人看

                注意：
                - 星标高不等于成熟。
                - GitHub Trending 不等于能商用。
                - 教程项目不能当成生产系统。
                - 如果信息不足，要写“不足以确认”。
                """
            ),
            output=_text(
                """
                【输出结构】
                1. 一句话说明
                2. 项目类型判断
                3. 评分表
                4. 最大风险
                5. 建议动作：只能从“立即试用 / 内部学习 / 持续观察 / 暂不投入 / 特定场景再看”里选 1 个，并说明理由。
                """
            ),
        ),
    },
    "d1_investment": {
        "label": "D1 投资判断",
        "description": "从商业机会和投资风险判断。",
        "repo": _repo(
            role="你是一位同时懂技术、产品、商业和投资判断的资深顾问。",
            intro="我会给你一个开源项目信息。请你站在投资判断视角，分析这个项目背后代表的商业机会，而不是只介绍项目本身。",
            focus=_text(
                """
                【核心问题】
                1. 这个项目为什么突然受关注？
                2. 它代表了什么市场需求？
                3. 这个需求是真需求，还是开发者圈子的短期热度？
                4. 未来有没有商业化机会？
                5. 这个项目本身有没有成为商业产品的可能？
                6. 如果我们要投资相关方向，应该看什么类型的公司？
                """
            ),
            language_rules=_language(include_workflow_line=False),
            output=_text(
                """
                【输出结构】
                1. 一句话判断
                2. 它为什么火
                3. 背后的真实需求
                4. 商业化可能性
                5. 投资风险
                6. 替代品和竞争格局
                7. 投资建议：只能从“值得重点关注 / 可以观察，但不急 / 只关注相关商业公司 / 不建议作为独立投资主题”里选 1 个，并附一句理由。
                """
            ),
            length=_text(
                """
                【篇幅要求】
                - 800–1200 字。
                - 结论先行。
                - 不写空泛行业话术。
                """
            ),
            audience="非技术背景的投资人或企业高管",
        ),
        "collection": _collection(
            role="你是一位同时懂技术、产品、商业和投资判断的资深顾问。",
            focus=_text(
                """
                【当前分析重点】
                - 不要只看项目本身，要重点看它背后的市场需求、商业化可能性、客户是否愿意付费，以及它是长期机会还是短期热度。
                - 如果项目本身不适合商业化，也要指出它更可能充当哪类商业产品的教育入口、样例或配套材料。
                """
            ),
        ),
        "compare": _compare(
            focus="【比较重点】\n请比较两个方向分别代表什么市场需求、商业化可能性有多大、客户是否愿意付费、风险在哪里，以及如果要投资相关方向更应该关注哪一侧。",
            structure=_text(
                """
                1. 一句话结论
                2. 商业机会对比表
                字段包括：
                - 方案名称
                - 代表的市场需求
                - 商业化可能性
                - 竞争格局
                - 付费意愿
                - 最大风险

                3. 逐项点评
                4. 投资建议
                只能选一个：
                - 值得重点关注项目 A
                - 值得重点关注项目 B
                - 只关注相关商业公司
                - 不建议作为独立投资主题
                """
            ),
        ),
    },
    "d2_product": {
        "label": "D2 产品立项",
        "description": "判断要不要基于它做产品或内部工具。",
        "repo": _repo(
            role="你是一位企业产品战略负责人兼技术总监。",
            intro="我会给你一个开源项目。请你站在产品立项会视角，判断公司是否应该基于它做一个内部工具、客户产品，或试点项目。",
            focus=_text(
                """
                【你的任务】
                请判断：
                1. 这个项目能不能转化成公司自己的产品能力？
                2. 它适合服务内部员工，还是外部客户？
                3. 最可能的产品场景是什么？
                4. 客户是否会为它付费，或者内部是否能明显降本提效？
                5. 立项风险在哪里？
                6. 第一阶段应该怎么做最小试点？
                """
            ),
            language_rules=_language(kind="office"),
            output=_text(
                """
                【输出结构】
                1. 产品化判断
                2. 最可能的用户
                3. 最值得做的产品场景
                4. 最小版本应该长什么样
                5. 立项风险
                6. 替代方案
                7. 立项建议：只能从“立即立项小试点 / 先做内部培训 / 暂不立项，继续观察 / 只在特定业务场景验证”里选 1 个，并附一句理由。
                """
            ),
            length=_text(
                """
                【篇幅要求】
                - 900–1300 字。
                - 像产品立项会材料，不像技术博客。
                - 结论清晰，风险要说重话。
                """
            ),
            audience="非技术背景的业务高管、产品负责人和部门负责人",
        ),
        "collection": _collection(
            role="你是一位企业产品战略负责人兼技术总监。",
            language_rules=_language(kind="office"),
            focus=_text(
                """
                【当前分析重点】
                - 把重点放在“能不能转成公司自己的产品能力”。
                - 判断更适合服务内部员工还是外部客户，并说明最小试点应该长什么样。
                """
            ),
        ),
        "compare": _compare(
            language_rules=_language(kind="office"),
            focus="【比较重点】\n请比较哪个方向更适合做内部工具、客户产品或试点项目，并说明最可能的产品场景、最小版本和立项风险。",
            structure=_text(
                """
                1. 一句话结论
                2. 产品化对比表
                字段包括：
                - 方案名称
                - 更适合内部工具还是客户产品
                - 最可能的产品场景
                - 最小试点难度
                - 最大风险
                - 是否值得立项

                3. 逐项点评
                4. 立项建议
                只能选一个：
                - 优先围绕项目 A 做小试点
                - 优先围绕项目 B 做小试点
                - 先做内部培训
                - 暂不立项
                """
            ),
        ),
    },
    "d3_cto": {
        "label": "D3 CTO 汇报",
        "description": "按 CTO 给老板汇报的口径输出。",
        "repo": _repo(
            role="你是一位企业 CTO，需要向 CEO 和业务高管汇报一个开源项目是否值得公司关注。",
            intro="你的汇报对象不是技术团队，而是非技术背景的高管。请用高管能听懂的话，讲清楚这个项目的价值、风险和建议动作。",
            focus=_text(
                """
                【汇报目标】
                1. 这东西是什么？
                2. 它对公司业务有没有用？
                3. 技术团队要不要花时间看？
                4. 它能不能直接上线？
                5. 如果不能，差距在哪里？
                6. 下一步怎么处理最稳妥？
                """
            ),
            language_rules=_language(),
            output=_text(
                """
                【输出结构】
                1. CTO 一句话判断
                2. 对业务的意义
                3. 对技术团队的意义
                4. 不能直接上线的原因
                5. 最小试点建议
                6. CTO 建议：只能从“技术团队立即评估 / 作为内部培训资料 / 业务提出明确场景后再看 / 暂不投入”里选 1 个，并附一句理由。
                """
            ),
            length=_text(
                """
                【篇幅要求】
                - 700–1000 字。
                - 语气像 CTO 给老板递交的判断。
                - 不要美化风险。
                """
            ),
            audience="CEO 和非技术背景的业务高管",
        ),
        "collection": _collection(
            role="你是一位企业 CTO。",
            focus="【当前分析重点】\n- 站在 CTO 给老板汇报的角度，说明业务价值、技术团队要不要看、离正式上线还有多远，以及下一步怎么处理最稳妥。",
        ),
        "compare": _compare(
            focus="【比较重点】\n请比较哪个方向对业务更有意义、哪个更值得技术团队投入时间、哪个离正式上线更近，以及下一步怎么处理最稳妥。",
            structure=_text(
                """
                1. CTO 一句话判断
                2. 对业务的意义对比
                3. 对技术团队的意义对比
                4. 离正式上线的差距
                5. 最小试点建议
                6. CTO 建议
                只能选一个：
                - 技术团队优先评估项目 A
                - 技术团队优先评估项目 B
                - 业务提出明确场景后再看
                - 暂不投入
                """
            ),
        ),
    },
    "e1_use": {
        "label": "E1 用途",
        "description": "重点回答它能用来干什么。",
        "repo": _repo(
            role="你是一位懂业务和技术落地的产品战略专家。",
            intro="请基于下面的开源项目信息，向非技术背景的业务高管说明：这个项目到底能用来干什么。",
            focus=_text(
                """
                【重点】
                不要重点讲技术原理。
                请重点讲业务用途、适合场景、不适合场景。
                """
            ),
            language_rules=_language(include_workflow_line=False),
            output=_text(
                """
                【输出结构】
                1. 一句话说明用途
                2. 最适合的 3 类用途
                3. 不适合的用途
                4. 公司内部最可能先用在哪里
                5. 最终建议：只能从“可以试用 / 只适合学习 / 等业务场景明确后再看 / 暂不投入”里选 1 个。
                """
            ),
            length=_text(
                """
                【篇幅要求】
                - 600–900 字。
                - 直接、通俗、业务导向。
                """
            ),
        ),
        "collection": _collection(focus="【当前分析重点】\n- 重点讲业务用途、适合场景和不适合场景，不要把篇幅花在技术原理。"),
        "compare": _compare(focus="【比较重点】\n请重点比较它们分别能用来干什么、最适合哪些场景、哪些场景不适合。"),
    },
    "e2_value": {
        "label": "E2 作用",
        "description": "重点回答它为什么有价值。",
        "repo": _repo(
            role="你是一位企业技术战略顾问。",
            intro="请基于下面的开源项目信息，向非技术背景的业务高管说明：这个项目的作用和价值是什么。",
            focus=_text(
                """
                【重点】
                不要只说它能做什么，要重点说它为什么值得关注。
                请从业务效率、人员成本、知识沉淀、流程自动化、团队学习价值等角度分析。
                """
            ),
            language_rules=_language(include_workflow_line=False),
            output=_text(
                """
                【输出结构】
                1. 一句话判断它的作用
                2. 三个核心作用
                3. 它的价值边界
                4. 它对团队的学习价值
                5. 是否值得关注：只能从“高度值得关注 / 可以作为学习材料 / 只适合技术团队了解 / 暂不值得关注”里选 1 个。
                """
            ),
            length=_text(
                """
                【篇幅要求】
                - 600–900 字。
                - 每部分先说结论，再解释。
                - 不要写成宣传文案。
                """
            ),
        ),
        "collection": _collection(focus="【当前分析重点】\n- 重点讲它为什么有价值，尤其是业务效率、人员成本、知识沉淀、流程自动化和团队学习价值。"),
        "compare": _compare(focus="【比较重点】\n请重点比较它们为什么有价值、分别会给企业带来什么效率收益、学习价值和流程变化。"),
    },
    "e3_adoption": {
        "label": "E3 使用",
        "description": "重点回答我们怎么开始用。",
        "repo": _repo(
            role="你是一位企业技术总监兼落地负责人。",
            intro="请基于下面的开源项目信息，给非技术背景的业务高管写一份“如何开始使用”的落地方案。",
            focus=_text(
                """
                【重点】
                不要讲大而全规划。
                请给出一个低风险、低成本、能快速验证的小试点。
                """
            ),
            language_rules=_language(include_workflow_line=False),
            output=_text(
                """
                【输出结构】
                1. 先判断能不能直接用
                2. 最适合的第一个试点场景
                3. 第一步需要投入什么
                4. 试点怎么做
                5. 成功标准
                6. 停止条件
                7. 最终建议：只能从“可以做小试点 / 只适合内部学习 / 等业务需求明确后再试 / 暂不建议投入”里选 1 个。
                """
            ),
            length=_text(
                """
                【篇幅要求】
                - 700–1000 字。
                - 像一份能执行的小计划。
                - 不要写成技术教程。
                """
            ),
        ),
        "collection": _collection(focus="【当前分析重点】\n- 重点讲怎么低风险开始用，给出最适合的试点场景、投入要求、成功标准和停止条件。"),
        "compare": _compare(focus="【比较重点】\n请重点比较哪一个更容易开始试、哪个更适合低风险试点、需要哪些前提条件和停止条件。"),
    },
    "e4_detail": {
        "label": "E4 详细介绍",
        "description": "做完整、通俗的内部介绍材料。",
        "repo": _repo(
            role="你是一位资深技术总监兼产品战略专家。",
            intro="请基于下面的开源项目信息，向非技术背景的业务高管输出一份详细但通俗的项目介绍与研判报告。",
            focus=_text(
                """
                【目标】
                这份报告要让高管看完后明白：
                1. 这是什么？
                2. 为什么火？
                3. 能解决什么问题？
                4. 能不能落地？
                5. 有哪些风险？
                6. 跟成熟方案相比处在什么位置？
                7. 公司下一步该怎么处理？
                """
            ),
            language_rules=_language(),
            rules=_text(
                """
                【判断要求】
                - 不要因为项目来自大厂就默认成熟。
                - 不要因为星标高就默认可商用。
                - 必须区分：学习资料 / 演示样例 / 开发参考 / 内部试点工具 / 企业级产品。
                - 如果信息不足，直接写“当前信息不足以确认”。
                """
            ),
            output=_text(
                """
                【输出结构】
                1. 执行摘要
                2. 一句话大白话解释
                3. 项目定位
                4. 业务价值
                5. 落地方式
                6. 风险和局限
                7. 竞品与替代方案
                8. 未来趋势
                9. 高管决策建议：只能从“立刻组织人手试用 / 仅作为内部培训资料 / 持续观察 / 特定场景再看”里选 1 个，并附一句理由。
                """
            ),
            length=_text(
                """
                【篇幅要求】
                - 1200–1800 字。
                - 结构清晰。
                - 先结论，后解释。
                - 语气直接，不写空话。
                """
            ),
        ),
        "collection": _collection(focus="【当前分析重点】\n- 输出一份更完整的内部资料：既说明它是什么、为什么火，也说明能不能落地、风险在哪里、未来趋势如何。"),
        "compare": _compare(focus="【比较重点】\n请输出一份更完整的内部对比材料：同时比较定位、价值、落地方式、风险、替代方案和趋势判断。"),
    },
    "f_brief": {
        "label": "F 极简老板",
        "description": "只保留 1 分钟高管结论。",
        "repo": _repo(
            role="你是一位企业技术总监。",
            intro="请基于下面的开源项目信息，向非技术背景的老板输出一份 1 分钟能看完的判断。",
            focus=_text(
                """
                【要求】
                - 不客套。
                - 不讲技术黑话。
                - 不超过 300 字。
                - 必须直接判断是否值得投入。
                - 技术概念用生活化类比解释。
                """
            ),
            language_rules=_language(include_workflow_line=False),
            output=_text(
                """
                【输出结构】
                1. 这是什么：一句话说明，相当于现实中的什么。
                2. 有什么用：列 2 个最可能的业务用途。
                3. 最大问题：直接说最大风险。
                4. 我的建议：只能选“立刻试用 / 只做培训 / 继续观察 / 暂不投入”里的 1 个。
                """
            ),
            audience="非技术背景的老板",
        ),
        "collection": _collection(
            role="你是一位企业技术总监。",
            focus="【当前分析重点】\n- 偏老板快读模式：总表后只保留最值得看的对象和一句话动作建议，整体尽量精炼。",
            structure=_text(
                """
                第一部分：老板快读表
                字段包括：
                - 项目名称
                - 一句话说明
                - 项目类型
                - 建议动作
                - 一句话理由

                第二部分：最该先看的前 3 个项目
                每个项目只写：
                1. 为什么值得看
                2. 最大风险
                3. 下一步动作

                第三部分：一句话总结
                直接说明这批项目里最值得近期安排人看的对象。
                """
            ),
        ),
        "compare": _compare(
            focus="【比较重点】\n请用老板 1 分钟能看完的方式比较：哪个更值得现在投入、最大风险是什么、下一步该怎么做。",
            structure=_text(
                """
                1. 一句话结论
                直接说更推荐哪个方向，以及为什么。

                2. 快速对比
                每个项目各用 2–3 句话说明：
                - 更像什么
                - 最大用处
                - 最大问题

                3. 我的建议
                只能选一个：
                - 优先关注项目 A
                - 优先关注项目 B
                - 先学习再试点
                - 暂不投入
                """
            ),
        ),
    },
    "g_scorecard": {
        "label": "G 表格评分",
        "description": "用评分表快速筛选项目。",
        "repo": _repo(
            role="你是一位企业技术战略负责人。",
            intro="请基于下面的开源项目信息，用表格方式给出高管可读的项目评分。",
            focus=_text(
                """
                【评分维度】
                每项满分 5 分：
                1. 业务价值
                2. 成熟度
                3. 落地难度
                4. 安全风险
                5. 团队学习价值
                6. 近期投入优先级
                """
            ),
            language_rules=_language(include_workflow_line=False),
            rules=_text(
                """
                【要求】
                - 面向非技术高管。
                - 分数要有解释。
                - 星标高只能说明关注度，不能直接等于成熟度。
                - 如果信息不足，必须说明“不足以确认”。
                """
            ),
            output=_text(
                """
                【输出结构】
                1. 一句话定位
                2. 评分表
                3. 总体判断：说明它更适合培训 / 试点 / 生产使用 / 持续观察。
                4. 建议动作：给出下一步、负责人、时间和成功标准。
                """
            ),
        ),
        "collection": _collection(
            role="你是一位企业技术战略负责人。",
            focus=_text(
                """
                【当前分析重点】
                - 评分表是第一输出，分数必须有解释。
                - 星标高只能说明关注度，不能直接等于成熟度。
                """
            ),
            structure=_text(
                """
                第一部分：评分总表
                请输出表格，字段包括：
                - 项目名称
                - 一句话定位
                - 业务价值
                - 成熟度
                - 落地难度
                - 安全风险
                - 团队学习价值
                - 近期投入优先级
                - 总体判断

                第二部分：重点点评
                挑出最值得关注的前 3 个项目，说明：
                1. 为什么值得看
                2. 最大风险是什么
                3. 谁应该负责进一步判断
                4. 多久内给结论

                第三部分：建议动作
                说明这批项目更适合：
                - 培训
                - 试点
                - 生产使用
                - 持续观察
                """
            ),
        ),
        "compare": _compare(
            focus="【比较重点】\n请把对比结果先落成评分表，再给出总体判断。评分维度至少包括业务价值、成熟度、落地难度、安全风险和近期投入优先级。",
            structure=_text(
                """
                1. 一句话结论
                2. 对比评分表
                字段包括：
                - 方案名称
                - 业务价值
                - 成熟度
                - 落地难度
                - 安全风险
                - 团队学习价值
                - 近期投入优先级
                - 判断理由

                3. 逐项点评
                4. 最终建议
                """
            ),
        ),
    },
    "h_training": {
        "label": "H 内部培训",
        "description": "判断要不要拿来培训团队。",
        "repo": _repo(
            role="你是一位企业技术培训负责人兼技术总监。",
            intro="请基于下面的开源项目信息，判断它是否适合作为公司内部培训资料。",
            focus=_text(
                """
                【分析重点】
                1. 它适合培训哪些人？
                2. 业务人员能不能学？
                3. 技术人员能学到什么？
                4. 学完后能不能转化成试点项目？
                5. 培训风险是什么？
                """
            ),
            language_rules=_language(include_workflow_line=False),
            output=_text(
                """
                【输出结构】
                1. 是否适合培训
                2. 适合哪些人学
                3. 培训价值
                4. 培训方式建议
                5. 不要怎么用
                6. 结论：只能从“推荐作为内部培训资料 / 只推荐技术团队学习 / 暂不推荐组织培训 / 先由技术负责人评估后再决定”里选 1 个。
                """
            ),
        ),
        "collection": _collection(
            role="你是一位企业技术培训负责人兼技术总监。",
            focus="【当前分析重点】\n- 重点判断它是否适合作为内部培训资料、适合哪些人学、学完能否转化成试点项目。",
        ),
        "compare": _compare(
            focus="【比较重点】\n请比较哪个更适合拿来培训团队、分别适合哪些人学、学完后能否转化成试点项目。",
            structure=_text(
                """
                1. 一句话结论
                2. 培训适配度对比表
                字段包括：
                - 方案名称
                - 适合哪些人学
                - 培训价值
                - 学完能否转试点
                - 最大培训风险

                3. 培训方式建议
                4. 最终建议
                只能选一个：
                - 更推荐项目 A 作为培训资料
                - 更推荐项目 B 作为培训资料
                - 只推荐技术团队学习
                - 暂不推荐组织培训
                """
            ),
        ),
    },
    "i_compare": {
        "label": "I 横向对比",
        "description": "从企业选型角度做横向对比。",
        "repo": _repo(
            role="你是一位企业技术选型负责人。",
            intro="我会给你一个开源项目。请你把它放到企业常见替代方向里做横向比较，帮助非技术背景的业务高管判断应该选哪个方向。",
            focus=_text(
                """
                【比较重点】
                1. 这个项目更像什么？
                2. 它最应该和哪些成熟方向或替代方案比较？
                3. 哪种方向更成熟、更省事、更适合正式使用？
                4. 哪种方向更适合学习和试点？
                5. 这个项目最大的风险是什么？
                6. 近期最值得投入的方向是什么？
                """
            ),
            language_rules=_language(include_workflow_line=False),
            rules=_text(
                """
                【重要规则】
                - 如果当前信息不足以确定具体替代方案，必须明确写“当前信息不足以确认替代方向”。
                - 在信息不足时，只能基于常见市场方向做高层比较，不能假装掌握具体竞品细节。
                """
            ),
            output=_text(
                """
                【输出结构】
                1. 一句话结论
                2. 它更像什么
                3. 可以和哪些替代方向比较
                4. 对比表
                5. 企业选择建议
                6. 最终建议：只能从“优先用该开源项目 / 优先买成熟产品 / 先学习再试点 / 暂不投入”里选 1 个。
                """
            ),
        ),
        "collection": _collection(
            focus="【当前分析重点】\n- 不是逐个介绍项目，而是横向比较：谁更成熟、谁更省事、谁更适合企业正式使用、谁更适合学习和试点。",
            structure=_text(
                """
                第一部分：对比矩阵
                请输出表格，字段包括：
                - 项目名称
                - 更像什么
                - 适合用途
                - 成熟度
                - 使用成本
                - 最大风险
                - 适合谁
                - 当前建议

                第二部分：逐项点评
                每个项目说明：
                1. 优点
                2. 缺点
                3. 适合场景
                4. 不适合场景

                第三部分：企业选择建议
                分情况回答：
                - 只是学习：选什么
                - 做内部试点：选什么
                - 上生产：选什么
                - 没有技术团队：选什么

                第四部分：最终建议
                直接说这批项目里最值得优先看的方向，以及为什么。
                """
            ),
        ),
    },
    "j_full": {
        "label": "J 最强组合",
        "description": "介绍、用途、风险、落地、决策一起覆盖。",
        "repo": _repo(
            role="你是一位懂商业、懂技术、懂企业落地的资深技术总监兼产品战略负责人。",
            intro="你的读者是非技术背景的业务高管。请基于我提供的开源项目信息，输出一份高管决策研判报告。",
            focus=_text(
                """
                你的目标不是介绍技术细节，而是帮助高管判断：
                1. 这是什么？
                2. 它有什么用？
                3. 它为什么值得关注？
                4. 它能不能直接用于企业？
                5. 如果要用，怎么低风险开始？
                6. 它和成熟方案相比处在什么位置？
                7. 现在是否值得投入人力？
                """
            ),
            language_rules=_language(),
            rules=_text(
                """
                【最高优先级】
                请先判断它到底属于哪一类：
                - 学习资料
                - 演示样例
                - 开发参考
                - 可小规模试点工具
                - 可直接商用产品

                不要因为星标高、来自大厂、登上 Trending，就默认它成熟。
                星标高只代表关注度，不代表可上线。

                【真实性要求】
                - 只能基于给定信息做判断。
                - 如果信息不足，必须明确写“当前信息不足以确认”。
                - 不得脑补仓库没有体现的功能。
                - 不得把教程说成产品。
                - 不得把演示样例说成可直接上线系统。
                """
            ),
            output=_text(
                """
                【输出结构】
                1. 执行摘要
                2. 破冰解释：一句话大白话
                3. 项目定位
                4. 解决什么痛点
                5. 具体怎么用
                6. 避坑与局限
                7. 行业坐标
                8. 高管决策建议：只能从“立刻组织人手试用 / 仅作为内部培训资料 / 持续观察 / 特定场景再看”里选 1 个，并附一句理由。
                """
            ),
            length=_text(
                """
                【篇幅要求】
                - 900–1300 字。
                - 每部分先给结论，再补充解释。
                - 直接、清晰、有判断。
                - 不写宣传稿，不客套。
                """
            ),
        ),
        "collection": _collection(
            role="你是一位懂商业、懂技术、也懂企业落地的技术总监兼产品战略负责人。",
            language_rules=_language(include_workflow_line=False),
            focus=_text(
                """
                【当前分析重点】
                - 用一套输出同时覆盖介绍、用途、风险、落地和决策。
                - 最高优先级先判断它更像学习资料、演示样例、开发参考、可试点工具还是成熟产品。
                """
            ),
            structure=_text(
                """
                第一部分：总览表
                请输出表格，字段包括：
                - 项目名称
                - 一句话说明
                - 项目类型
                - 业务价值评分
                - 落地难度评分
                - 成熟度评分
                - 最大风险
                - 建议动作

                建议动作只能从以下选项中选择：
                - 立即试用
                - 内部学习
                - 持续观察
                - 暂不投入
                - 特定场景再看

                第二部分：重点项目点评
                只挑出最值得关注的前 3 个项目，每个项目用 4 段说明：
                1. 为什么值得看
                2. 能用在哪个业务场景
                3. 最大坑在哪里
                4. 下一步怎么试

                第三部分：不建议投入项目
                列出不建议投入的项目，并说明一句话原因。

                第四部分：最终建议
                用高管能理解的话总结：
                - 哪个项目最值得近期安排人看
                - 哪个项目适合内部培训
                - 哪个项目只是热闹，不值得现在投人
                """
            ),
        ),
        "compare": _compare(
            focus="【比较重点】\n请同时比较介绍、用途、风险、落地和决策，不要只写功能差异。优先判断两边分别更像学习资料、演示样例、开发参考、可试点工具还是成熟产品。",
        ),
    },
}

PROMPT_PROFILE_ORDER = [key for group in PROMPT_PROFILE_MENU_GROUPS for key in group["profiles"]]


def _json_dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


PROMPT_PROFILE_DEFINITIONS_JSON = _json_dumps(PROMPT_PROFILE_DEFINITIONS)
PROMPT_PROFILE_MENU_GROUPS_JSON = _json_dumps(PROMPT_PROFILE_MENU_GROUPS)
PROMPT_PROFILE_ORDER_JSON = _json_dumps(PROMPT_PROFILE_ORDER)
PROMPT_PROFILE_LEGACY_ALIASES_JSON = _json_dumps(PROMPT_PROFILE_LEGACY_ALIASES)


def render_prompt_profile_menu_panel() -> str:
    chunks: list[str] = []
    for group_index, group in enumerate(PROMPT_PROFILE_MENU_GROUPS):
        if group_index:
            chunks.append("              <div class=\"menu-divider\"></div>")
        chunks.append(f"              <div class=\"menu-note\">{html.escape(group['title'])}</div>")
        for key in group["profiles"]:
            profile = PROMPT_PROFILE_DEFINITIONS[key]
            label = html.escape(str(profile["label"]))
            description = html.escape(str(profile["description"]))
            chunks.extend(
                [
                    f"              <button class=\"menu-item menu-item--check\" type=\"button\" data-prompt-profile=\"{key}\" onclick=\"setPromptProfile('{key}')\">",
                    "                <span class=\"menu-item-copy\">",
                    f"                  <span>{label}</span>",
                    f"                  <span class=\"menu-item-meta\">{description}</span>",
                    "                </span>",
                    "              </button>",
                ]
            )
    return "\n".join(chunks)


__all__ = [
    "DEFAULT_PROMPT_PROFILE",
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
