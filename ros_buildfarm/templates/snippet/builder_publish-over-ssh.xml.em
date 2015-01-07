    <jenkins.plugins.publish__over__ssh.BapSshBuilderPlugin plugin="publish-over-ssh@@1.12">
      <delegate>
        <consolePrefix>SSH: </consolePrefix>
        <delegate>
          <publishers>
            <jenkins.plugins.publish__over__ssh.BapSshPublisher>
              <configName>@config_name</configName>
              <verbose>false</verbose>
              <transfers>
                <jenkins.plugins.publish__over__ssh.BapSshTransfer>
                  <remoteDirectory>@remote_directory</remoteDirectory>
                  <sourceFiles>@(' '.join(source_files))</sourceFiles>
                  <excludes/>
                  <removePrefix>@remove_prefix</removePrefix>
                  <remoteDirectorySDF>false</remoteDirectorySDF>
                  <flatten>false</flatten>
                  <cleanRemote>false</cleanRemote>
                  <noDefaultExcludes>false</noDefaultExcludes>
                  <makeEmptyDirs>false</makeEmptyDirs>
                  <patternSeparator>[, ]+</patternSeparator>
                  <execCommand/>
                  <execTimeout>120000</execTimeout>
                  <usePty>false</usePty>
                </jenkins.plugins.publish__over__ssh.BapSshTransfer>
              </transfers>
              <useWorkspaceInPromotion>false</useWorkspaceInPromotion>
              <usePromotionTimestamp>false</usePromotionTimestamp>
              <retry class="jenkins.plugins.publish_over_ssh.BapSshRetry">
                <retries>10</retries>
                <retryDelay>5000</retryDelay>
              </retry>
            </jenkins.plugins.publish__over__ssh.BapSshPublisher>
          </publishers>
          <continueOnError>false</continueOnError>
          <failOnError>true</failOnError>
          <alwaysPublishFromMaster>false</alwaysPublishFromMaster>
          <hostConfigurationAccess class="jenkins.plugins.publish_over_ssh.BapSshPublisherPlugin" reference="../.."/>
        </delegate>
      </delegate>
    </jenkins.plugins.publish__over__ssh.BapSshBuilderPlugin>
