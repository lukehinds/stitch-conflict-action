import os
import subprocess
import sys
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


def resolve_pr_conflicts(repo, pr_number, openrouter_key, conflict_files):
    print(f"🔧 Resolving conflicts for PR #{pr_number} in files: {conflict_files}")

    # The workflow already attempted the merge, leaving conflicts.
    # We proceed directly to finding conflict markers in the specified files.
    # Assuming find_conflicts() can work on the current state or use the file list.
    conflict_blocks = find_conflicts(conflict_files) # Pass files if needed by find_conflicts

    if not conflict_blocks:
        print("🤔 No conflict markers found in specified files despite merge failure. Aborting.")
        # Abort the merge as we can't resolve automatically
        try:
            run_shell(["git", "merge", "--abort"])
            print("Git merge aborted.")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Failed to abort merge: {e}")
        sys.exit(1) # Exit to indicate failure

    print("🤖 Sending conflicts to AI for resolution...")
    ai_suggestion = send_to_ai(conflict_blocks, openrouter_key)

    print("✍️ Applying AI suggestions...")
    apply_fixes(ai_suggestion)

    print("💾 Committing resolved files...")
    run_shell(["git", "add", "."]) # Stage all resolved files
    # Commit message reflects the merge was done into the base branch first
    commit_message = f'Auto-resolve conflicts for PR #{pr_number} via @fix-merge'
    run_shell(["git", "commit", "-m", commit_message])

    # Push logic remains in the workflow step after the script finishes
    # print(f"✅ Successfully resolved conflicts for {conflict_files}.")
    # We don't push from here anymore, the workflow step does it.


def main():
    github_token = os.getenv("GITHUB_TOKEN")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    pr_number_str = os.getenv("PR_NUMBER")
    repo_name = os.getenv("GITHUB_REPOSITORY")

    # Strip whitespace from PR number string if it exists
    if pr_number_str:
        pr_number_str = pr_number_str.strip()

    if not github_token or not openrouter_key or not repo_name:
        print("❌ Missing required environment variables (GITHUB_TOKEN, OPENROUTER_API_KEY, GITHUB_REPOSITORY)")
        sys.exit(1)

    # Check if file paths were passed as arguments from the workflow
    conflict_files_from_args = sys.argv[1:]

    g = Github(github_token)
    repo = g.get_repo(repo_name)

    if conflict_files_from_args:
        # Workflow passed specific files via @fix-merge
        print(f"🔧 Resolving specific files passed as arguments: {conflict_files_from_args}")
        # Check pr_number_str again after stripping
        if not pr_number_str:
            print("❌ PR_NUMBER environment variable is required and non-empty when files are passed via arguments.")
            sys.exit(1)
        try:
            pr_number = int(pr_number_str) # Use stripped value
            # Pass the list of conflict files to the resolver function
            resolve_pr_conflicts(repo, pr_number, openrouter_key, conflict_files_from_args)
        except ValueError:
            print(f"❌ Invalid PR_NUMBER: {pr_number_str}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error resolving conflicts for PR #{pr_number_str}: {e}")
            # Consider adding git merge --abort here if needed
            sys.exit(1)

    elif pr_number_str:
        # Handle case where only PR_NUMBER is set (e.g., manual trigger, future use)
        # Check pr_number_str again after stripping
        print(f"🔧 Resolving conflicts for specific PR #{pr_number_str} based on environment variable.")
        print("⚠️ Warning: No specific conflict files provided. This mode might require changes.")
        # You might need to manually run git merge here or adjust logic
        # For now, we'll assume this path isn't hit by the current workflow
        # try:
        #     pr_number = int(pr_number_str) # Use stripped value
        #     # Placeholder: Need to define how conflicts are identified here
        #     # resolve_pr_conflicts(repo, pr_number, openrouter_key, [])
        # except ValueError:
        #     print(f"❌ Invalid PR_NUMBER: {pr_number_str}")
        #     sys.exit(1)
        # except Exception as e:
        #     print(f"❌ Error resolving conflicts for PR #{pr_number_str}: {e}")
        #     sys.exit(1)
        pass # Avoid running resolve_pr_conflicts without file list for now

    else:
        # Scan all open PRs if no specific PR or files are given (e.g., scheduled run)
        print("🧹 No PR number or specific files provided — scanning for conflicted PRs...")
        try:
            conflicted_prs = [
                pr for pr in repo.get_pulls(state="open")
                # Add more robust check? e.g., label or mergeable_state == "dirty"
                if pr.mergeable_state == "dirty"
            ]
            if not conflicted_prs:
                print("✅ No conflicted PRs found requiring resolution.")
                return

            for pr in conflicted_prs:
                print(f"🔧 Attempting to resolve PR #{pr.number}: {pr.title}")
                try:
                    # Pass an empty list or modify to detect files
                    # resolve_pr_conflicts(repo, pr.number, openrouter_key, [])
                    pass # Avoid running resolve_pr_conflicts without file list for now
                except Exception as e:
                    print(f"❌ Error resolving PR #{pr.number}: {e}")
                    # Continue to the next PR
        except Exception as e:
            print(f"❌ Error scanning for conflicted PRs: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
