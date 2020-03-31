<scm class="hudson.scm.SubversionSCM" plugin="subversion@@2.13.1">
  <locations>
    <hudson.scm.SubversionSCM_-ModuleLocation>
      <remote>@ESCAPE(remote)</remote>
@[if local]@
      <local>@ESCAPE(local)</local>
@[end if]@
      <depthOption>infinity</depthOption>
      <ignoreExternalsOption>false</ignoreExternalsOption>
    </hudson.scm.SubversionSCM_-ModuleLocation>
  </locations>
  <excludedRegions/>
  <includedRegions/>
  <excludedUsers/>
  <excludedRevprop/>
  <excludedCommitMessages/>
  <workspaceUpdater class="hudson.scm.subversion.UpdateUpdater"/>
  <ignoreDirPropChanges>false</ignoreDirPropChanges>
  <filterChangelog>false</filterChangelog>
</scm>
