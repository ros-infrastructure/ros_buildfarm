<project>
  <actions/>
  <description/>
  <keepDependencies>false</keepDependencies>
  <properties>
    <jenkins.advancedqueue.priority.strategy.PriorityJobProperty plugin="PrioritySorter@@3.5.1">
      <useJobPriority>false</useJobPriority>
      <priority>-1</priority>
    </jenkins.advancedqueue.priority.strategy.PriorityJobProperty>
    <org.jenkinsci.plugins.requeuejob.RequeueJobProperty plugin="jobrequeue@@1.1">
      <requeueJob>false</requeueJob>
    </org.jenkinsci.plugins.requeuejob.RequeueJobProperty>
  </properties>
  <scm class="hudson.scm.NullSCM"/>
  <assignedNode>building_repository</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>@block_when_upstream_building</blockBuildWhenUpstreamBuilding>
  <triggers>
    <jenkins.triggers.ReverseBuildTrigger>
      <spec/>
      <upstreamProjects>@upstream_job_names</upstreamProjects>
      <threshold>
        <name>SUCCESS</name>
        <ordinal>0</ordinal>
        <color>BLUE</color>
        <completeBuild>true</completeBuild>
      </threshold>
    </jenkins.triggers.ReverseBuildTrigger>
  </triggers>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <hudson.tasks.Shell>
      <command>#!/bin/bash
$HOME/upload_triggers/upload_repo.bash @repo
</command>
    </hudson.tasks.Shell>
  </builders>
  <publishers/>
  <buildWrappers/>
</project>
