  <scm class="hudson.plugins.git.GitSCM" plugin="git@@2.3.4">
    <configVersion>2</configVersion>
    <userRemoteConfigs>
      <hudson.plugins.git.UserRemoteConfig>
@[if refspec]@
        <refspec>@ESCAPE(refspec)</refspec>
@[end if]@
        <url>@ESCAPE(url)</url>
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
      <hudson.plugins.git.extensions.impl.CloneOption>
        <shallow>true</shallow>
        <reference/>
      </hudson.plugins.git.extensions.impl.CloneOption>
    </extensions>
  </scm>
