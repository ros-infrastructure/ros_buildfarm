  <scm class="hudson.plugins.git.GitSCM" plugin="git@@4.3.0">
    <configVersion>2</configVersion>
    <userRemoteConfigs>
      <hudson.plugins.git.UserRemoteConfig>
@[if refspec]@
        <refspec>@ESCAPE(refspec)</refspec>
@[end if]@
        <url>@ESCAPE(url)</url>
@[if vars().get('git_ssh_credential_id')]@
        <credentialsId>@git_ssh_credential_id</credentialsId>
@[end if]@
      </hudson.plugins.git.UserRemoteConfig>
    </userRemoteConfigs>
    <branches>
      <hudson.plugins.git.BranchSpec>
        <name>@ESCAPE(branch_name)</name>
      </hudson.plugins.git.BranchSpec>
    </branches>
    <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
    <submoduleCfg class="list"/>
    <extensions>
@[if relative_target_dir]@
      <hudson.plugins.git.extensions.impl.RelativeTargetDirectory>
        <relativeTargetDir>@ESCAPE(relative_target_dir)</relativeTargetDir>
      </hudson.plugins.git.extensions.impl.RelativeTargetDirectory>
@[end if]@
@[if not vars().get('merge_branch')]@
      <hudson.plugins.git.extensions.impl.CloneOption>
        <shallow>true</shallow>
        <noTags>false</noTags>
        <reference/>
        <depth>0</depth>
        <honorRefspec>false</honorRefspec>
      </hudson.plugins.git.extensions.impl.CloneOption>
@[else]@
      <hudson.plugins.git.extensions.impl.PreBuildMerge>
        <options>
          <mergeRemote>origin</mergeRemote>
          <mergeTarget>@merge_branch</mergeTarget>
          <mergeStrategy>default</mergeStrategy>
          <fastForwardMode>FF</fastForwardMode>
        </options>
      </hudson.plugins.git.extensions.impl.PreBuildMerge>
@[end if]@
      <hudson.plugins.git.extensions.impl.SubmoduleOption>
        <disableSubmodules>false</disableSubmodules>
        <recursiveSubmodules>true</recursiveSubmodules>
        <trackingSubmodules>false</trackingSubmodules>
        <reference></reference>
        <parentCredentials>false</parentCredentials>
        <shallow>false</shallow>
      </hudson.plugins.git.extensions.impl.SubmoduleOption>
    </extensions>
  </scm>
