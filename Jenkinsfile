import groovy.json.JsonOutput

/** Map of Tox environments and associated capabilities */
def environments = [
  desktop: [
    browserName: 'Firefox',
    version: '47.0',
    platform: 'Windows 7'
  ],
  mobile: [
    browserName: 'Browser',
    platformName: 'Android',
    platformVersion: '5.1',
    deviceName: 'Android Emulator',
    appiumVersion: '1.5.3'
  ]
]

/** Transform a map into a list of maps
 *
 * @param aMap map to transform
 * @return a list of maps
*/
@NonCPS
def entrySet(aMap) {
  aMap.collect {
    k, v -> [key: k, value: v]
  }
}

/** Write capabilities to JSON file
 *
 * @param desiredCapabilities capabilities to include in the file
*/
def writeCapabilities(desiredCapabilities) {
    def defaultCapabilities = [
        build: env.BUILD_TAG,
        public: 'public restricted'
    ]
    def capabilities = defaultCapabilities.clone()
    capabilities.putAll(desiredCapabilities)
    def json = JsonOutput.toJson([capabilities: capabilities])
    writeFile file: 'capabilities.json', text: json
}

/** Run Tox
 *
 * @param environment test environment to run
*/
def runTox(environment) {
  try {
    wrap([$class: 'AnsiColorBuildWrapper']) {
      withCredentials([[
        $class: 'StringBinding',
        credentialsId: 'SAUCELABS_API_KEY',
        variable: 'SAUCELABS_API_KEY']]) {
        withEnv(["PYTEST_ADDOPTS=${PYTEST_ADDOPTS} " +
          "--base-url=${PYTEST_BASE_URL} " +
          "--driver=SauceLabs " +
          "--variables=capabilities.json " +
          "--color=yes"]) {
          sh "tox -e ${environment}"
        }
      }
    }
  } catch(err) {
    currentBuild.result = 'FAILURE'
    throw err
  } finally {
    dir('results') {
      stash environment
    }
  }
}

/** Send a notice to #fxtest-alerts on irc.mozilla.org with the build result
 *
 * @param result outcome of build
*/
def ircNotification(result) {
  def nick = "fxtest${BUILD_NUMBER}"
  def channel = '#fx-test-alerts'
  result = result.toUpperCase()
  def message = "Project ${JOB_NAME} build #${BUILD_NUMBER}: ${result}: ${BUILD_URL}"
  node {
    sh """
        (
        echo NICK ${nick}
        echo USER ${nick} 8 * : ${nick}
        sleep 5
        echo "JOIN ${channel}"
        echo "NOTICE ${channel} :${message}"
        echo QUIT
        ) | openssl s_client -connect irc.mozilla.org:6697
    """
  }
}

stage('Checkout') {
  node {
    timestamps {
      deleteDir()
      checkout scm
      stash 'workspace'
    }
  }
}

def builders = [:]
for (entry in entrySet(environments)) {
  def environment = entry.key
  def capabilities = entry.value
  builders[(environment)] = {
    node {
      timeout(time: 1, unit: 'HOURS') {
        timestamps {
          deleteDir()
          unstash 'workspace'
          writeCapabilities(capabilities)
          withCredentials([[
            $class: 'FileBinding',
            credentialsId: 'SUMO_VARIABLES',
            variable: 'VARIABLES']]) {
            withEnv(["PYTEST_ADDOPTS=--variables=${VARIABLES}"]) {
              runTox(environment)
            }
          }
        }
      }
    }
  }
}

try {
  stage('Test') {
    parallel builders
  }
} catch(err) {
  currentBuild.result = 'FAILURE'
  ircNotification(currentBuild.result)
  mail(
    body: "${BUILD_URL}",
    from: "firefox-test-engineering@mozilla.com",
    replyTo: "firefox-test-engineering@mozilla.com",
    subject: "Build failed in Jenkins: ${JOB_NAME} #${BUILD_NUMBER}",
    to: "fte-ci@mozilla.com")
  throw err
} finally {
  stage('Results') {
    def keys = environments.keySet() as String[]
    def htmlFiles = []
    node {
      deleteDir()
      sh 'mkdir results'
      dir('results') {
        for (int i = 0; i < keys.size(); i++) {
          // Unstash results from each environment
          unstash keys[i]
          htmlFiles.add("${keys[i]}.html")
        }
      }
      publishHTML(target: [
        allowMissing: false,
        alwaysLinkToLastBuild: true,
        keepAll: true,
        reportDir: 'results',
        reportFiles: htmlFiles.join(','),
        reportName: 'HTML Report'])
      junit 'results/*.xml'
      archiveArtifacts 'results/*'
    }
  }
}
