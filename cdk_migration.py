import os
from github import Github

cdk_projects = []


def _add_cdk_repo(name: str, path: str, version: str):
    repo = {
        'repo': name,
        'project_path': path,
        'cdk_version': version
    }
    cdk_projects.append(repo)


def _output_projects():
    print('CDK repos found:')
    for project in cdk_projects:
        print(project)
    print('\n')


def _get_metrics():
    cdk_v1_total = len([project for project in cdk_projects if project['cdk_version'] == '1'])
    cdk_v2_total = len([project for project in cdk_projects if project['cdk_version'] == '2'])
    overall_total = len(cdk_projects)
    progress = (cdk_v2_total * 100 / overall_total)

    print(f'- Total projects overall:\t{overall_total}')
    print(f'- Total projects version 1:\t{cdk_v1_total}')
    print(f'- Total projects version 2:\t{cdk_v2_total}')
    print(f'\n Migration progress: {progress}%')


def _analyze_repo(repo):
    contents = repo.get_contents('')
    for file_content in contents:
        if file_content.type == 'dir':
            contents.extend(repo.get_contents(file_content.path))
        else:
            if 'cdk.json' in file_content.path:
                cdk_path = file_content.path.removesuffix('cdk.json')
                try:
                    pipfile_content = repo.get_contents(f'{cdk_path}Pipfile')
                    pipfile_content_decoded = pipfile_content.decoded_content.decode()
                    if cdk_path == '':
                        cdk_path = '/'
                    if 'aws-cdk.core' in pipfile_content_decoded:
                        _add_cdk_repo(repo.name, cdk_path, '1')
                    elif 'aws-cdk-lib' in pipfile_content_decoded:
                        _add_cdk_repo(repo.name, cdk_path, '2')
                    else:
                        print('aws-cdk-* package not found in Pipfile.')
                except:
                    print('Pipfile not found.')


def main():
    token = os.environ['GITHUB_TOKEN']
    g = Github(token)

    for repo in g.get_user().get_repos():
        if repo.name.startswith('radar'):
            _analyze_repo(repo)

    _output_projects()
    _get_metrics()


if __name__ == "__main__":
    main()