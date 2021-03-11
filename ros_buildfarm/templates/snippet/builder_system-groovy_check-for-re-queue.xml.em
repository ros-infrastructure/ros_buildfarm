@(SNIPPET(
  'builder_system-groovy',
  command=
"""// VERIFY THAT THIS PROJECT HAS NOT ALREADY BEEN RE-QUEUED

println ""
println "# BEGIN SECTION: Check for duplicate triggers"

try {
  project = Thread.currentThread().executable.project
  if (project.isInQueue()) {
    println "Another build of this project is already queued -> aborting build"
    throw new InterruptedException()
  }
} finally {
  println "# END SECTION"
  println ""
}
""",
  script_file=None,
))@
