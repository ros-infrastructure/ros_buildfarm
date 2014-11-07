from jenkinsapi.jenkins import Jenkins

from .jenkins_credentials import get_credentials

JENKINS_MANAGEMENT_VIEW = 'Manage'


def connect(jenkins_url):
    print("Connecting to Jenkins '%s'" % jenkins_url)
    username, password = get_credentials(jenkins_url)
    jenkins = Jenkins(jenkins_url, username, password)
    print("Connected to Jenkins version '%s'" % jenkins.version)
    return jenkins


def configure_view(jenkins, view_name):
    if view_name not in jenkins.views:
        print("Creating view '%s'" % view_name)
        view = jenkins.views.create(view_name)
    else:
        print("Ensure that view '%s' exists" % view_name)
        view = jenkins.views[view_name]
    return view


def configure_job(jenkins, job_name, job_config, view=None):
    if not jenkins.has_job(job_name):
        print("Creating job '%s'" % job_name)
        job = jenkins.create_job(job_name, job_config)
    else:
        print("Updating job '%s'" % job_name)
        job = jenkins.get_job(job_name)
        job.update_config(job_config)
    print(job_config)
    if view is not None:
        if job_name not in view:
            print("Adding job '%s' to view '%s" % (job_name, view.name))
            job = view.add_job(job_name, job)
        else:
            print("Job '%s' is already in view '%s" % (job_name, view.name))
    return job
