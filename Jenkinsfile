@Library('github.com/mozmeao/jenkins-pipeline@20171123.1')
def config
def docker_image
def dc_name

conduit {
    node {
        stage("Prepare") {
            checkout scm
            setGitEnvironmentVariables()

            try {
                config = readYaml file: "jenkins.yml"
            }
            catch (e) {
                config = []
            }
            println "config ==> ${config}"

            if (!config || (config && config.pipeline && config.pipeline.enabled == false)) {
                println "Pipeline disabled."
            }
        }

        docker_image = "${config.project.docker_name}:full-${GIT_COMMIT_SHORT}"

        stage("Build") {
            if (!dockerImageExists(docker_image)) {
                sh "GIT_SHA=${GIT_COMMIT} GIT_SHA_SHORT=${GIT_COMMIT_SHORT} LOCALE_ENV=production ./docker/bin/build-docker-images.sh"
            }
            else {
                echo "Image ${docker_image} already exists."
            }
        }

        stage("Upload Images") {
            dockerImagePush("${config.project.docker_name}:full-${GIT_COMMIT_SHORT}", "mozjenkins-docker-hub")
            dockerImagePush("${config.project.docker_name}:full-no-locales-${GIT_COMMIT_SHORT}", "mozjenkins-docker-hub")
            dockerImagePush("${config.project.docker_name}:locales-${GIT_COMMIT_SHORT}", "mozjenkins-docker-hub")
            dockerImagePush("${config.project.docker_name}:staticfiles-${GIT_COMMIT_SHORT}", "mozjenkins-docker-hub")
            dockerImagePush("${config.project.docker_name}:base-dev-${GIT_COMMIT_SHORT}", "mozjenkins-docker-hub")
            dockerImagePush("${config.project.docker_name}:base-${GIT_COMMIT_SHORT}", "mozjenkins-docker-hub")
        }

        stage("Run Flake8") {
            sh "docker run ${config.project.docker_name}:full-no-locales-${GIT_COMMIT_SHORT} flake8 kitsune"
        }
        stage("Run Mocha Tests") {
            sh "docker run kitsune:staticfiles-latest ./node_modules/.bin/mocha --compilers js:babel/register --recursive kitsune/*/static/*/js/tests/* \$@"
        }
        stage("Run Unit Tests") {
            try {
                dc_name = "${config.project.name}-${BUILD_NUMBER}-${GIT_COMMIT_SHORT}"
                sh "docker-compose --project-name ${dc_name} up -d mariadb"
                sh "docker-compose --project-name ${dc_name} up -d elasticsearch"
                sh "docker-compose --project-name ${dc_name} up -d redis"
                // Replace with urlwait or takis
                sh "sleep 10s;"
                sh "docker-compose --project-name ${dc_name} -f docker-compose.yml -f docker/composefiles/test.yml run web ./bin/run-unit-tests.sh"
            }
            finally {
                sh "docker-compose --project-name ${dc_name} -f docker-compose.yml -f docker/composefiles/test.yml kill"
            }
        }
        stage("Upload Latest Images") {
            // When on master branch tag and push push the latest tag
            onBranch("master") {
                dockerImageTag("${config.project.docker_name}:full-${GIT_COMMIT_SHORT}", "${config.project.docker_name}:full-latest")
                dockerImagePush("${config.project.docker_name}:full-latest", "mozjenkins-docker-hub")

                dockerImageTag("${config.project.docker_name}:full-no-locales-${GIT_COMMIT_SHORT}", "${config.project.docker_name}:full-no-locales-latest")
                dockerImagePush("${config.project.docker_name}:full-no-locales-latest", "mozjenkins-docker-hub")

                dockerImageTag("${config.project.docker_name}:locales-${GIT_COMMIT_SHORT}", "${config.project.docker_name}:locales-latest")
                dockerImagePush("${config.project.docker_name}:locales-latest", "mozjenkins-docker-hub")

                dockerImageTag("${config.project.docker_name}:staticfiles-${GIT_COMMIT_SHORT}", "${config.project.docker_name}:staticfiles-latest")
                dockerImagePush("${config.project.docker_name}:staticfiles-latest", "mozjenkins-docker-hub")

                dockerImageTag("${config.project.docker_name}:base-dev-${GIT_COMMIT_SHORT}", "${config.project.docker_name}:base-dev-latest")
                dockerImagePush("${config.project.docker_name}:base-dev-latest", "mozjenkins-docker-hub")

                dockerImageTag("${config.project.docker_name}:base-${GIT_COMMIT_SHORT}", "${config.project.docker_name}:base-latest")
                dockerImagePush("${config.project.docker_name}:base-latest", "mozjenkins-docker-hub")

                sh "docker/bin/upload-staticfiles.sh"
            }
        }

    }
}
