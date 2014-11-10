@(SNIPPET(
    'builder_system-groovy',
    command=
"""
// VERFIY THAT NO UPSTREAM PROJECT IS BROKEN
import hudson.model.Result

println ""
println "Verify that no upstream project is broken"
println ""

project = Thread.currentThread().executable.project

for (upstream in project.getUpstreamProjects()) {
  if (upstream.getNextBuildNumber() == 1) {
    println "Aborting build because upstream project '" + upstream.name + "' has not been built yet"
    println ""
    throw new InterruptedException()
  }
  lb = upstream.getLastBuild()
  if (!lb) {
    println "Aborting build because upstream project '" + upstream.name + "' can't provide last build"
    println ""
    throw new InterruptedException()
  }
  r = lb.getResult()
  if (!r) {
    println "Aborting build because upstream project '" + upstream.name + "' build '" + lb.getNumber() + "' can't provide last result"
    println ""
    throw new InterruptedException()
  }
  if (r.isWorseOrEqualTo(Result.FAILURE)) {
    println "Aborting build because upstream project '" + upstream.name + "' build '" + lb.getNumber() + "' has result '" + r + "'"
    println ""
    throw new InterruptedException()
  }
  println "Upstream project '" + upstream.name + "' build '" + lb.getNumber() + "' has result '" + r + "'"
}

println "All upstream projects are (un)stable"
println ""
""",
))@
