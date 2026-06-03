# Rule 1: Harness Read Required

每次关于 `LLM_VLA` 的对话、分析、修改、测试、运行或 Git 提交前，必须先读取
`harness` 文件夹中的核心文件。

必须先读取：

- `harness/README.md`
- `harness/rules/rule1_harness_read.md`
- `harness/rules/output_contract.md`
- `harness/skills/franka_arm_actions.yaml`
- `harness/memory/project_memory.md`
- `harness/plan_state.md`

原因：LLM 规划器、仿真动作、Git 规则和当前 plan 步骤都以 harness 为准。
