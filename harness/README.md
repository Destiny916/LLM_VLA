# LLM_VLA Harness

This harness records the rules, memory, skills, and current plan state for
`LLM_VLA`.

## Rule 1

每次关于 `LLM_VLA` 的对话、分析、修改、运行或提交前，必须先读取本
`harness` 文件夹中的核心文件：

- `harness/README.md`
- `harness/rules/rule1_harness_read.md`
- `harness/rules/output_contract.md`
- `harness/rules/llm_prompt_contract.md`
- `harness/skills/franka_arm_actions.yaml`
- `harness/memory/project_memory.md`
- `harness/plan_state.md`

## Scope

- Primary project root: `D:/il/IsaacLab/scripts/LLM_VLA`
- Robot simulation: IsaacLab built-in Franka Panda asset
- Git branch for commits: `codex`
- Remote repository: `https://github.com/Destiny916/LLM_VLA.git`

## Quick Checks

```powershell
python harness\scripts\check_harness.py
python -m unittest discover -s tests -v
```

## RAG Knowledge

扩展版设计新增 `harness/rag` 作为后续 RAG 模块的知识源。当前任务 1 已建立：

- `harness/rag/action_catalog.md`
- `harness/rag/action_examples.md`
- `harness/rag/task_rules.md`
- `harness/rag/state_rules.md`
- `harness/rag/safety_rules.md`
- `harness/rag/conversation_memory.md`
- `harness/rag/two_joint_policy.md`

这些文件记录扩展版动作 token、任务级复位、上举/放下状态语义、idle hold、安全边界和会话记忆。后续实现 RAG 前，仍以现有代码合同为运行事实；RAG 文件是下一阶段扩展设计知识源。

## Change Control

- 不自动提交。
- 每次对话后如有文件修改，必须主动询问用户是否提交。
- 每次提交只能提交到 `codex` 分支。
