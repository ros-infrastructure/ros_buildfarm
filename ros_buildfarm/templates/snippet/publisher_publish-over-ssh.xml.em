    <jenkins.plugins.publish__over__ssh.BapSshPublisherPlugin plugin="publish-over-ssh@@1.20.1">
      <consolePrefix>SSH: </consolePrefix>
      <delegate plugin="publish-over@@0.22">
        <publishers>
          <jenkins.plugins.publish__over__ssh.BapSshPublisher plugin="publish-over-ssh@@1.20.1">
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
                <useAgentForwarding>false</useAgentForwarding>
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
    </jenkins.plugins.publish__over__ssh.BapSshPublisherPlugin>
