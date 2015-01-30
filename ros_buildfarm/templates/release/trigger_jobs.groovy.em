import hudson.model.Cause.UpstreamCause
import jenkins.model.Jenkins

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

println "Triggering " + job_names.size + " jobs..."
triggered = 0
skipped = 0
for (job_name in job_names) {
    found_project = false
    for (p in Jenkins.instance.allItems) {
        if (p.name != job_name) continue
        found_project = true
        if (p.isDisabled()) {
            println "  " + job_name + " (skipped disabled project)"
            skipped += 1
            break
        }
        if (p.isBuilding()) {
            println "  " + job_name + " (skipped already building project)"
            skipped += 1
            break
        }
        if (p.isInQueue()) {
            println "  " + job_name + " (skipped already queued project)"
            skipped += 1
            break
        }
        println job_name
        p.scheduleBuild(new UpstreamCause(binding.variables["build"]))
        triggered += 1
        break
    }
    if (!found_project) {
        println "  " + job_name + " (skipped nonexisting project)"
        skipped += 1
    }
}
println "Triggered " + triggered + " jobs, skipped " + skipped + " jobs."
