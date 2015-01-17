import copy
import difflib
import sys
from xml.etree import ElementTree

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.views import Views

from .jenkins_credentials import get_credentials
from .templates import expand_template

JENKINS_MANAGEMENT_VIEW = 'Manage'


class JenkinsProxy(Jenkins):

    """Proxy for Jenkins instance caching data for performance reasons."""

    def __init__(self, *args, **kwargs):
        super(JenkinsProxy, self).__init__(*args, **kwargs)
        self.__jobs = None

    @property
    def jobs(self):
        if self.__jobs is None:
            self.__jobs = super(JenkinsProxy, self).jobs
        return self.__jobs


def connect(jenkins_url):
    print("Connecting to Jenkins '%s'" % jenkins_url)
    username, password = get_credentials(jenkins_url)
    jenkins = JenkinsProxy(jenkins_url, username, password)
    print("Connected to Jenkins version '%s'" % jenkins.version)
    return jenkins


def configure_management_view(jenkins):
    return configure_view(
        jenkins, JENKINS_MANAGEMENT_VIEW, include_regex='^((?!__).)*$')


def configure_view(
        jenkins, view_name, include_regex=None,
        template_name='generic_view.xml.em'):
    view_config = get_view_config(
        template_name, view_name, include_regex=include_regex)
    view_type = _get_view_type(view_config)
    if view_name not in jenkins.views:
        print("Creating view '%s' of type '%s'" % (view_name, view_type))
        view = jenkins.views.create(view_name, view_type=view_type)
        remote_view_config = view.get_config()
    else:
        print("Ensure that view '%s' exists" % view_name)
        view = jenkins.views[view_name]
        remote_view_config = view.get_config()
        remote_view_type = _get_view_type(remote_view_config)
        if remote_view_type != view_type:
            del jenkins.views[view_name]
            print("Recreating view '%s' of type '%s'" % (view_name, view_type))
            view = jenkins.views.create(view_name, view_type=view_type)
            remote_view_config = view.get_config()

    diff = _diff_configs(remote_view_config, view_config)
    if not diff:
        print("Skipped '%s' because the config is the same" % view_name)
    else:
        print("Updating view '%s'" % view_name)
        print('   ', '<<<')
        for line in diff:
            print('   ', line.rstrip('\n'))
        print('   ', '>>>')
        try:
            view.update_config(view_config)
        except Exception:
            print("Failed to configure view '%s' with config:\n%s" %
                  (view_name, view_config), file=sys.stderr)
            raise
    return view


def get_view_config(template_name, view_name, include_regex=None, data=None):
    view_data = copy.deepcopy(data) if data is not None else {}
    view_data.update({
        'view_name': view_name,
        'include_regex': include_regex,
    })
    view_config = expand_template(template_name, view_data)
    return view_config


def _get_view_type(view_config):
    root = ElementTree.fromstring(view_config)
    root.tag
    if root.tag == 'hudson.model.ListView':
        return Views.LIST_VIEW
    if root.tag == 'hudson.plugins.view.dashboard.Dashboard':
        return Views.DASHBOARD_VIEW
    assert False, 'Unknown list type: ' + root.tag


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
                    print('   ', line.rstrip('\n'))
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


def invoke_job(jenkins, job_name, cause=None):
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
        if job.is_queued():
            print("Skipped to invoke job '%s' because it is queued" %
                  job_name, file=sys.stderr)
            return False
        if job.is_running():
            print("Skipped to invoke job '%s' because it is running" %
                  job_name, file=sys.stderr)
            return False
        print("Invoking job '%s'" % job_name)
        job.invoke(cause=cause)
    except Exception:
        print("Failed to invoke job '%s'" % job_name, file=sys.stderr)
        raise
    return True


def _diff_configs(remote_config, new_config):
    remote_root = ElementTree.fromstring(remote_config)
    new_root = ElementTree.fromstring(new_config)

    # ignore description which contains timestamp
    if remote_root.find('description') is not None:
        remote_root.find('description').text = ''
    if new_root.find('description') is not None:
        new_root.find('description').text = ''

    if ElementTree.tostring(remote_root) == ElementTree.tostring(new_root):
        return []

    xml1 = ElementTree.tostring(remote_root, encoding='unicode')
    xml2 = ElementTree.tostring(new_root, encoding='unicode')
    lines1 = xml1.splitlines()
    lines2 = xml2.splitlines()

    return difflib.unified_diff(
        lines1, lines2, 'remote config', 'new config', n=0)


def remove_jobs(jenkins, job_prefix, excluded_job_names):
    for job_name in jenkins.jobs.keys():
        if not job_name.startswith(job_prefix):
            continue
        if job_name in excluded_job_names:
            continue
        print("Deleting job '%s'" % job_name)
        jenkins.delete_job(job_name)
