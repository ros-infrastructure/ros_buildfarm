  <scm class="hudson.plugins.mercurial.MercurialSCM" plugin="mercurial@@1260.vdfb_723cdcc81">
    <installation>Default</installation>
    <source>@ESCAPE(source)</source>
    <modules/>
    <revisionType>BRANCH</revisionType>
    <revision>@ESCAPE(branch)</revision>
@[if subdir]@
    <subdir>@ESCAPE(subdir)</subdir>
@[end if]@
    <clean>false</clean>
    <credentialsId/>
    <disableChangeLog>false</disableChangeLog>
  </scm>
