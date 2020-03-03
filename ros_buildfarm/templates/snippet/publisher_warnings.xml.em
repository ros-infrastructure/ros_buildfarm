<io.jenkins.plugins.analysis.core.steps.IssuesRecorder plugin="warnings-ng@@7.3.0">
  <analysisTools>
    <io.jenkins.plugins.analysis.warnings.Cmake>
      <id></id>
      <name></name>
      <pattern></pattern>
      <reportEncoding></reportEncoding>
      <skipSymbolicLinks>false</skipSymbolicLinks>
    </io.jenkins.plugins.analysis.warnings.Cmake>
    <io.jenkins.plugins.analysis.warnings.Gcc4>
      <id></id>
      <name></name>
      <pattern></pattern>
      <reportEncoding></reportEncoding>
      <skipSymbolicLinks>false</skipSymbolicLinks>
    </io.jenkins.plugins.analysis.warnings.Gcc4>
  </analysisTools>
  <sourceCodeEncoding></sourceCodeEncoding>
  <sourceDirectory></sourceDirectory>
  <ignoreQualityGate>false</ignoreQualityGate>
  <ignoreFailedBuilds>true</ignoreFailedBuilds>
  <referenceJobName>-</referenceJobName>
  <failOnError>false</failOnError>
  <healthy>0</healthy>
  <unhealthy>0</unhealthy>
  <minimumSeverity plugin="analysis-model-api@@7.0.2">
    <name>LOW</name>
  </minimumSeverity>
  <filters>
    <io.jenkins.plugins.analysis.core.filter.ExcludeMessage>
      <pattern>^Manually-specified variables were not used by the project:$</pattern>
    </io.jenkins.plugins.analysis.core.filter.ExcludeMessage>
  </filters>
  <isEnabledForFailure>false</isEnabledForFailure>
  <isAggregatingResults>false</isAggregatingResults>
  <isBlameDisabled>false</isBlameDisabled>
  <isForensicsDisabled>false</isForensicsDisabled>
@[if unstable_threshold != '']@
  <qualityGates>
    <io.jenkins.plugins.analysis.core.util.QualityGate>
      <threshold>@unstable_threshold</threshold>
      <type>TOTAL</type>
      <status>WARNING</status>
    </io.jenkins.plugins.analysis.core.util.QualityGate>
  </qualityGates>
@[else]@
  <qualityGates/>
@[end if]@
  <trendChartType>AGGREGATION_TOOLS</trendChartType>
</io.jenkins.plugins.analysis.core.steps.IssuesRecorder>
