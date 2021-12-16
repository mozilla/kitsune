#!/bin/bash
set -exo pipefail
GREEN='\033[1;32m'
NC='\033[0m' # No Color
DOCKER_HUB="https://hub.docker.com/r/mozilla/kitsune/tags/"
PYENV_FILE='.python-version'

function whatsdeployed {
	xdg-open "https://whatsdeployed.io/s-iiX"
}

function deploy {
	REGION=${2}
	REGION_ENV=${3}
	COMMIT_HASH=${4}
	DEPLOY_SECRETS=${5:-NO}
	K8S_NAMESPACE="sumo-${REGION_ENV}"

	if [[ "${DEPLOY_SECRETS}" == "secrets" ]]; then
		echo "Applying secrets"
		${KUBECTL_BIN} -n "${K8S_NAMESPACE}" apply -f "regions/${REGION}/${REGION_ENV}-secrets.yaml"
	else
		echo "Secrets will *NOT* be applied"
	fi

	invoke -f "regions/${REGION}/${REGION_ENV}.yaml" deployments.create-celery --apply --tag "prod-${COMMIT_HASH}"
	invoke -f "regions/${REGION}/${REGION_ENV}.yaml" rollouts.status-celery
	invoke -f "regions/${REGION}/${REGION_ENV}.yaml" deployments.create-cron --apply --tag "prod-${COMMIT_HASH}"
	invoke -f "regions/${REGION}/${REGION_ENV}.yaml" rollouts.status-cron
	invoke -f "regions/${REGION}/${REGION_ENV}.yaml" deployments.create-web --apply --tag "prod-${COMMIT_HASH}"
	invoke -f "regions/${REGION}/${REGION_ENV}.yaml" rollouts.status-web

	post-deploy "$@"

	echo ":tada: Successfully deployed <${DOCKER_HUB}|prod-${COMMIT_HASH}> to <https://${REGION_ENV}-${REGION}.sumo.mozit.cloud/|SUMO-${REGION_ENV} in ${REGION}>"
	printf "${GREEN}OK${NC}\n"
}

function post-deploy {
	REGION=${2}
	REGION_ENV=${3}
	K8S_NAMESPACE="sumo-${REGION_ENV}"

	# run post-deployment tasks
	echo "Running post-deployment tasks"
	# Get the name of a running web pod on which we can run the post-deploy script
	SUMO_POD=$(${KUBECTL_BIN} -n "${K8S_NAMESPACE}" get pods | egrep 'sumo-.*-web' | grep Running | head -1 | awk '{ print $1 }')
	${KUBECTL_BIN} -n "${K8S_NAMESPACE}" exec "${SUMO_POD}" bin/run-post-deploy.sh
}

function initialize {
	REGION=${2}

	if [ -f "./regions/${REGION}/kubectl" ]; then
		KUBECTL_BIN="./regions/${REGION}/kubectl"
	else
		KUBECTL_BIN=$(which kubectl)
	fi
	export KUBECTL_BIN

	if [ -f "./regions/${REGION}/kubeconfig" ]; then
		export KUBECONFIG="./regions/${REGION}/kubeconfig"
	fi

	${KUBECTL_BIN} version >/dev/null
	if [ $? == 1 ]; then
		echo "Can't connect to the Kubernetes server. Exiting here"
		exit 1
	fi

	compare-client-server-versions
}

function compare-client-server-versions {
	CLIENT_VERSION=$(${KUBECTL_BIN} version --short | grep Client | awk -F. '{print $2}')
	SERVER_VERSION=$(${KUBECTL_BIN} version --short | grep Server | awk -F. '{print $2}')

	# Calculate difference between versions
	DIFFERENCE=$((CLIENT_VERSION - SERVER_VERSION))
	if ((DIFFERENCE > 1)) || ((DIFFERENCE < -1)); then
		echo "Version mismatch; Client and server versions must be equal or have 1 minor version step. Exiting here"
		echo "Client version: $CLIENT_VERSION, Server version: $SERVER_VERSION "
		exit 1
	fi
}

if ![ -f "$PYENV_FILE" ]; then
	source venv/bin/activate
fi
initialize "$@"

$1 $@
