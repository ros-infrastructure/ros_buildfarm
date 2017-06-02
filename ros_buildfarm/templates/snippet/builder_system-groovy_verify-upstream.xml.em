@{
code = FILE('snippet/check_recursive_upstream_projects.groovy')
}@
@(SNIPPET(
    'builder_system-groovy',
    command=
"""// VERFIY THAT NO RECURSIVE UPSTREAM PROJECT IS IN PROGRESS OR BROKEN
import hudson.model.Result

println ""
println "# BEGIN SECTION: Check upstream projects"
println "Verify that no recursive upstream project is broken:"
println ""

%s

try {
  project = Thread.currentThread().executable.project
  if (!check_recursive_upstream_projects(project, [])) {
    println ""
    println "  -> aborting build"
    throw new InterruptedException()
  }
  println "All recursive upstream projects are (un)stable"
} finally {
  println "# END SECTION"
  println ""
}
""" % code,
    script_file=None,
))@
