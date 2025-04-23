    <com.cloudbees.jenkins.plugins.sshagent.SSHAgentBuildWrapper plugin="ssh-agent@@376.v8933585c69d3">
      <credentialIds>
@[for credential_id in credential_ids]@
        <string>@credential_id</string>
@[end for]@
      </credentialIds>
      <ignoreMissing>false</ignoreMissing>
    </com.cloudbees.jenkins.plugins.sshagent.SSHAgentBuildWrapper>
