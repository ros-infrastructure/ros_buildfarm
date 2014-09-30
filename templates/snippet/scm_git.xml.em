	<scm class="hudson.plugins.git.GitSCM" plugin="git@@2.2.6">
		<configVersion>2</configVersion>
		<userRemoteConfigs>
			<hudson.plugins.git.UserRemoteConfig>
				<url>@url</url>
			</hudson.plugins.git.UserRemoteConfig>
		</userRemoteConfigs>
		<branches>
			<hudson.plugins.git.BranchSpec>
				<name>@refspec</name>
			</hudson.plugins.git.BranchSpec>
		</branches>
		<doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
		<submoduleCfg class="list"/>
		<extensions>
@[if relative_target_dir]@
			<hudson.plugins.git.extensions.impl.RelativeTargetDirectory>
				<relativeTargetDir>@relative_target_dir</relativeTargetDir>
			</hudson.plugins.git.extensions.impl.RelativeTargetDirectory>
@[end if]@
		</extensions>
	</scm>
