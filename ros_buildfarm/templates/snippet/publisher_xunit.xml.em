@{
# for backward compatibility only
if 'types' not in vars() and 'pattern' in vars():
    types = [('GoogleTestType', pattern)]
}@
    <xunit plugin="xunit@@2.3.1">
      <types>
@[for type_tag, pattern in types]@
@{assert type_tag in ('GoogleTestType', 'JUnitType'), 'Unsupported test type tag: ' + type_tag}@
        <@(type_tag)>
          <pattern>@ESCAPE(pattern)</pattern>
          <skipNoTestFiles>true</skipNoTestFiles>
          <failIfNotNew>true</failIfNotNew>
          <deleteOutputFiles>true</deleteOutputFiles>
          <stopProcessingIfError>true</stopProcessingIfError>
        </@(type_tag)>
@[end for]@
      </types>
      <thresholds>
        <org.jenkinsci.plugins.xunit.threshold.FailedThreshold>
          <unstableThreshold>0</unstableThreshold>
          <unstableNewThreshold/>
          <failureThreshold/>
          <failureNewThreshold/>
        </org.jenkinsci.plugins.xunit.threshold.FailedThreshold>
        <org.jenkinsci.plugins.xunit.threshold.SkippedThreshold>
          <unstableThreshold/>
          <unstableNewThreshold/>
          <failureThreshold/>
          <failureNewThreshold/>
        </org.jenkinsci.plugins.xunit.threshold.SkippedThreshold>
      </thresholds>
      <thresholdMode>1</thresholdMode>
      <extraConfiguration>
        <testTimeMargin>3000</testTimeMargin>
      </extraConfiguration>
    </xunit>
