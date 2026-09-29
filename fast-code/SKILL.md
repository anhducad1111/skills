---
name: fast-code
description: Use when adding small features, fixing bugs in single files, or making quick edits—tasks under 30 minutes with clear scope
---

# Fast Code

## Overview

Skip the overhead. Write code directly, deploy immediately. No reviews, no compiles, no docs—just working code.

For simple tasks with clear scope and low risk.

## When to Use

**Use when ALL apply:**
- ✅ Single file or related 2-3 files
- ✅ Clear scope (user described exactly what to do)
- ✅ Estimated time < 30 minutes
- ✅ Low risk (not critical path, not security, not API-breaking)
- ✅ No architectural decisions needed
- ✅ No tests required
- ✅ No compilation step

**Don't use when:**
- ❌ Multi-file refactoring
- ❌ Unclear requirements ("make it better")
- ❌ Security or compliance changes
- ❌ Public APIs or breaking changes
- ❌ Complex logic requiring explanation
- ❌ Changes affecting other systems
- ❌ "This might take a while"

## Core Pattern

```
User: "Add X to file Y"
      ↓
You:  Read file Y (understand context)
      ↓
You:  Edit/Write directly (minimal changes only)
      ↓
You:  Done ✓ (no review, no docs, no compile)
```

## Quick Reference

| Task | Do | Don't |
|------|----|----|
| Bug fix in one file | Edit directly | Create PR, request review |
| Add simple function | Write code | Plan architecture |
| Update config value | Change it | Document changes |
| Typo fix | Fix it | Create summary |
| Add missing import | Add it | Verify whole project |
| Simple CSS tweak | Tweak it | Create stylesheet doc |

## What "Fast Code" Means

**DO:**
- Read the file once
- Make the exact change requested
- Save and done

**DON'T:**
- Use `Skill` tool (skip getting confirmation)
- Create multiple drafts
- Add "summary" messages
- Check if tests pass
- Create documentation
- Request code review
- Ask "is this good?"
- Explain what you did

## Constraints

### File Count
- 1 file: Always fast-code
- 2-3 related files: Only if trivial (same change in each)
- 4+ files: Use normal flow

### Scope Size
- Under 50 lines changed: Always fast-code
- 50-200 lines: Only if it's one function/component
- 200+ lines: Use normal flow

### Task Complexity
- Mechanical: `s/old/new/`, add import, update config → fast-code
- Logic change: New function with clear behavior → fast-code
- Design decision: Needs architecture discussion → NOT fast-code

### Risk Level
**Fast-code only for:**
- Feature flags (can toggle off)
- UI tweaks (no backend changes)
- Documentation strings
- Configuration
- Test-only code
- New files (not modifying existing)

**NOT for:**
- Authentication/authorization
- Data access patterns
- API contracts
- Shared utilities
- Core algorithms

## Examples

### ✅ Fast-Code (Do It)
```
"Fix typo in README: 'experiance' → 'experience'"
"Add missing import in src/utils/helpers.ts"
"Update API_URL constant to new endpoint"
"Add console.log for debugging in main.ts"
"Create new config file with default values"
```

### ❌ Not Fast-Code (Use Normal Flow)
```
"Refactor authentication system"
"Optimize database queries"
"Add feature flags everywhere"
"Update all error messages"
"Migrate to new library"
```

## The Iron Law

**If you're thinking about it, it's not fast.**

Red flags:
- "Should I check if this breaks anything?" → Not fast-code
- "Maybe I should verify it works?" → Not fast-code
- "Should I document this?" → Not fast-code
- "Let me create a plan first..." → Not fast-code

**If doubt exists, use normal flow.**

## Real-World Impact

Fast-code saves time by eliminating:
- 5-10 min of planning
- 10-15 min of verification
- 5 min of documentation

**Total:** 20-30 min saved per task

**Cost if wrong:** 5 min to roll back + one redo

**ROI:** Only use on low-risk tasks where 20-min savings > 5-min rollback cost

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skipping file read | Always read first—understand context |
| Making extra changes | Only change what was requested |
| "Improving" nearby code | Don't. Stay in scope. |
| Guessing file structure | Read it. Verify structure. Then edit. |
| "Should I commit this?" | No. Just save. User decides. |
| Thinking about edge cases | Don't. Scope is narrow. Trust requester. |

## When to Abandon Fast-Code

**Mid-task, switch to normal flow if:**
- File is more complex than expected
- You need to change multiple unrelated files
- Edge cases emerge
- You're unsure about the impact
- Changes exceed 200 lines total

**Signal: "Let me read the full context" → Use normal flow**

## Skill Checklist

**Before using fast-code:**
- [ ] Task clearly described (no "make it better")
- [ ] Single focused change
- [ ] Fits in one session (< 30 min)
- [ ] Low risk (not critical, not API, not auth)
- [ ] No verification needed (obvious correctness)
- [ ] User ready for immediate deployment

**If ANY checkbox is unchecked: Use normal flow.**
