    <hudson.plugins.groovy.SystemGroovy plugin="groovy@@2.2">
@[if command]@
      <source class="hudson.plugins.groovy.StringSystemScriptSource">
        <script plugin="script-security@@1.74">
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
