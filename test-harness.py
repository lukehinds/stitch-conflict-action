import os
import shutil
import subprocess
import argparse
from pathlib import Path
import random

MAIN_BRANCH = "main"



ADJECTIVES = [
    "silent", "brave", "tasty", "angry", "fuzzy", "stormy", "clever",
    "bouncy", "mellow", "sneaky", "heavy", "curious", "zesty", "sleepy",
]

NOUNS = [
    "tiger", "tulip", "banana", "tarmac", "octopus", "nebula", "cascade",
    "kangaroo", "biscuit", "python", "falcon", "avocado", "glacier"
]

def random_case_name():
    return f"{random.choice(ADJECTIVES)}{random.choice(NOUNS)}"


def run(cmd, cwd=None, check=True):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=True)
    if result.returncode != 0 and check:
        print(f"❌ Command failed: {cmd}")
        print(result.stderr)
        raise RuntimeError(result.stderr)
    return result.stdout.strip()

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def init_repo(repo_path):
    print("📁 Initializing new repo...")
    run("git init -b main", cwd=repo_path)
    run("git config user.name 'Test Bot'", cwd=repo_path)
    run("git config user.email 'test@example.com'", cwd=repo_path)

def create_conflicting_branches(repo_path, test_name, base_code, branch1_code, branch2_code):
    print(f"\n🔧 Setting up test case: {test_name}")
    file_path = repo_path / "calc.py"

    # Reset to main
    run(f"git checkout {MAIN_BRANCH}", cwd=repo_path)

    # Write base file
    write_file(file_path, base_code)
    run("git add .", cwd=repo_path)
    run(f"git commit -m 'Base commit for {test_name}'", cwd=repo_path)

    # Create branch 1 and modify
    run(f"git checkout -b {test_name}_branch1", cwd=repo_path)
    write_file(file_path, branch1_code)
    run("git commit -am 'Change A'", cwd=repo_path)

    # Create branch 2 and modify
    run(f"git checkout {MAIN_BRANCH}", cwd=repo_path)
    run(f"git checkout -b {test_name}_branch2", cwd=repo_path)
    write_file(file_path, branch2_code)
    run("git commit -am 'Change B'", cwd=repo_path)

def push_branches(repo_path, test_name):
    print("📤 Pushing branches to origin...")
    branches = [MAIN_BRANCH, f"{test_name}_branch1", f"{test_name}_branch2"]
    for b in branches:
        run(f"git checkout {b}", cwd=repo_path)
        run(f"git push -u origin {b}", cwd=repo_path)

def auto_merge_branch1(repo_path, test_name):
    print("🔁 Merging branch1 into main on GitHub...")
    run(f"git checkout {MAIN_BRANCH}", cwd=repo_path)
    run(f"git merge {test_name}_branch1", cwd=repo_path)
    run(f"git push origin {MAIN_BRANCH}", cwd=repo_path)

def create_pull_request(repo_path, test_name):
    pr_title = f"Test Conflict PR - {test_name}"
    pr_body = "This PR is expected to produce merge conflicts for testing."

    print("🚀 Creating PR using GitHub CLI...")
    run(
        f'gh pr create --base {MAIN_BRANCH} '
        f'--head {test_name}_branch2 '
        f'--title "{pr_title}" '
        f'--body "{pr_body}"',
        cwd=repo_path
    )

def setup(args):
    repo_path = Path(args.path).resolve()
    print(f"🔍 Using repo path: {repo_path}")
    test_name = args.case or random_case_name()
    print(f"🎯 Using test case: {test_name}")


    if not args.existing:
        if repo_path.exists():
            print("♻️ Cleaning up old test repo...")
            shutil.rmtree(repo_path)
        repo_path.mkdir(parents=True)
        init_repo(repo_path)
    else:
        if not (repo_path / ".git").exists():
            raise Exception("🚫 Path does not appear to be a Git repository.")

    # Code variants
    base_code = """def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b"""
    change_a = """def add(a, b):\n    print(f"Adding {a} and {b}")\n    return a + b\n\ndef subtract(a, b):\n    return a - b"""
    change_b = """def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    print(f"Subtracting {b} from {a}")\n    return a - b"""

    create_conflicting_branches(repo_path, args.case, base_code, change_a, change_b)

    if args.push:
        push_branches(repo_path, args.case)

    if args.auto_merge:
        auto_merge_branch1(repo_path, args.case)

    if args.create_pr:
        create_pull_request(repo_path, args.case)

    print("\n✅ Test case ready.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test harness for merge conflict cases")
    parser.add_argument("--existing", action="store_true", help="Use existing git repo")
    parser.add_argument("--path", type=str, default="merge-conflict-test-repo", help="Target repo directory")
    parser.add_argument("--case", type=str, default=None, help="Test case name (auto-generated if omitted)")
    parser.add_argument("--push", action="store_true", help="Push branches to GitHub")
    parser.add_argument("--create-pr", action="store_true", help="Create a pull request for branch2")
    parser.add_argument("--auto-merge", action="store_true", help="Merge branch1 into main to trigger conflict")

    setup(parser.parse_args())
