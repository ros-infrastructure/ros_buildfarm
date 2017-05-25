def check_project(project, depth, verbose=true) {
  if (project.isBuilding()) {
    println "  " * depth + "- '" + project.name + "' is currently building"
    return false
  }
  if (project.isInQueue()) {
    println "  " * depth + "- '" + project.name + "' is currently queued"
    return false
  }
  if (project.getNextBuildNumber() == 1) {
    println "  " * depth + "- '" + project.name + "' has not been built yet"
    return false
  }
  def lb = project.getLastBuild()
  if (!lb) {
    println "  " * depth + "- '" + project.name + "' can't provide last build"
    return false
  }
  def r = lb.getResult()
  if (!r) {
    println "  " * depth + "- '" + project.name + "' build '" + lb.getNumber() + "' can't provide last result"
    return false
  }
  if (r.isWorseOrEqualTo(Result.FAILURE)) {
    println "  " * depth + "- '" + project.name + "' build '" + lb.getNumber() + "' has result '" + r + "'"
    return false
  }
  if (verbose) {
    println "  " * depth + "- '" + project.name + "' build '" + lb.getNumber() + "' has result '" + r + "'"
  }
  return true
}

def check_recursive_upstream_projects(project, checked_projects, depth=0, verbose=true) {
  checked_projects.add(project.name)
  for (upstream in project.getUpstreamProjects()) {
    if (checked_projects.contains(upstream.name)) {
      continue
    }
    if (!check_project(upstream, depth, verbose=verbose)) {
      return false
    }
    if (!check_recursive_upstream_projects(upstream, checked_projects, depth + 1, verbose=verbose)) {
      return false
    }
  }
  return true
}
