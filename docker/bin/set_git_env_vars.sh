# intended to be sourced into other scripts to set the git environment varaibles
# GIT_COMMIT, GIT_SHA, GIT_COMMIT_SHORT, GIT_TAG, GIT_TAG_DATE_BASED, GIT_BRANCH, and BRANCH_NAME.

if [[ -z "$GIT_COMMIT" ]]; then
    export GIT_COMMIT=$(git rev-parse HEAD)
fi
if [[ -z "$GIT_SHA" ]]; then
    export GIT_SHA="${GIT_COMMIT}"
fi
export GIT_COMMIT_SHORT="${GIT_COMMIT:0:6}"
if [[ -z "$GIT_TAG" ]]; then
    export GIT_TAG=$(git describe --tags --exact-match $GIT_COMMIT 2> /dev/null)
fi
if [[ "$GIT_TAG" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}(\.[0-9])?$ ]]; then
    export GIT_TAG_DATE_BASED=true
fi
if [[ -z "$GIT_BRANCH" ]]; then
    export GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    export BRANCH_NAME="$GIT_BRANCH"
fi
export BRANCH_NAME_SAFE="${BRANCH_NAME/\//-}"
export BRANCH_AND_COMMIT="${BRANCH_NAME_SAFE}-${GIT_COMMIT}"
# Docker Hub Stuff
export DEPLOYMENT_DOCKER_REPO="itsre/sumo-kitsune-travis"
export DEPLOYMENT_DOCKER_IMAGE="${DEPLOYMENT_DOCKER_REPO}:full-${GIT_COMMIT_SHORT}"
