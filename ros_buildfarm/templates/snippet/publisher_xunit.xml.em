@{
# for backward compatibility only
if 'types' not in vars() and 'pattern' in vars():
    types = [('GoogleTestType', pattern)]
}@
    <xunit plugin="xunit@@2.3.9">
      <types>
@[for type_tag_and_pattern in types]@
@{
# expanding these within the for statement leads to a TypeError in empy version 3.3.4 and older
type_tag, pattern = type_tag_and_pattern
assert type_tag in ('CTestType', 'GoogleTestType', 'JUnitType'), 'Unsupported test type tag: ' + type_tag
}@
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
