@(SNIPPET(
    'builder_system-groovy',
    command=
"""// CHECK IF TRIGGERED BUILD HAS FAILED
// only triggered when previous build step was successful
import java.io.BufferedReader
import java.util.regex.Matcher
import java.util.regex.Pattern

import hudson.model.Cause
import hudson.model.Result

println "# BEGIN SECTION: Check if triggered build failed"

try {
  // search build output for failed build
  r = build.getLogReader()
  br = new BufferedReader(r)
  pattern = Pattern.compile(".* completed. Result was FAILURE.*")
  def line
  while ((line = br.readLine()) != null) {
    if (pattern.matcher(line).matches()) {
      println "Aborting build since triggered build has failed"
      // check if previous build was already rescheduling to avoid infinite loop
      pr = build.getPreviousBuild().getLogReader()
      if (pr) {
        pbr = new BufferedReader(pr)
        while ((line = pbr.readLine()) != null) {
          if (pattern.matcher(line).matches()) {
            println "Skip rescheduling new build since this was already a rescheduled build"
            println ""
            build.setResult(Result.FAILURE)
            return
          }
        }
      }
      println "Immediately rescheduling new build..."
      println ""
      build.project.scheduleBuild(new Cause.UserIdCause())
      throw new InterruptedException()
    }
  }
  println "Pattern not found in build log, continuing..."
} finally {
  println "# END SECTION"
}
""",
    script_file=None,
    classpath='',
))@
