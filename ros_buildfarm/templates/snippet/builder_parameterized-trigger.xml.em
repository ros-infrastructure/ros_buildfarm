    <hudson.plugins.parameterizedtrigger.TriggerBuilder plugin="parameterized-trigger@@2.33">
      <configs>
        <hudson.plugins.parameterizedtrigger.BlockableBuildTriggerConfig>
@[if parameters]@
          <configs>
            <hudson.plugins.parameterizedtrigger.PredefinedBuildParameters>
              <properties>@ESCAPE(parameters)</properties>
            </hudson.plugins.parameterizedtrigger.PredefinedBuildParameters>
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
