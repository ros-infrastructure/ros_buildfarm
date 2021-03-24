@(SNIPPET(
    'credentials_binding',
    bindings=[
        {
            'id': credential_id,
            'type': 'user-pass',
            'user_var': 'PULP_USERNAME',
            'pass_var': 'PULP_PASSWORD',
        },
        {
            'id': dest_credential_id,
            'type': 'string',
            'var': 'PULP_BASE_URL',
        },
    ],
))@
