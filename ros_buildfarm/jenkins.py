from __future__ import print_function

from ast import literal_eval
import copy
import difflib
import sys
try:
    from urllib.request import urlopen
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen
    from urllib2 import HTTPError
from xml.etree import ElementTree

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.requester import Requester
from jenkinsapi.views import Views

from .jenkins_credentials import get_credentials
from .templates import expand_template

JENKINS_MANAGEMENT_VIEW = 'Manage'


class CrumbRequester(Requester):

    """Adapter for Requester inserting the crumb in every request."""

    def __init__(self, *args, **kwargs):
        super(CrumbRequester, self).__init__(*args, **kwargs)
        self._baseurl = kwargs['baseurl']
        self._last_crumb_data = None

    def post_url(self, *args, **kwargs):
        if self._last_crumb_data:
            # first try request with previous crumb if available
            response = self._post_url_with_crumb(
                self._last_crumb_data, *args, **kwargs)
            # code 403 might indicate that the crumb is not valid anymore
            if response.status_code != 403:
                return response

        # fetch new crumb (if server has crumbs enabled)
        if self._last_crumb_data is not False:
            self._last_crumb_data = self._get_crumb_data()
        return self._post_url_with_crumb(
            self._last_crumb_data, *args, **kwargs)

    def _get_crumb_data(self):
        response = self.get_url(self._baseurl + '/crumbIssuer/api/python')
        if response.status_code in [404]:
            print('The Jenkins master does not require a crumb')
            return False
        if response.status_code not in [200]:
            raise RuntimeError('Failed to fetch crumb: %s' % response.text)
        crumb_issuer_response = literal_eval(response.text)
        crumb_request_field = crumb_issuer_response['crumbRequestField']
        crumb = crumb_issuer_response['crumb']
        print('Fetched crumb: %s' % crumb)
        return {crumb_request_field: crumb}

    def _post_url_with_crumb(self, crumb_data, *args, **kwargs):
        if crumb_data:
            if len(args) >= 5:
                headers = args[4]
            else:
                headers = kwargs.setdefault('headers', {})
            headers.update(crumb_data)
        return super(CrumbRequester, self).post_url(*args, **kwargs)


class JenkinsProxy(Jenkins):

    """Proxy for Jenkins instance caching data for performance reasons."""

    def __init__(self, *args, **kwargs):
        requester_kwargs = copy.copy(kwargs)
        requester_kwargs['baseurl'] = args[0]
        kwargs['requester'] = CrumbRequester(**requester_kwargs)
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
    jenkins = JenkinsProxy(jenkins_url, username=username, password=password)
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
    create_view = view_name not in jenkins.views
    if create_view:
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
        if not create_view:
            print('   ', '<<<')
            for line in diff:
                print('   ', line.rstrip('\n'))
            print('   ', '>>>')
        try:
            response_text = view.update_config(view_config)
        except Exception:
            print("Failed to configure view '%s' with config:\n%s" %
                  (view_name, view_config), file=sys.stderr)
            raise
        if response_text:
            raise RuntimeError(
                "Failed to configure view '%s':\n%s" %
                (view_name, response_text))
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
    response_text = None
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
                response_text = job.update_config(job_config)
                if response_text:
                    print('Failed to update job config:\n%s' % response_text)
                    raise RuntimeError()
    except Exception:
        print("Failed to configure job '%s' with config:\n%s" %
              (job_name, job_config), file=sys.stderr)
        raise
    if response_text:
        raise RuntimeError(
            "Failed to configure job '%s':\n%s" % (job_name, response_text))
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
