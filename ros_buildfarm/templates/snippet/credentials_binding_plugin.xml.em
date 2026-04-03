    <org.jenkinsci.plugins.credentialsbinding.impl.SecretBuildWrapper plugin="credentials-binding@@687.v619cb_15e923f">
      <bindings>
        <org.jenkinsci.plugins.credentialsbinding.impl.UsernamePasswordMultiBinding>
          <credentialsId>@(credential_id)</credentialsId>
          <usernameVariable>@(env_var_prefix)_USERNAME</usernameVariable>
          <passwordVariable>@(env_var_prefix)_PASSWORD</passwordVariable>
        </org.jenkinsci.plugins.credentialsbinding.impl.UsernamePasswordMultiBinding>
      </bindings>
    </org.jenkinsci.plugins.credentialsbinding.impl.SecretBuildWrapper>
