set -e
GREEN='\033[1;32m'
NC='\033[0m' # No Color


function whatsdeployed {
    xdg-open "https://whatsdeployed.io/s-iiX"
}

function deploy {
    export KUBECTL_BIN="./regions/${2}/kubectl"
    export KUBECONFIG="./regions/${2}/kubeconfig"
    ${KUBECTL_BIN} -n sumo-${3} apply -f "regions/${2}/${3}-secrets.yaml"
    invoke  -f "regions/${2}/${3}.yaml" deployments.create-celery --apply --tag full-${4}
    invoke  -f "regions/${2}/${3}.yaml" rollouts.status-celery
    invoke  -f "regions/${2}/${3}.yaml" deployments.create-cron --apply --tag full-${4}
    invoke  -f "regions/${2}/${3}.yaml" rollouts.status-cron
    invoke  -f "regions/${2}/${3}.yaml" deployments.create-web --apply --tag full-${4}
    invoke  -f "regions/${2}/${3}.yaml" rollouts.status-web
    printf "${GREEN}OK${NC}\n"
}

source venv/bin/activate

$1 $@
