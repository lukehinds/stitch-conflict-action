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
