import os
import subprocess
from github import Github
from resolve_conflicts.utils import find_conflicts, send_to_ai, apply_fixes

def run_shell(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()

def fetch_and_merge_main():
    # Ensure we can detect merge conflicts
    run_shell(["git", "fetch", "origin", "main"])
    try:
        run_shell(["git", "merge", "origin/main"])
    except subprocess.CalledProcessError:
        # This is *expected* when there are conflicts
        print("❗ Merge conflict detected during `git merge origin/main`")
        return True
    return False


def manage_conflict_label(repo, pr_number, add=True):
    label_name = "merge-conflict"
    pr = repo.get_pull(pr_number)
    labels = [label.name for label in pr.get_labels()]

    if add and label_name not in labels:
        pr.add_to_labels(label_name)
        print(f"🟥 Added label `{label_name}`")
    elif not add and label_name in labels:
        pr.remove_from_labels(label_name)
        print(f"✅ Removed label `{label_name}`")


def resolve_pr_conflicts(repo, pr_number, openrouter_key):
    pr = repo.get_pull(pr_number)
    head_branch = pr.head.ref
    base_branch = pr.base.ref

    print(f"Checking out PR branch: {head_branch}")
    run_shell(["git", "checkout", head_branch])
    run_shell(["git", "pull", "origin", head_branch]) # Ensure local branch is up-to-date

    print(f"Fetching base branch: {base_branch}")
    run_shell(["git", "fetch", "origin", base_branch])

    print(f"Attempting merge of {base_branch} into {head_branch}")
    try:
        run_shell(["git", "merge", f"origin/{base_branch}"])
        print("✅ No merge conflicts found.")
        manage_conflict_label(repo, pr_number, add=False)
        return # Success, no conflicts
    except subprocess.CalledProcessError:
        print("❗ Merge conflict detected.")
        manage_conflict_label(repo, pr_number, add=True)

    conflict_blocks = find_conflicts()
    if not conflict_blocks:
        print("🤔 No conflict markers found despite merge failure. Manual check needed.")
        # Consider aborting the merge here if needed
        # run_shell(["git", "merge", "--abort"])
        return

    print("🤖 Sending conflicts to AI for resolution...")
    ai_suggestion = send_to_ai(conflict_blocks, openrouter_key)

    print("Applying AI suggestions...")
    apply_fixes(ai_suggestion)

    print("Committing resolved files...")
    run_shell(["git", "add", "."]) # Stage all resolved files
    run_shell(["git", "commit", "-m", f'Auto-resolve conflicts for PR #{pr_number}'])

    print(f"Pushing resolved branch {head_branch}...")
    run_shell(["git", "push", "origin", head_branch])
    manage_conflict_label(repo, pr_number, add=False)
    print(f"✅ Successfully resolved conflicts and pushed to {head_branch}.")


def main():
    github_token = os.getenv("GITHUB_TOKEN")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    pr_number = os.getenv("PR_NUMBER")

    g = Github(github_token)
    repo = g.get_repo(os.getenv("GITHUB_REPOSITORY"))

    if pr_number:
        pr = repo.get_pull(int(pr_number))
        resolve_pr_conflicts(repo, pr.number, openrouter_key)
    else:
        print("🧹 No PR number provided — scanning for conflicted PRs...")
        conflicted_prs = [
            pr for pr in repo.get_pulls(state="open")
            if pr.mergeable_state == "dirty"
        ]
        for pr in conflicted_prs:
            print(f"🔧 Attempting to resolve PR #{pr.number}: {pr.title}")
            try:
                resolve_pr_conflicts(repo, pr.number, openrouter_key)
            except Exception as e:
                print(f"❌ Error resolving PR #{pr.number}: {e}")
