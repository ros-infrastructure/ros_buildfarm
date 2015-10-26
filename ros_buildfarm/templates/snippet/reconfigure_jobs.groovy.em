import difflib.DiffUtils
import groovy.io.FileType
import hudson.AbortException
import java.io.StringBufferInputStream
import java.io.StringWriter
import javax.xml.parsers.DocumentBuilderFactory
import javax.xml.transform.stream.StreamSource
import jenkins.model.Jenkins
import org.apache.xml.serialize.OutputFormat
import org.apache.xml.serialize.XMLSerializer

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


def diff_configs(current_config_file, new_config) {

    factory = DocumentBuilderFactory.newInstance()
    builder = factory.newDocumentBuilder()

    current_doc = builder.parse(current_config_file.getFile())

    new_config_stream = new StringBufferInputStream(new_config)
    new_doc = builder.parse(new_config_stream)

    // ignore description which contains a timestamp
    if (current_doc.getElementsByTagName('description')) {
        current_doc.getElementsByTagName('description').item(0).setTextContent('')
    }
    if (new_doc.getElementsByTagName('description')) {
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


// reconfigure jobs
println '# BEGIN SECTION: Groovy script - reconfigure jobs'
println 'Reconfiguring @(expected_num_jobs) jobs...'
created = 0
updated = 0
skipped = 0

config_dir = build.getWorkspace().toString() + '/reconfigure_jobs/configs'

def jobs = []
def dir = new File(config_dir)
dir.eachFileRecurse (FileType.FILES) { file ->
    jobs << file
}

if (jobs.size() != @(expected_num_jobs)) {
    println "ERROR: Found different number of job configs than expected!! " + jobs.size() + " is not @(expected_num_jobs) as expected."
    throw new AbortException("Wrong number of job configs")
}

jobs.each{
    found_project = false
    job_name = it.getName()
    job_config = new File(it.path).getText('UTF-8')
    for (p in Jenkins.instance.allItems) {
        if (p.name != job_name) continue
        found_project = true
        job_config_file = p.getConfigFile()

        diff = diff_configs(job_config_file, job_config)
        if (!diff) {
            println "Skipped job '" + job_name + "' because the config is the same"
            skipped += 1
        } else {
            println "Updating job '" + job_name + "'"
            println '    <<<'
            for (line in diff) {
                println '    ' + line
            }
            println '    <<<'

            reader = new StringReader(job_config)
            source = new StreamSource(reader)
            p.updateByXml(source)
            updated += 1
        }
        break
    }
    if (!found_project) {
        println "Creating job '" + job_name + "'"
        stream = new StringBufferInputStream(job_config)
        Jenkins.instance.createProjectFromXML(job_name, stream)
        created += 1
    }
}
println 'Created ' + created + ' jobs, updated ' + updated + ' jobs, skipped ' + skipped + ' jobs.'
println '# END SECTION'

// delete obsolete jobs
for (item in job_prefixes_and_names) {
    job_type = item.key
    job_prefix = item.value.job_prefix
    job_names = item.value.job_names
    deleted = 0
    println "# BEGIN SECTION: Groovy script - delete obsolete '" + job_type + "' jobs"
    println "Searching for obsolete jobs starting with '" + job_prefix + "'"
    for (p in Jenkins.instance.allItems) {
        if (!p.name.startsWith(job_prefix)) continue
        if (p.name in job_names) continue
        println "Deleting job '" + p.name + "'"
        p.delete()
        deleted += 1
    }
    println 'Deleted ' + deleted + ' jobs.'
    println '# END SECTION'
}
