@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: cpu info"',
        'lscpu',
        'echo "# END SECTION"',
        'echo "# BEGIN SECTION: docker version"',
        'docker version',
        'echo "# END SECTION"',
        'echo "# BEGIN SECTION: docker info"',
        'docker info',
        'echo "# END SECTION"',
        'echo "# BEGIN SECTION: glxinfo"',
        'DISPLAY=:0 glxinfo',
        'echo "# END SECTION"',
    ]),
))@
