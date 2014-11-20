from datetime import datetime
import difflib
import sys
from xml.etree import ElementTree

from jenkinsapi.jenkins import Jenkins

from .jenkins_credentials import get_credentials
from .templates import expand_template

JENKINS_MANAGEMENT_VIEW = 'Manage'


def connect(jenkins_url):
    print("Connecting to Jenkins '%s'" % jenkins_url)
    username, password = get_credentials(jenkins_url)
    jenkins = Jenkins(jenkins_url, username, password)
    print("Connected to Jenkins version '%s'" % jenkins.version)
    return jenkins


def configure_view(jenkins, view_name, include_regex=None):
    if view_name not in jenkins.views:
        print("Creating view '%s'" % view_name)
        view = jenkins.views.create(view_name)
    else:
        print("Ensure that view '%s' exists" % view_name)
        view = jenkins.views[view_name]
    if include_regex:
        view_config = _get_view_config(view_name, include_regex)
        try:
            view.update_config(view_config)
        except Exception:
            print("Failed to configure view '%s' with config:\n%s" %
                  (view_name, view_config), file=sys.stderr)
            raise
    return view


def _get_view_config(view_name, include_regex):
    template_name = 'generic_view.xml.em'
    now = datetime.utcnow()
    now_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    view_data = {
        'template_name': template_name,
        'now_str': now_str,

        'view_name': view_name,

        'include_regex': include_regex,
    }
    view_config = expand_template(template_name, view_data)
    return view_config


def configure_job(jenkins, job_name, job_config, view=None):
    try:
        if not jenkins.has_job(job_name):
            print("Creating job '%s'" % job_name)
            job = jenkins.create_job(job_name, job_config)
        else:
            job = jenkins.get_job(job_name)
            remote_job_config = job.get_config()
            diff = _diff_configs(remote_job_config, job_config)
            if not diff:
                print("Skipped '%s' because the config is the same" % job_name)
            else:
                print("Updating job '%s'" % job_name)
                print('   ', '<<<')
                for line in diff:
                    print('   ', line)
                print('   ', '>>>')
                job.update_config(job_config)
    except Exception:
        print("Failed to configure job '%s' with config:\n%s" %
              (job_name, job_config), file=sys.stderr)
        raise
    if view is not None:
        if job_name not in view:
            print("Adding job '%s' to view '%s'" % (job_name, view.name))
            job = view.add_job(job_name, job)
        else:
            print("Job '%s' is already in view '%s'" % (job_name, view.name))
    return job


def invoke_job(jenkins, job_name, prevent_multiple=True):
    try:
        if not jenkins.has_job(job_name):
            print("Failed to invoke job '%s' because it does not exist" %
                  job_name, file=sys.stderr)
            return False
        job = jenkins.get_job(job_name)
        if not job.is_enabled():
            print("Failed to invoke job '%s' because it is disabled" %
                  job_name, file=sys.stderr)
            return False
        if prevent_multiple and job.is_queued():
            print("Skipped to invoke job '%s' because it is already queued" %
                  job_name)
            return False
        if prevent_multiple and job.is_running():
            print("Skipped to invoke job '%s' because it is already running" %
                  job_name)
            return False
        print("Invoking job '%s'" % job_name)
        job.invoke()
    except Exception:
        print("Failed to invoke job '%s'" % job_name, file=sys.stderr)
        raise
    return True


def _diff_configs(remote_config, new_config):
    remote_root = ElementTree.fromstring(remote_config)
    new_root = ElementTree.fromstring(new_config)

    # ignore description which contains timestamp
    remote_root.find('description').text = ''
    new_root.find('description').text = ''

    if ElementTree.tostring(remote_root) == ElementTree.tostring(new_root):
        return []

    lines1 = ElementTree.tostringlist(remote_root, encoding='unicode')
    lines2 = ElementTree.tostringlist(new_root, encoding='unicode')
    return difflib.unified_diff(
        lines1, lines2, 'remote config', 'new config', n=0)
