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
    println "  A"
    println "  upstream.name '" + upstream.name + "'"
    println "  upstream.getNextBuildNumber() '" + upstream.getNextBuildNumber() + "'"
    if (upstream.getNextBuildNumber() == 1) {
      println "  A aborting"
      println ""
      println "Aborting build because upstream project '" + upstream.name + "' has not been built yet"
      println ""
      throw new InterruptedException()
    }
    println "  B"
    println "  upstream.getLastBuild() '" + upstream.getLastBuild() + "'"
    lb = upstream.getLastBuild()
    if (!lb) {
      println "  B aborting"
      println ""
      println "Aborting build because upstream project '" + upstream.name + "' can't provide last build"
      println ""
      throw new InterruptedException()
    }
    println "  C"
    println "  lb.getResult() '" + lb.getResult() + "'"
    r = lb.getResult()
    if (!r) {
      println "  C aborting"
      println "  lb.getNumber() '" + lb.getNumber() + "'"
      println ""
      println "Aborting build because upstream project '" + upstream.name + "' build '" + lb.getNumber() + "' can't provide last result"
      println ""
      throw new InterruptedException()
    }
    println "  D"
    if (r.isWorseOrEqualTo(Result.FAILURE)) {
      println "  D aborting"
      println "  lb.getNumber() '" + lb.getNumber() + "'"
      println "  r '" + r + "'"
      println ""
      println "Aborting build because upstream project '" + upstream.name + "' build '" + lb.getNumber() + "' has result '" + r + "'"
      println ""
      throw new InterruptedException()
    }
    println "  E"
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
