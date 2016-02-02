@(SNIPPET(
    'builder_system-groovy',
    command=
"""// VERFIY THAT NO RECURSIVE UPSTREAM PROJECT IS IN PROGRESS OR BROKEN
import hudson.model.Result

println ""
println "# BEGIN SECTION: Check upstream projects"
println "Verify that no recursive upstream project is broken:"

def check_project(project, depth) {
  if (project.isBuilding()) {
    println ""
    println "  " * depth + "- '" + project.name + "' is currently building"
    println "  " * depth + "-> aborting build"
    println ""
    return false
  }
  if (project.isInQueue()) {
    println ""
    println "  " * depth + "- '" + project.name + "' is currently queued"
    println "  " * depth + "-> aborting build"
    println ""
    return false
  }
  if (project.getNextBuildNumber() == 1) {
    println ""
    println "  " * depth + "- '" + project.name + "' has not been built yet"
    println "  " * depth + "-> aborting build"
    println ""
    return false
  }
  def lb = project.getLastBuild()
  if (!lb) {
    println ""
    println "  " * depth + "- '" + project.name + "' can't provide last build"
    println "  " * depth + "-> aborting build"
    println ""
    return false
  }
  def r = lb.getResult()
  if (!r) {
    println ""
    println "  " * depth + "- '" + project.name + "' build '" + lb.getNumber() + "' can't provide last result"
    println "  " * depth + "-> aborting build"
    println ""
    return false
  }
  if (r.isWorseOrEqualTo(Result.FAILURE)) {
    println ""
    println "  " * depth + "- '" + project.name + "' build '" + lb.getNumber() + "' has result '" + r + "'"
    println "  " * depth + "-> aborting build"
    println ""
    return false
  }
  println "  " * depth + "- '" + project.name + "' build '" + lb.getNumber() + "' has result '" + r + "'"
  return true
}

def check_recursive_upstream_projects(project, checked_projects, depth=0) {
  checked_projects.add(project.name)
  for (upstream in project.getUpstreamProjects()) {
    if (checked_projects.contains(upstream.name)) {
      continue
    }
    success = check_project(upstream, depth)
    if (!success) {
      // abort this build
      throw new InterruptedException()
    }
    check_recursive_upstream_projects(upstream, checked_projects, depth + 1)
  }
}

try {
  project = Thread.currentThread().executable.project
  check_recursive_upstream_projects(project, [])
  println "All recursive upstream projects are (un)stable"
} finally {
  println "# END SECTION"
  println ""
}
""",
    script_file=None,
    classpath='',
))@
