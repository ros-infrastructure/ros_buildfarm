    <org.jenkinsci.plugins.credentialsbinding.impl.SecretBuildWrapper plugin="credentials-binding@@728.v902a_273b_8947">
      <bindings>
        <org.jenkinsci.plugins.credentialsbinding.impl.UsernamePasswordMultiBinding>
          <credentialsId>@(credential_id)</credentialsId>
          <usernameVariable>@(env_var_prefix)_USERNAME</usernameVariable>
          <passwordVariable>@(env_var_prefix)_PASSWORD</passwordVariable>
        </org.jenkinsci.plugins.credentialsbinding.impl.UsernamePasswordMultiBinding>
      </bindings>
    </org.jenkinsci.plugins.credentialsbinding.impl.SecretBuildWrapper>
