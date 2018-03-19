@(SNIPPET(
    'builder_system-groovy',
    command=
"""// EXTRACT WARNINGS AND MARK BUILD UNSTABLE
import java.io.BufferedReader
import java.util.regex.Matcher
import java.util.regex.Pattern

import hudson.model.Result

println "# BEGIN SECTION: Look for warnings"

try {
  // search build output for warning messages
  r = build.getLogReader()
  br = new BufferedReader(r)
  pattern = Pattern.compile(".*WARNING:.*")
  ignore_pattern = Pattern.compile(".*WARNING: (You're not using the default seccomp profile|No swap limit support).*")
  def warnings = []
  def line
  while ((line = br.readLine()) != null) {
    if (pattern.matcher(line).matches()) {
      if (ignore_pattern.matcher(line).matches()) continue
      warnings << line
    }
  }
  if (warnings.size() == 0) {
    println "No warnings found"
  } else {
    println "Found " + warnings.size() + " warnings:"
    println ""
    for (warning in warnings) {
      println "- " + warning
      println ""
    }
    if (build.getResult().isBetterThan(Result.UNSTABLE)) {
      println "Marking build as unstable"
      build.setResult(Result.UNSTABLE)
    }
  }
} finally {
  println "# END SECTION"
}
""",
    script_file=None,
))@
