# Create PR

## Overview

Create a well-structured pull request with proper description, labels, and reviewers.

## Steps

1. **Get target branch**
   - Determine the target branch for PR
   - Ask for confirmation from user
   - **_CRITICAL_**: Do not proceed without getting confirmation or actual target branch name

2. **Update README.md**
   - Analyze the current codebase structure and contents
   - Create or update README.md if already present
   - Ensure README.md accurately reflects the current state of the codebase

3. **Create or update changelog**
   - Use the changelog-generator agent to create user-friendly changelog entries

4. **Prepare branch**
   - Ensure all changes are committed
   - Push branch to remote
   - Verify branch is up to date with target branch

5. **Write PR description**
   - Summarize changes clearly
   - Include context and motivation
   - List any breaking changes
   - Add screenshots if UI changes

6. **Set up PR**
   - Create PR with descriptive title to target branch
   - Add appropriate labels
   - Assign reviewers
   - Link related issues

## PR Template

- [ ] Feature A
- [ ] Bug fix B
- [ ] Unit tests pass
- [ ] Manual testing completed
