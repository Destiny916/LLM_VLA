# Output Contract

The execution output sent to Isaac Sim is a space-separated sequence of action
names. Task-plan JSON is introduced in task 4, but only expanded
`action_tokens` may be passed to Isaac Sim.

Allowed tokens:

- `left_2rad`
- `right_2rad`
- `lift_up`
- `put_down`
- `reset`
- `hold_reset`
- `stop`

Removed tokens:

- `left_circle`
- `right_circle`

Rules:

- `left_2rad` means Franka `panda_joint1 = -2.0 rad`.
- `right_2rad` means Franka `panda_joint1 = +2.0 rad`.
- Only `panda_joint1` and `panda_joint2` are unlocked for this simplified arm demo.
- Other Franka joints are locked by keeping IsaacLab default joint targets.
- `lift_up` changes the persistent pose state to arm lifted by moving `panda_joint2` only.
- `put_down` changes the persistent pose state from lifted to down by moving `panda_joint2` only; it is not `reset`.
- `reset` means `panda_joint1 = 0.0` and `panda_joint2 = 0.0`; locked joints keep default targets.
- `hold_reset` means keep the two unlocked joints at reset targets when there is no task or after all tasks are complete.
- `stop` stops the current task queue and must be a standalone token.
- Default motion actions run for 30 simulation steps.
- Default `reset` and `hold_reset` actions run for 60 simulation steps.
- Actions are not forced to reset after every motion.
- Each task sequence must end with `reset` or `reset hold_reset`.
- `lift_up` must be followed by `put_down` before `reset`.
- `put_down` may only appear after `lift_up` in the same task context.
- The execution token sequence must not contain digits, JSON, punctuation, Chinese explanation, or extra text.
- CLI must display API raw output, visible reasoning summary, API token result, local validation result, and simulation result.
