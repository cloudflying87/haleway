#!/usr/bin/env python3
"""
Continue Here - Project Setup Automation
==========================================
This script automates the remaining setup steps after the initial project
structure has been created by setup_new_project.py.

Run this from your NEW project directory (not BuildTemplate).
"""

import subprocess
import sys
from pathlib import Path


class ContinueSetup:
    """Automate the continuation of project setup."""

    def __init__(self):
        self.project_dir = Path.cwd()
        self.project_name = "haleway"
        self.python_version = "3.13.1"
        self.venv_python = None  # Will be set after creating virtualenv

    def print_header(self, text):
        """Print a formatted header."""
        print(f"\n{'=' * 60}")
        print(f"  {text}")
        print("=" * 60)

    def print_step(self, number, text):
        """Print a step number and description."""
        print(f"\n{'─' * 60}")
        print(f"📍 Step {number}: {text}")
        print("─" * 60)

    def run_command(self, cmd, description, check=True, shell=False, show_output=True, env=None):
        """Run a command and handle errors."""
        print(f"\n▶ {description}")
        print(f"  Command: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")

        try:
            if show_output:
                # Don't capture output - show it in real-time
                if shell:
                    result = subprocess.run(cmd, shell=True, check=check, env=env)
                else:
                    result = subprocess.run(cmd, check=check, env=env)

                if result.returncode == 0:
                    print("✅ Success")
                return True
            else:
                # Capture output (for quick commands)
                if shell:
                    result = subprocess.run(
                        cmd, shell=True, check=check, capture_output=True, text=True, env=env
                    )
                else:
                    result = subprocess.run(
                        cmd, check=check, capture_output=True, text=True, env=env
                    )

                if result.stdout:
                    print(result.stdout)
                if result.returncode == 0:
                    print("✅ Success")
                return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e}")
            if hasattr(e, "stderr") and e.stderr:
                print(f"   {e.stderr}")
            if check:
                raise
            return False
        except FileNotFoundError:
            print("❌ Command not found")
            return False

    def create_pyenv(self):
        """Create and activate Python environment."""
        self.print_step(1, "Creating Python Environment")

        # Check if pyenv is installed
        try:
            subprocess.run(["pyenv", "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("⚠️  pyenv not found. Skipping virtual environment creation.")
            print("   You can install pyenv later or use venv:")
            print("   python3 -m venv .venv")
            print("   source .venv/bin/activate")
            return False

        # Check if environment already exists
        result = subprocess.run(["pyenv", "virtualenvs", "--bare"], capture_output=True, text=True)

        if self.project_name in result.stdout:
            print(f"✅ Environment '{self.project_name}' already exists")
            # Set the virtualenv Python path
            pyenv_root = Path.home() / ".pyenv" / "versions" / self.project_name / "bin" / "python"
            if pyenv_root.exists():
                self.venv_python = str(pyenv_root)
            return True

        # Create environment
        success = self.run_command(
            ["pyenv", "virtualenv", self.python_version, self.project_name],
            f"Creating pyenv environment: {self.project_name}",
            check=False,
        )

        if success:
            # Set the virtualenv Python path
            pyenv_root = Path.home() / ".pyenv" / "versions" / self.project_name / "bin" / "python"
            if pyenv_root.exists():
                self.venv_python = str(pyenv_root)
                print("\n✅ Environment created!")
                print(f"   Using: {self.venv_python}")
            else:
                print("\n✅ Environment created!")
                print("   It will auto-activate when you cd into this directory")
                print("   (thanks to .python-version file)")

        return success

    def install_uv(self):
        """Install UV package manager."""
        self.print_step(2, "Installing UV Package Manager (Optional)")

        # Use virtualenv Python if available, otherwise system Python
        python_cmd = self.venv_python or sys.executable

        # Check if already installed
        try:
            subprocess.run(["uv", "--version"], capture_output=True, check=True)
            print("✅ UV already installed")
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        print("UV is 10-100x faster than pip!")
        if input("Install UV? (Y/n): ").lower() != "n":
            return self.run_command(
                [python_cmd, "-m", "pip", "install", "uv"], "Installing UV via pip", check=False
            )
        else:
            print("⏭️  Skipping UV installation")
            return False

    def install_dependencies(self):
        """Install project dependencies."""
        self.print_step(3, "Installing Dependencies")

        print("\n⏱️  This may take a few minutes on first run...")

        # Use virtualenv Python if available
        python_cmd = self.venv_python or sys.executable

        makefile = self.project_dir / "Makefile"
        if not makefile.exists():
            print("⚠️  Makefile not found. Installing manually...")
            return self.run_command(
                [python_cmd, "-m", "pip", "install", "-r", "requirements/development.txt"],
                "Installing dependencies with pip",
                check=False,
            )

        # Set up environment to use virtualenv
        import os

        env = os.environ.copy()
        if self.venv_python:
            venv_bin = str(Path(self.venv_python).parent)
            env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"
            env["VIRTUAL_ENV"] = str(Path(self.venv_python).parent.parent)
            print(f"   Using virtualenv: {env['VIRTUAL_ENV']}")

        # Try using make commands with virtualenv activated
        self.run_command(
            ["make", "install-uv"],
            "Installing UV via Makefile",
            check=False,
            env=env if self.venv_python else None,
        )

        return self.run_command(
            ["make", "install"],
            "Installing all dependencies",
            check=False,
            env=env if self.venv_python else None,
        )

    def verify_django_setup(self):
        """Verify Django project is properly set up."""
        self.print_step(4, "Verifying Django Project")

        # Check if manage.py exists
        manage_py = self.project_dir / "manage.py"
        if not manage_py.exists():
            print("❌ manage.py not found!")
            print("   This script expects a project created by setup_new_project.py")
            return False

        # Check if config/settings exists
        config_settings = self.project_dir / "config" / "settings"
        if not config_settings.exists():
            print("❌ config/settings/ not found!")
            print("   This script expects a project created by setup_new_project.py")
            return False

        # Check if core app exists
        core_app = self.project_dir / "apps" / "core"
        if not core_app.exists():
            print("❌ apps/core/ not found!")
            print("   This script expects a project created by setup_new_project.py")
            return False

        print("✅ Django project structure verified")
        return True

    def run_initial_setup(self):
        """Run initial Django setup commands."""
        self.print_step(5, "Running Initial Setup")

        # Use virtualenv Python if available
        python_cmd = self.venv_python or "python"

        # Set up environment to use virtualenv
        import os

        env = None
        if self.venv_python:
            env = os.environ.copy()
            venv_bin = str(Path(self.venv_python).parent)
            env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"
            env["VIRTUAL_ENV"] = str(Path(self.venv_python).parent.parent)

        makefile = self.project_dir / "Makefile"
        if makefile.exists():
            return self.run_command(
                ["make", "setup"],
                "Running make setup (migrations, pre-commit hooks, etc.)",
                check=False,
                env=env,
            )
        else:
            # Manual setup
            print("Running migrations...")
            self.run_command(
                [python_cmd, "manage.py", "migrate"], "Applying database migrations", check=False
            )
            return True

    def initialize_git(self):
        """Initialize git repository and create initial commit."""
        self.print_step(6, "Initializing Git Repository")

        git_dir = self.project_dir / ".git"

        if git_dir.exists():
            print("✅ Git repository already initialized")
        else:
            self.run_command(["git", "init"], "Initializing git repository", check=True)

        # Check if there are uncommitted changes
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)

        if result.stdout.strip():
            if input("\nCreate initial commit? (Y/n): ").lower() != "n":
                self.run_command(["git", "add", "."], "Staging all files", check=False)

                self.run_command(
                    ["git", "commit", "-m", "Initial project setup"],
                    "Creating initial commit",
                    check=False,
                )

                print("\n📝 Next: Add remote and push")
                print(f"   git remote add origin git@github.com:username/{self.project_name}.git")
                print("   git push -u origin main")
        else:
            print("✅ No changes to commit")

        return True

    def show_next_steps(self):
        """Show what to do next."""
        self.print_header("✅ Setup Complete!")

        print(f"""
🎉 Your {self.project_name} project is ready!

🚀 Start Development:
   make run
   # or
   python manage.py runserver

📝 Create Superuser:
   python manage.py createsuperuser

🌐 Access Your Site:
   - Homepage: http://localhost:8000 (You made it! 🎉)
   - Admin: http://localhost:8000/admin
   - Health: http://localhost:8000/health

📚 Documentation:
   - Quick reference: NEXT_STEPS.md
   - Complete guides: docs/SETUP_GUIDE.md
   - Beginner tutorial: docs/BEGINNERS_GUIDE.md
   - Your design system: docs/STYLE_GUIDE.md

🧹 Clean Up:
   Once you're up and running, you can delete:
   - continue_here.py (this script)
   - NEXT_STEPS.md (the guide)

Happy coding! 🎉
""")

    def run(self):
        """Run the complete continuation setup."""
        self.print_header(f"🚀 Continue Setup: {self.project_name}")

        print(f"""
This script will help you complete your project setup.

📍 Current directory: {self.project_dir}
🐍 Python version: {self.python_version}

We'll automate:
  1. Creating Python environment
  2. Installing UV (optional)
  3. Installing dependencies
  4. Verifying Django project
  5. Running migrations
  6. Initializing git

Press Ctrl+C at any time to stop.
""")

        if input("Continue? (Y/n): ").lower() == "n":
            print("\n❌ Setup cancelled")
            print("   You can run this script again anytime")
            print("   Or follow manual steps in NEXT_STEPS.md")
            return

        try:
            # Run each step
            self.create_pyenv()
            self.install_uv()
            self.install_dependencies()
            if not self.verify_django_setup():
                print("\n❌ Django project verification failed")
                print("   This script only works with projects created by setup_new_project.py")
                sys.exit(1)
            self.run_initial_setup()
            self.initialize_git()

            # Show what's next
            self.show_next_steps()

        except KeyboardInterrupt:
            print("\n\n⚠️  Setup interrupted")
            print("   You can run this script again to continue")
            print("   Or follow manual steps in NEXT_STEPS.md")
            sys.exit(1)
        except Exception as e:
            print(f"\n\n❌ Error during setup: {e}")
            print("   See NEXT_STEPS.md for manual setup instructions")
            sys.exit(1)


def main():
    """Main entry point."""
    setup = ContinueSetup()
    setup.run()


if __name__ == "__main__":
    main()
