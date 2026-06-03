# LLM_VLA Harness

This harness records the rules, memory, skills, and current plan state for
`LLM_VLA`.

## Rule 1

每次关于 `LLM_VLA` 的对话、分析、修改、运行或提交前，必须先读取本
`harness` 文件夹中的核心文件：

- `harness/README.md`
- `harness/rules/rule1_harness_read.md`
- `harness/rules/output_contract.md`
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

## Change Control

- 不自动提交。
- 每次对话后如有文件修改，必须主动询问用户是否提交。
- 每次提交只能提交到 `codex` 分支。
