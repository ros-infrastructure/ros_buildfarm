    <com.cloudbees.jenkins.plugins.sshagent.SSHAgentBuildWrapper plugin="ssh-agent@@433.v9e73d67c3f74">
      <credentialIds>
@[for credential_id in credential_ids]@
        <string>@credential_id</string>
@[end for]@
      </credentialIds>
      <ignoreMissing>false</ignoreMissing>
    </com.cloudbees.jenkins.plugins.sshagent.SSHAgentBuildWrapper>
