import hudson.model.Cause
import jenkins.model.Jenkins

job_names = []
@[for job_name in job_names]@
job_names << "@job_name"
@[end for]@

class CustomCause extends Cause {
    public String getShortDescription() {
        return "Triggered by " + binding.variables["build"]
    }
}

println "Triggering jobs..."
triggered = 0
skipped = 0
for (job_name in job_names) {
    for (p in Jenkins.instance.allItems) {
        if (p.name != job_name) continue
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
        p.scheduleBuild(new CustomCause())
        triggered += 1
        break
    }
}
println "Triggered " + triggered + " jobs, skipped " + skipped + " jobs."
