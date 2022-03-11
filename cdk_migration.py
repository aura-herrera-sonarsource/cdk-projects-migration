import os
import re
from github import Github, Repository, UnknownObjectException, ContentFile

cdk_projects = []
cdk_projects_without_dependencies_file = []


def _add_cdk_repo(cdk_list: list, name: str, cdk_path: str, version: str):
    if cdk_path == "":
        cdk_path = "/"
    repo = {"repo": name, "project_path": cdk_path, "cdk_version": version}
    cdk_list.append(repo)


def _output_projects(projects: list, projects_type: str):
    print(f"\n=> {projects_type} found: {len(projects)}")
    for project in projects:
        print(project)
    print("\n")


def _get_metrics():
    cdk_v1_total = len(
        [project for project in cdk_projects if project["cdk_version"] == "1"]
    )
    cdk_v2_total = len(
        [project for project in cdk_projects if project["cdk_version"] == "2"]
    )
    overall_total = len(cdk_projects)
    progress = cdk_v2_total * 100 / overall_total

    print(f"- Total projects version 1:\t{cdk_v1_total}")
    print(f"- Total projects version 2:\t{cdk_v2_total}")
    print(f"- Total projects overall:\t{overall_total}")
    print(f"\n Migration progress: {progress}%\n")


def _find_dependencies_file(repo: Repository.Repository, cdk_path: str):
    try:
        return repo.get_contents(f"{cdk_path}Pipfile")
    except UnknownObjectException:
        pass

    try:
        return repo.get_contents(f"{cdk_path}requirements.txt")
    except UnknownObjectException:
        pass

    _add_cdk_repo(
        cdk_projects_without_dependencies_file, repo.name, cdk_path, "not found"
    )

    return False


def _find_cdk_version(repo_name: str, cdk_path: str, file_content: str):
    if "aws-cdk.core" in file_content:
        _add_cdk_repo(cdk_projects, repo_name, cdk_path, "1")
    elif "aws-cdk-lib" in file_content:
        _add_cdk_repo(cdk_projects, repo_name, cdk_path, "2")
    else:
        print("aws-cdk.* package not found in Pipfile.")


def _analyze_repo(repo: Repository.Repository):
    contents = repo.get_contents("")
    for file_content in contents:
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            if "cdk.json" in file_content.path:
                cdk_path = file_content.path.removesuffix("cdk.json")
                dependencies_file = _find_dependencies_file(repo, cdk_path)
                if dependencies_file:
                    dependencies_file_decoded = (
                        dependencies_file.decoded_content.decode()
                    )
                    _find_cdk_version(repo.name, cdk_path, dependencies_file_decoded)


def main():
    token = os.environ["GITHUB_TOKEN"]
    g = Github(token)

    for repo in g.get_user().get_repos():
        # later to be changed from 'radar' to 'sonarcloud'
        if re.match(r"radar", repo.name, re.IGNORECASE):
            _analyze_repo(repo)

    if len(cdk_projects_without_dependencies_file) > 0:
        _output_projects(
            cdk_projects_without_dependencies_file,
            "Possible CDK projects without dependencies file",
        )
    if len(cdk_projects) > 0:
        _output_projects(cdk_projects, "CDK projects")
        _get_metrics()
    else:
        print("\nNo cdk projects found.")


if __name__ == "__main__":
    main()
