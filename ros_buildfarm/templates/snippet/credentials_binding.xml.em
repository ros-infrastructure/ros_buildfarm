    <org.jenkinsci.plugins.credentialsbinding.impl.SecretBuildWrapper plugin="credentials-binding@@1.24">
      <bindings>
@[for binding in bindings]@
@[if binding['type'] == 'user-pass']@
        <org.jenkinsci.plugins.credentialsbinding.impl.UsernamePasswordMultiBinding>
          <credentialsId>@(binding['id'])</credentialsId>
          <usernameVariable>@(binding['user_var'])</usernameVariable>
          <passwordVariable>@(binding['pass_var'])</passwordVariable>
        </org.jenkinsci.plugins.credentialsbinding.impl.UsernamePasswordMultiBinding>
@[elif binding['type'] == 'string']@
        <org.jenkinsci.plugins.credentialsbinding.impl.StringBinding>
          <credentialsId>@(binding['id'])</credentialsId>
          <variable>@(binding['var'])</variable>
        </org.jenkinsci.plugins.credentialsbinding.impl.StringBinding>
@[else]@
@{assert False, "Unsupported binding type '%s'" % binding['type']}@
@[end if]@
@[end for]@
      </bindings>
    </org.jenkinsci.plugins.credentialsbinding.impl.SecretBuildWrapper>
