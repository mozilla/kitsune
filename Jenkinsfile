@Library('github.com/mozmeao/jenkins-pipeline@20171123.1')
def config
def docker_image

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

    docker_image = "${config.project.docker_name}:${GIT_COMMIT_SHORT}"

    stage("Build") {
      if (!dockerImageExists(docker_image)) {
            sh "echo 'ENV GIT_SHA ${GIT_COMMIT}' >> Dockerfile"
            dockerImagePull( "${config.project.docker_name}:latest")
            dockerImageBuild(docker_image, [
                    "pull": true,
                    "cache_from": "${config.project.docker_name}:latest",
                ])
      }
      else {
        echo "Image ${docker_image} already exists."
      }
    }

    stage("Upload Images") {
      dockerImagePush(docker_image, "mozjenkins-docker-hub")
      onBranch("master") {
        dockerImageTag(docker_image, "${config.project.docker_name}:latest")
        dockerImagePush("${config.project.docker_name}:latest", "mozjenkins-docker-hub")
      }
    }
  }

  milestone()

}
