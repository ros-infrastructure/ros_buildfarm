    <hudson.plugins.parameterizedtrigger.TriggerBuilder plugin="parameterized-trigger@@2.35.2">
      <configs>
        <hudson.plugins.parameterizedtrigger.BlockableBuildTriggerConfig>
@[if parameters]@
          <configs>
            <hudson.plugins.parameterizedtrigger.PredefinedBuildParameters>
              <properties>@ESCAPE(parameters)</properties>
              <textParamValueOnNewLine>false</textParamValueOnNewLine>
            </hudson.plugins.parameterizedtrigger.PredefinedBuildParameters>
@[if parameter_files]@
            <hudson.plugins.parameterizedtrigger.FileBuildParameters>
              <propertiesFile>@(','.join(ESCAPE(parameter_files)))</propertiesFile>
              <failTriggerOnMissing>@(vars().get('missing_parameter_files_skip', False) ? 'true' : 'false')</failTriggerOnMissing>
              <textParamValueOnNewLine>false</textParamValueOnNewLine>
              <useMatrixChild>false</useMatrixChild>
              <onlyExactRuns>false</onlyExactRuns>
            </hudson.plugins.parameterizedtrigger.FileBuildParameters>
@[end if]@
          </configs>
@[else]@
          <configs class="empty-list"/>
@[end if]@
          <projects>@project</projects>
          <condition>ALWAYS</condition>
          <triggerWithNoParameters>false</triggerWithNoParameters>
          <triggerFromChildProjects>false</triggerFromChildProjects>
          <block>
@[if not continue_on_failure]@
            <buildStepFailureThreshold>
              <name>FAILURE</name>
              <ordinal>2</ordinal>
              <color>RED</color>
              <completeBuild>true</completeBuild>
            </buildStepFailureThreshold>
@[end if]@
            <unstableThreshold>
              <name>UNSTABLE</name>
              <ordinal>1</ordinal>
              <color>YELLOW</color>
              <completeBuild>true</completeBuild>
            </unstableThreshold>
@[if not continue_on_failure]@
            <failureThreshold>
              <name>FAILURE</name>
              <ordinal>2</ordinal>
              <color>RED</color>
              <completeBuild>true</completeBuild>
            </failureThreshold>
@[end if]@
          </block>
          <buildAllNodesWithLabel>false</buildAllNodesWithLabel>
        </hudson.plugins.parameterizedtrigger.BlockableBuildTriggerConfig>
      </configs>
    </hudson.plugins.parameterizedtrigger.TriggerBuilder>
