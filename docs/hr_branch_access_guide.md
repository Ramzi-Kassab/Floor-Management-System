# HR Branch Access Guide

This repository currently tracks only the local `work` branch, and no Git remotes are configured. GitHub will not show the branch until it is pushed to a remote.

## Verify branches locally
1. List local branches: `git branch` — expect to see `work` as the active branch.
2. List all branches (including remotes, if any): `git branch -a`.

## Add a GitHub remote (if missing)
1. Set the remote URL (replace `<org>` and `<repo>`):
   ```bash
   git remote add origin git@github.com:<org>/<repo>.git
   ```
2. Confirm remotes: `git remote -v` should show `origin` once configured.

## Push the HR branch so GitHub can display it
1. From `work`, create and push the HR branch (replace `<branch>` if you prefer a different name):
   ```bash
   git checkout -b hr-portal-fixes
   git push -u origin hr-portal-fixes
   ```
   The `-u` flag sets upstream tracking so future `git push` calls work without extra arguments.

## Locate the branch on GitHub
1. Open the repository page on GitHub.
2. Use the **Branch** dropdown or the **Branches** tab.
3. Search for `hr-portal-fixes` (or your chosen branch name). Once pushed, GitHub lists it under active branches.

## Troubleshooting visibility
- If the branch still does not appear, confirm the push succeeded and that you have access to the correct GitHub repository.
- Run `git fetch --all` to sync local refs with remote and re-check `git branch -a`.
