    <com.cloudbees.jenkins.plugins.sshagent.SSHAgentBuildWrapper plugin="ssh-agent@@405.v67cc4f9764d0">
      <credentialIds>
@[for credential_id in credential_ids]@
        <string>@credential_id</string>
@[end for]@
      </credentialIds>
      <ignoreMissing>false</ignoreMissing>
    </com.cloudbees.jenkins.plugins.sshagent.SSHAgentBuildWrapper>
