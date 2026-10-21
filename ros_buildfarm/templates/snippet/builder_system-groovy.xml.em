    <hudson.plugins.groovy.SystemGroovy plugin="groovy@@537.v741a_5a_f1b_581">
@[if command]@
      <source class="hudson.plugins.groovy.StringSystemScriptSource">
        <script plugin="script-security@@1402.1405.vc96e74964250">
          <script>@ESCAPE(command)</script>
          <sandbox>false</sandbox>
        </script>
      </source>
@[end if]@
@[if script_file]@
      <source class="hudson.plugins.groovy.FileSystemScriptSource">
        <scriptFile>@ESCAPE(script_file)</scriptFile>
      </source>
@[end if]@
    </hudson.plugins.groovy.SystemGroovy>
