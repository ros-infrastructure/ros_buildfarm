import subprocess


def dpkg_parsechangelog(source_dir, fields):
    cmd = ['dpkg-parsechangelog']
    output = subprocess.check_output(cmd, cwd=source_dir)
    values = {}
    for line in output.decode().splitlines():
        for field in fields:
            prefix = '%s: ' % field
            if line.startswith(prefix):
                values[field] = line[len(prefix):]
    assert len(fields) == len(values.keys())
    return [values[field] for field in fields]
