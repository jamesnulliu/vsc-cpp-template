from argparse import ArgumentParser, ArgumentTypeError
from enum import Enum, unique
import shutil
from pathlib import Path
import os
import atexit

TEMPLATE_DIR = Path(".templates")

TEMPLATE_GEN_PATHS = [
    "cmake",
    "include",
    "src",
    "lib",
    "test",
    "scripts",
    "CMakeLists.txt",
    ".clangd",
    ".clang-format",
    ".vscode/launch.json",
    ".github/workflows/ci-auto-format-and-commit.yml"
    ".github/workflows/ci-build-and-test.yml",
]

MATCH_PATTERN = "_template_project_name_"


@unique
class ProjectType(Enum):
    cxx_exe = 1
    cxx_lib = 2
    cuda_exe = 3
    cuda_lib = 4


def copy_directory_contents(src_dir, dst_dir):
    src_dir = Path(src_dir)
    dst_dir = Path(dst_dir)

    # Create destination directory if it doesn't exist
    dst_dir.mkdir(parents=True, exist_ok=True)

    # Copy each item in the source directory
    for item in src_dir.glob("*"):
        if item.is_file():
            shutil.copy2(item, dst_dir)
        elif item.is_dir():
            shutil.copytree(item, dst_dir / item.name, dirs_exist_ok=True)


def rename_directory(old_path, new_path):
    if Path(old_path).is_dir():
        Path(old_path).rename(new_path)


def replace_in_file(file_path, old_text, new_text):
    with open(file_path, "r") as file:
        content = file.read()

    content = content.replace(old_text, new_text)

    with open(file_path, "w") as file:
        file.write(content)


def replace_in_directory(directory, old_text, new_text):
    for root, _, files in Path(directory).walk():
        for file in files:
            if file.endswith((".cpp", ".hpp", ".h", ".cu", ".cuh")):
                file_path = Path(root, file)
                replace_in_file(
                    file_path,
                    f"{old_text}",
                    f"{new_text}",
                )


def main(args):
    # Remove ".templates" directory on exit =======================================================
    if args.remove_template:
        atexit.register(shutil.rmtree, TEMPLATE_DIR)
        return

    # Reset project directory by removing all template-generated file =============================
    for path in TEMPLATE_GEN_PATHS:
        path = Path(path)
        if path.is_file():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    if args.reset:
        copy_directory_contents(TEMPLATE_DIR / "reset", ".")
        return

    project_type = ProjectType(args.project_type).name
    project_name = args.project_name

    # Copy contents from common and target project type directory to "." ==========================
    copy_directory_contents(TEMPLATE_DIR / "common", ".")
    copy_directory_contents(TEMPLATE_DIR / project_type, ".")

    # Rename "./include/{MATCH_PATTERN}" to "./include/{project_name}" ============================
    rename_directory(Path("include", MATCH_PATTERN), Path("include", project_name))

    # Rename other {MATCH_PATTERN}s in files ======================================================
    for directory in ["include", "lib", "test", "src"]:
        if Path(directory).is_dir():
            replace_in_directory(directory, MATCH_PATTERN, project_name)
    if Path("CMakeLists.txt").is_file():
        replace_in_file("CMakeLists.txt", MATCH_PATTERN, project_name)

    # Rename <path-to-cuda> in ".clangd" to $CUDA_HOME ============================================
    if args.project_type in [3, 4]:
        if Path(".clangd").is_file():
            replace_in_file(
                ".clangd", "<path-to-cuda>", os.environ.get("CUDA_HOME", "")
            )


if __name__ == "__main__":
    parser = ArgumentParser(description="Project type selector")

    parser.add_argument(
        "--remove-template", action="store_true", help="Remove '.templates' directory."
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset template, remove all generated files",
    )

    parser.add_argument(
        "-t",
        "--project-type",
        type=int,
        choices=[t.value for t in ProjectType],
        help="Type of project to create (1=cxx_exe, 2=cxx_lib, 3=cuda_exe, 4=cuda_lib)",
    )

    def validate_project_name(name):
        if not name.isidentifier():
            raise ArgumentTypeError(f"Project name '{name}' must be a valid identifier")
        return name

    parser.add_argument(
        "-n",
        "--project-name",
        type=validate_project_name,
        help="Name of the project. Affects namespace and the include directory name.",
    )

    args = parser.parse_args()

    if not (args.reset or args.remove_template) and (
        args.project_type is None or args.project_name is None
    ):
        parser.error(
            "--project-type and --project-name are required unless --remove-template or --reset is specified"
        )

    main(args)