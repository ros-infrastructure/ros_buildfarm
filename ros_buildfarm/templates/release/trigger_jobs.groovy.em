import hudson.model.Cause.UpstreamCause
import hudson.model.Result
import jenkins.model.Jenkins

not_failed_only = @('true' if not_failed_only else 'false')

job_names = []
@{
job_names = sorted(job_names)
group_size = 1000
}@
// group job names in chunks of @group_size to not exceed groovy limits
@[for i in range(0, len(job_names), group_size)]@
def add_job_names_@(int(i / group_size) + 1)(job_names) {
@[for j in range(i, min(i + group_size, len(job_names)))]@
job_names << '@(job_names[j])'
@[end for]@
}
add_job_names_@(int(i / group_size) + 1)(job_names)
@[end for]@

@(FILE('snippet/check_recursive_upstream_projects.groovy'))@

println "Triggering " + job_names.size() + " jobs..."
triggered = 0
skipped = 0
for (job_name in job_names) {
    p = Jenkins.instance.getItemByFullName(job_name)
    if (!p) {
        println "  " + job_name + " (skipped nonexisting project)"
        skipped += 1
        continue
    }
    if (p.isDisabled()) {
        println "  " + job_name + " (skipped disabled project)"
        skipped += 1
        continue
    }
    if (p.isBuilding()) {
        println "  " + job_name + " (skipped already building project)"
        skipped += 1
        continue
    }
    if (p.isInQueue()) {
        println "  " + job_name + " (skipped already queued project)"
        skipped += 1
        continue
    }
    if (not_failed_only) {
        def lb = p.getLastBuild()
        if (lb && lb.getResult() == Result.FAILURE) {
            println "  " + job_name + " (skipped failed project)"
            skipped += 1
            continue
        }
    }
    upstream_projects = []
    success = check_recursive_upstream_projects(p, upstream_projects, depth=1, verbose=false)
    if (!success) {
        println "  " + job_name + " (skipped project with disabled / failed / pending upstream job)"
        skipped += 1
        continue
    }
    any_triggered_job_is_upstream = false
    for (other_name in job_names) {
      if (other_name == job_name) {
        continue
      }
      if (other_name in upstream_projects) {
        any_triggered_job_is_upstream = true
        break
      }
    }
    if (any_triggered_job_is_upstream) {
        println "  " + job_name + " (skipped project which will be trigger by another triggered project)"
        skipped += 1
        continue
    }
    println job_name
    p.scheduleBuild(new UpstreamCause(binding.variables["build"]))
    triggered += 1
}
println "Triggered " + triggered + " jobs, skipped " + skipped + " jobs."
