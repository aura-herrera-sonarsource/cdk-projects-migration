# CDK projects migration

This script will use a Github token (with all `repo` permissions) and retrieve all repositories starting with a specific
value (eg. "sonarcloud") to then determine if this repo contains (or not) a cdk project.
