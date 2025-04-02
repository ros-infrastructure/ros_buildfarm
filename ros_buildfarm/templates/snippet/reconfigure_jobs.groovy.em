import difflib.DiffUtils
import groovy.io.FileType
@@ThreadInterrupt
import groovy.transform.ThreadInterrupt
import hudson.AbortException
import hudson.model.View
import java.io.StringBufferInputStream
import java.io.StringWriter
import javax.xml.parsers.DocumentBuilderFactory
import javax.xml.transform.stream.StreamSource
import jenkins.model.Jenkins
import org.apache.xml.serialize.OutputFormat
import org.apache.xml.serialize.XMLSerializer
import org.xml.sax.InputSource

// job types with their prefix and a list of job names
// used to remove obsolete jobs with the same prefix which are not part of the list
job_prefixes_and_names = [:]
@[for job_type in sorted(job_prefixes_and_names.keys())]@
job_prefixes_and_names['@job_type'] = [
    'job_prefix': '@(job_prefixes_and_names[job_type][0])',
    'job_names': [],
]
@{
job_names = sorted(job_prefixes_and_names[job_type][1])
group_size = 1000
}@
// group job names in chunks of @group_size to not exceed groovy limits
@[for i in range(0, len(job_names), group_size)]@
def add_job_prefixes_and_names_@(job_type)_@(int(i / group_size) + 1)(job_names) {
@[for j in range(i, min(i + group_size, len(job_names)))]@
job_names << '@(job_names[j])'
@[end for]@
}
add_job_prefixes_and_names_@(job_type)_@(int(i / group_size) + 1)(job_prefixes_and_names['@job_type'].job_names)
@[end for]@
@[end for]@


println '# BEGIN SECTION: Groovy script - reconfigure'
dry_run = @('true' if dry_run else 'false')
dry_run_suffix = dry_run ? ' (dry run)' : ''


@[if vars().get('expected_num_views')]@
// reconfigure views
println '# BEGIN SUBSECTION: reconfigure @(expected_num_views) views'
created_views = 0
updated_views = 0
skipped_views = 0

view_config_dir = build.getWorkspace().toString() + '/reconfigure_jobs/view_configs'

def view_dir = new File(view_config_dir)
def views = view_dir.listFiles() ?: []
views.sort()

if (views.size() != @(expected_num_views)) {
    println "ERROR: Found different number of view configs than expected!! " + views.size() + " is not @(expected_num_views) as expected."
    // fail this build
    throw new AbortException("Wrong number of view configs")
}

for (it in views) {
    found_view = false
    view_name = it.getName()
    view_config = new File(it.path).getText('UTF-8')
    for (v in Jenkins.instance.views) {
        if (v.name != view_name) continue
        found_view = true
        output_stream= new ByteArrayOutputStream()
        v.writeXml(output_stream)
        reader = new StringReader(output_stream.toString())
        source = new InputSource(reader)

        diff = diff_configs(source, view_config)
        if (!diff) {
            println "Skipped view '" + view_name + "' because the config is the same" + dry_run_suffix
            skipped_views += 1
        } else {
            println "Updating view '" + view_name + "'" + dry_run_suffix
            println '    <<<'
            for (line in diff) {
                println '    ' + line
            }
            println '    >>>'

            if (!dry_run) {
                reader = new StringReader(view_config)
                source = new StreamSource(reader)
                v.updateByXml(source)
            }
            updated_views += 1
        }
        break
    }
    if (!found_view) {
        println "Creating view '" + view_name + "'" + dry_run_suffix
        if (!dry_run) {
            stream = new StringBufferInputStream(view_config)
            view = View.createViewFromXML(view_name, stream)
            Jenkins.instance.addView(view)
        }
        created_views += 1
    }
}

println 'Created ' + created_views + ' views, updated ' + updated_views + ' views, skipped ' + skipped_views + ' views' + dry_run_suffix + '.'
println '# END SUBSECTION'


@[end if]@
// reconfigure jobs
println '# BEGIN SUBSECTION: reconfigure @(expected_num_jobs) jobs'
created_jobs = 0
updated_jobs = 0
skipped_jobs = 0

job_config_dir = build.getWorkspace().toString() + '/reconfigure_jobs/job_configs'

def job_dir = new File(job_config_dir)
def jobs = job_dir.listFiles() ?: []
jobs.sort()

if (jobs.size() != @(expected_num_jobs)) {
    println "ERROR: Found different number of job configs than expected!! " + jobs.size() + " is not @(expected_num_jobs) as expected."
    // fail this build
    throw new AbortException("Wrong number of job configs")
}

def mergePullRequestData(job_name, current_file, job_config) {
    factory = DocumentBuilderFactory.newInstance()
    builder = factory.newDocumentBuilder()
    document = builder.parse(current_file)

    nodelist = document.getElementsByTagName("triggers")
    if (nodelist.getLength() != 1) return job_config
    trigger_node = nodelist.item(0)

    nodelist = trigger_node.getElementsByTagName("org.jenkinsci.plugins.ghprb.GhprbTrigger")
    if (nodelist.getLength() != 1) return job_config
    ghprb_trigger_node = nodelist.item(0)

    nodelist = ghprb_trigger_node.getElementsByTagName("pullRequests")
    if (nodelist.getLength() != 1) return job_config
    pull_requests_node = nodelist.item(0)

    builder2 = factory.newDocumentBuilder()
    stream = new StringBufferInputStream(job_config)
    document2 = builder2.parse(stream)

    nodelist = document2.getElementsByTagName("triggers")
    if (nodelist.getLength() != 1) return job_config
    trigger_node = nodelist.item(0)

    nodelist = trigger_node.getElementsByTagName("org.jenkinsci.plugins.ghprb.GhprbTrigger")
    if (nodelist.getLength() != 1) return job_config
    ghprb_trigger_node = nodelist.item(0)

    pull_requests_node = document2.importNode(pull_requests_node, true)
    ghprb_trigger_node.appendChild(pull_requests_node)

    println "Merged configuration with existing pull request job '" + job_name + "' to maintain pull request information"

    return format_xml(document2)
}

for (it in jobs) {
    job_name = it.getName()
    // remove leading serial number
    job_name = job_name[job_name.indexOf(' ') + 1..-1]
    job_config = new File(it.path).getText('UTF-8')
    p = Jenkins.instance.getItemByFullName(job_name)
    if (p) {
        job_config_file = p.getConfigFile()

        if (p.name.substring(1, 5) == 'pr__') {
            job_config = mergePullRequestData(job_name, job_config_file.getFile(), job_config)
        }

        diff = diff_configs(job_config_file.getFile(), job_config)
        if (!diff) {
            println "Skipped job '" + job_name + "' [" + (skipped_jobs + updated_jobs + created_jobs + 1) + " / " + jobs.length + "] because the config is the same" + dry_run_suffix
            skipped_jobs += 1
        } else {
            println "Updating job '" + job_name + "' [" + (skipped_jobs + updated_jobs + created_jobs + 1) + " / " + jobs.length + "]" + dry_run_suffix
            println '    <<<'
            for (line in diff) {
                println '    ' + line
            }
            println '    >>>'

            if (!dry_run) {
                reader = new StringReader(job_config)
                source = new StreamSource(reader)
                p.updateByXml(source)
            }
            updated_jobs += 1
        }
    } else {
        println "Creating job '" + job_name + "' [" + (skipped_jobs + updated_jobs + created_jobs + 1) + " / " + jobs.length + "]" + dry_run_suffix
        if (!dry_run) {
            stream = new StringBufferInputStream(job_config)
            Jenkins.instance.createProjectFromXML(job_name, stream)
        }
        created_jobs += 1
    }
}

println 'Created ' + created_jobs + ' jobs, updated ' + updated_jobs + ' jobs, skipped ' + skipped_jobs + ' jobs' + dry_run_suffix + '.'
println 'Rebuilding dependency graph...'
Jenkins.instance.rebuildDependencyGraph()
println '# END SUBSECTION'


// delete obsolete jobs
for (item in job_prefixes_and_names) {
    job_type = item.key
    job_prefix = item.value.job_prefix
    job_names = item.value.job_names
    deleted = 0
    println "# BEGIN SUBSECTION: Groovy script - delete obsolete '" + job_type + "' jobs"
    println "Searching for obsolete jobs starting with '" + job_prefix + "'"
    for (p in Jenkins.instance.allItems) {
        if (!p.name.startsWith(job_prefix)) continue
        if (p.name in job_names) continue
        println "Deleting job '" + p.name + "'" + dry_run_suffix
        if (!dry_run) {
            p.delete()
        }
        deleted += 1
    }
    println 'Deleted ' + deleted + ' jobs' + dry_run_suffix + '.'
    println '# END SUBSECTION'
}

println '# END SECTION'


def diff_configs(current_config, new_config) {

    factory = DocumentBuilderFactory.newInstance()
    builder = factory.newDocumentBuilder()

    current_doc = builder.parse(current_config)

    new_config_stream = new StringBufferInputStream(new_config)
    new_doc = builder.parse(new_config_stream)

    // ignore description which contains a timestamp
    if (current_doc.getElementsByTagName('description').getLength() > 0) {
        current_doc.getElementsByTagName('description').item(0).setTextContent('')
    }
    if (new_doc.getElementsByTagName('description').getLength() > 0) {
        new_doc.getElementsByTagName('description').item(0).setTextContent('')
    }

    current_string = format_xml(current_doc)
    new_string = format_xml(new_doc)

    if (current_string == new_string) {
        return []
    }

    current_lines = []
    current_string.eachLine { line, count ->
        current_lines << line
    }
    new_lines = []
    new_string.eachLine { line, count ->
        new_lines << line
    }

    patch = DiffUtils.diff(current_lines, new_lines)
    return DiffUtils.generateUnifiedDiff('current config', 'new config', current_lines, patch, 0)
}


def format_xml(doc) {
    format = new OutputFormat(doc)
    format.setIndenting(true)
    format.setIndent(2)
    writer = new StringWriter()
    serializer = new XMLSerializer(writer, format)
    serializer.serialize(doc)
    return writer.toString()
}
