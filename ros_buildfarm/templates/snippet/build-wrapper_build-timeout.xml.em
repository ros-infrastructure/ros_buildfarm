    <hudson.plugins.build__timeout.BuildTimeoutWrapper plugin="build-timeout@@1.19">
      <strategy class="hudson.plugins.build_timeout.impl.AbsoluteTimeOutStrategy">
        <timeoutMinutes>@int(timeout_minutes)</timeoutMinutes>
      </strategy>
      <operationList>
        <hudson.plugins.build__timeout.operations.WriteDescriptionOperation>
          <description>Build timed out after {0} minutes</description>
        </hudson.plugins.build__timeout.operations.WriteDescriptionOperation>
        <hudson.plugins.build__timeout.operations.FailOperation/>
      </operationList>
    </hudson.plugins.build__timeout.BuildTimeoutWrapper>
