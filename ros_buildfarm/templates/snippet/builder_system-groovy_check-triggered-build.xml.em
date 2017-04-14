@(SNIPPET(
    'builder_system-groovy',
    command=
"""// CHECK IF TRIGGERED BUILD HAS FAILED
// only abort if the last two builds haven't been aborted too
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
      println "Checking status of previous build..."
      pb = build.getPreviousBuild()
      if (pb) {
        if (pb.getResult() == Result.ABORTED) {
          println "- previous build was aborted"
          println ""
          println "Checking status of second previous build..."
          // check if second previous build was already aborted to avoid infinite loop
          ppb = pb.getPreviousBuild()
          if (ppb) {
            if (ppb.getResult() == Result.ABORTED) {
              println "- second previous build was aborted too"
              println ""
              println "Instead of aborting fail this build to send out notification emails"
              println ""
              build.setResult(Result.FAILURE)
              return
            }
          }
        }
      }
      println ""
      println "Aborting build, will be rescheduled automatically..."
      println ""
      // abort this build
      throw new InterruptedException()
    }
  }
  println "Pattern not found in build log, continuing..."
} finally {
  println "# END SECTION"
}
""",
    script_file=None,
))@
