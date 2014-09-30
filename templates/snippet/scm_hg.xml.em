	<scm class="hudson.plugins.mercurial.MercurialSCM" plugin="mercurial@@1.50">
		<source>@source</source>
		<modules/>
		<revisionType>BRANCH</revisionType>
		<revision>@branch</revision>
@[if subdir]@
		<subdir>@subdir</subdir>
@[end if]@
		<clean>false</clean>
		<credentialsId/>
		<disableChangeLog>false</disableChangeLog>
	</scm>
