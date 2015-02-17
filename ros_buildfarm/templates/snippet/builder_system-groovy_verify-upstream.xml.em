@(SNIPPET(
    'builder_system-groovy',
    command=
"""// VERFIY THAT NO UPSTREAM PROJECT IS BROKEN
import hudson.model.Result

println ""
println "# BEGIN SECTION: Check upstream projects"
println "Verify that no upstream project is broken:"

project = Thread.currentThread().executable.project

try {
  for (upstream in project.getUpstreamProjects()) {
    if (upstream.getNextBuildNumber() == 1) {
      println ""
      println "Aborting build because upstream project '" + upstream.name + "' has not been built yet"
      println ""
      throw new InterruptedException()
    }
    def lb = upstream.getLastBuild()
    if (!lb) {
      println ""
      println "Aborting build because upstream project '" + upstream.name + "' can't provide last build"
      println ""
      throw new InterruptedException()
    }
    def r = lb.getResult()
    if (!r) {
      println ""
      println "Aborting build because upstream project '" + upstream.name + "' build '" + lb.getNumber() + "' can't provide last result"
      println ""
      throw new InterruptedException()
    }
    if (r.isWorseOrEqualTo(Result.FAILURE)) {
      println ""
      println "Aborting build because upstream project '" + upstream.name + "' build '" + lb.getNumber() + "' has result '" + r + "'"
      println ""
      throw new InterruptedException()
    }
    println "- upstream project '" + upstream.name + "' build '" + lb.getNumber() + "' has result '" + r + "'"
  }
  println "All upstream projects are (un)stable"
} finally {
  println "# END SECTION"
  println ""
}
""",
    script_file=None,
    classpath='',
))@
