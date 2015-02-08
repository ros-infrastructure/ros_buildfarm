@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        '# generate key files',
        'echo "# BEGIN SECTION: Write PGP repository keys"',
    ] + script_generating_key_files + [
        'echo "# END SECTION"',
    ]),
))@
