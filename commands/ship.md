---
name: ship
description: Full end-to-end feature shipping workflow
disable-model-invocation: true
---

Ship feature: $ARGUMENTS

Execute the full-stack-ship workflow:
1. **Plan**: Analyze the request and create implementation plan
2. **Implement**: Write code following project patterns
3. **Test**: Add tests and run the test suite
4. **Review**: Self-review against quality checklist
5. **Prepare**: Create clean commits and PR description

Use the full-stack-ship skill orchestration pattern.
Report progress at each phase.
