@(SNIPPET(
  'builder_system-groovy',
  command=
"""// CHECK FOR FAILING JOBS
import hudson.model.Job

// Control the number of failures in a row to check
min_number_of_failures = 5
// Control the minimun amount of time failing
min_days_failing = 7
// rosdistro to search
rosdistro = "@ros_distro"

boolean is_failing_from_n_days(
  int min_days_failing, Job job)
{
  now = new Date()
  start_of_failing_period = now - min_days_failing

  last_success_build = job.getLastSuccessfulBuild()
  
  // if there is a last success build check when it was  
  if (last_success_build) {
    return last_success_build.getTime() < start_of_failing_period
  }
  
  // all builds are failing, check when was the first one
  return job.getFirstBuild().getTime() < start_of_failing_period       
}


// check if the N (=$number_of_builds_failing) previous builds from $job failed
boolean are_previous_builds_failing(
  int number_of_builds_failing, Job job)
{
  result = true
  last_failed_build = job.getLastFailedBuild()
  if (! last_failed_build)
    return false
  
  last_run_number = last_failed_build.getNumber()
  // loop the previous "min_number_of_failures" builds
  ((last_run_number -1)..(last_run_number - (min_number_of_failures-1))).each { num ->
    if (num <= 0) {
      result = false
      return true
    }

    // check if one of the previous builds is not FAILURE
    if (job.getBuildByNumber(num) && 
        job.getBuildByNumber(num).result != hudson.model.Result.FAILURE) {
      result = false
      return
    }
  }
  
  return result
}

initial_rosdistro = rosdistro.take(1).toUpperCase()

all_items = hudson.model.Hudson.instance.items

rosdistro_items = all_items.findAll{ job -> job.name.take(1) == initial_rosdistro }
active_jobs = rosdistro_items.findAll{job -> job.isBuildable()}
failed_jobs = active_jobs.findAll{job -> job.lastBuild && job.lastBuild.result == hudson.model.Result.FAILURE}

failed_jobs.each{ job -> 
  if (! is_failing_from_n_days(min_days_failing, job))
    return true

  if (! are_previous_builds_failing(min_number_of_failures, job))
    return true

  // Conditions checked, reporting failing job
  println hudson.model.Hudson.instance.getRootUrl() + job.getUrl()
}

return true
""",
  script_file=None,
))@
