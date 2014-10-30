@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        '# generate key files',
        'echo "# BEGIN SECTION: Generate key files"',
    ] + script_generating_key_files + [
        'echo "# END SECTION"',
    ]),
))@
