#!/usr/bin/python
#
# Copyright 2011-2013 Software freedom conservancy
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.common.exceptions import WebDriverException
from .service import Service
from .options import Options

class WebDriver(RemoteWebDriver):
    """
    Controls the ChromeDriver and allows you to drive the browser.

    You will need to download the ChromeDriver executable from
    http://chromedriver.storage.googleapis.com/index.html
    """

    def __init__(self, executable_path="chromedriver", port=0,
                 chrome_options=None, service_args=None,
                 desired_capabilities=None, service_log_path=None):
        """
        Creates a new instance of the chrome driver.

        Starts the service and then creates new instance of chrome driver.

        :Args:
         - executable_path - path to the executable. If the default is used it assumes the executable is in the $PATH
         - port - port you would like the service to run, if left as 0, a free port will be found.
         - desired_capabilities: Dictionary object with non-browser specific
           capabilities only, such as "proxy" or "loggingPref".
         - chrome_options: this takes an instance of ChromeOptions
        """
        if chrome_options is None:
            options = Options()
        else:
            options = chrome_options

        if desired_capabilities is not None:
          desired_capabilities.update(options.to_capabilities())
        else:
          desired_capabilities = options.to_capabilities()

        self.service = Service(executable_path, port=port,
            service_args=service_args, log_path=service_log_path)
        self.service.start()

        try:
            RemoteWebDriver.__init__(self,
                command_executor=self.service.service_url,
                desired_capabilities=desired_capabilities,
                keep_alive=True)
        except:
            self.quit()
            raise 
        self._is_remote = False

    def quit(self):
        """
        Closes the browser and shuts down the ChromeDriver executable
        that is started when starting the ChromeDriver
        """
        try:
            RemoteWebDriver.quit(self)
        except:
            # We don't care about the message because something probably has gone wrong
            pass
        finally:
            self.service.stop()
