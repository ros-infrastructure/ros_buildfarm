@[if project_authorization_xml is not None]@
    <hudson.security.AuthorizationMatrixProperty>
@[  for line in project_authorization_xml.splitlines()]@
      @line
@[  end for]@
    </hudson.security.AuthorizationMatrixProperty>
@[end if]@
