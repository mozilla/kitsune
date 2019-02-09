#!/bin/bash
EXIT=0
BASE_URL=${1:-https://support.mozilla.org}
URLS=(
    "/"
    "/de/"
    "/kb/insecure-password-warning-firefox"
    "/kb/get-started-firefox-overview-main-features"
    "/kb/how-change-your-default-browser-windows-10"
    "/robots.txt"
    "/healthz/"
    "/1/firefox/53.0.2/WINNT/en-US/insecure-password"
)

function check_http_code {
    echo -n "Checking URL ${1} "
    curl -X GET -L -s -o /dev/null -I -w "%{http_code}" $1 | grep ${2:-200} > /dev/null
    if [ $? -eq 0 ];
    then
        echo "OK"
    else
        echo "Failed"
        EXIT=1
    fi
}

for url in ${URLS[*]}
do
    check_http_code ${BASE_URL}${url}
done

# Check a page that throws 404. Not ideal but will surface 500s
check_http_code ${BASE_URL}/foo 404

exit ${EXIT}
