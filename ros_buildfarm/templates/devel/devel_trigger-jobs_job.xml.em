<project>
  <actions/>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
@(SNIPPET(
    'log-rotator',
    days_to_keep=365,
    num_to_keep=10,
))@
  <keepDependencies>false</keepDependencies>
  <properties>
@(SNIPPET(
    'property_job-priority',
    priority=40,
))@
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.ChoiceParameterDefinition>
          <name>filter</name>
          <description/>
          <choices class="java.util.Arrays$ArrayList">
            <a class="string-array">
              <string>not_stable</string>
              <string>worse_than_unstable</string>
              <string>all</string>
              <string>stable</string>
              <string>unstable</string>
              <string>failure</string>
              <string>aborted</string>
              <string>not_built</string>
            </a>
          </choices>
        </hudson.model.ChoiceParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
@(SNIPPET(
    'property_requeue-job',
))@
@(SNIPPET(
    'property_disk-usage',
))@
  </properties>
@(SNIPPET(
    'scm_null',
))@
  <assignedNode>master</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
@(SNIPPET(
    'builder_system-groovy',
    command=
"""import java.util.regex.Matcher
import java.util.regex.Pattern
import hudson.model.AbstractProject
import hudson.model.Result

build = Thread.currentThread().executable
resolver = build.buildVariableResolver
filter = resolver.resolve("filter")
println "Filter: " + filter

pattern = Pattern.compile("%s")
for (p in hudson.model.Hudson.instance.getAllItems(AbstractProject)) {
    if (!pattern.matcher(p.name).matches()) continue
    if (p.isDisabled()) continue
    if (p.isBuilding()) continue
    if (p.isInQueue()) continue

    if (filter != "all") {
        def lb = p.lastBuild
        if (!lb) {
            // job has never been built
            if (filter != "not_built" && filter != "not_stable" && filter != "worse_than_unstable") continue
        } else {
            def r = lb.result
            def pb = lb
            while (!r) {
              pb = pb.previousBuild
              if (!pb) {
                // no finished build yet
                break
              }
              r = pb.result
            }
            if (r == Result.SUCCESS) {
                if (filter != "stable") continue
            } else if (r == Result.UNSTABLE) {
                if (filter != "unstable" && filter != "not_stable") continue
            } else if (r == Result.FAILURE) {
                if (filter != "failure" && filter != "not_stable" && filter != "worse_than_unstable") continue
            } else if (r == Result.ABORTED) {
                if (filter != "aborted" && filter != "not_stable" && filter != "worse_than_unstable") continue
            } else if (!r) {
                if (filter != "not_built" && filter != "not_stable" && filter != "worse_than_unstable") continue
            } else if (r == Result.NOT_BUILT) {
              // this should never happen for the result of a build
              assert false
            } else {
              // unknown result value
              println("Job '" + p.name + "'' has unknown result: " + r)
              assert false
            }
        }
    }
    println p.name
    p.scheduleBuild()
}
""" % project_name_pattern,
))@
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_mailer',
    recipients=recipients,
    dynamic_recipients=[],
    send_to_individuals=False,
))@
  </publishers>
  <buildWrappers>
@(SNIPPET(
    'build-wrapper_timestamper',
))@
@(SNIPPET(
    'build-wrapper_disk-check',
))@
  </buildWrappers>
</project>
