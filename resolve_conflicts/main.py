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
    pr_number = int(os.getenv("PR_NUMBER"))

    g = Github(github_token)
    repo = g.get_repo(os.getenv("GITHUB_REPOSITORY"))

    # 🧪 Attempt to merge origin/main into this branch
    # Simulate what GitHub does: try merging origin/main
    print("🔁 Merging origin/main into PR branch to check for conflicts...")
    run_shell(["git", "fetch", "origin", "main"])
    try:
        run_shell(["git", "merge", "--no-commit", "--no-ff", "origin/main"])
    except subprocess.CalledProcessError:
        print("⚠️ Merge failed due to conflicts (expected if conflicting).")

    # Check for conflicted files
    conflicted = run_shell(["git", "diff", "--name-only", "--diff-filter=U"]).splitlines()

    if not conflicted:
        print("✅ No merge conflicts.")
        run_shell(["git", "merge", "--abort"])
        manage_conflict_label(repo, pr_number, add=False)
        return

    print(f"🛠 Merge conflicts detected in: {conflicted}")
    manage_conflict_label(repo, pr_number, add=True)

    # Extract and send to AI
    conflict_content = find_conflicts(conflicted)
    resolved_files = send_to_ai(conflict_content, openrouter_key)
    apply_fixes(resolved_files)

    # Commit + push
    run_shell(["git", "config", "user.name", "github-actions"])
    run_shell(["git", "config", "user.email", "github-actions@github.com"])
    run_shell(["git", "add", "."])
    run_shell(["git", "commit", "-m", "🤖 Resolved merge conflicts with AI"])
    run_shell(["git", "push"])

    # Clean up label
    manage_conflict_label(repo, pr_number, add=False)


if __name__ == "__main__":
    main()
