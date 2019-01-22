    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
@[for parameter in parameters]@
@[if parameter['type'] == 'boolean']@
        <hudson.model.BooleanParameterDefinition>
          <name>@parameter['name']</name>
          <description>@(parameter['description'] if 'description' in parameter and parameter['description'] is not None else '')</description>
          <defaultValue>@('true' if parameter.get('default_value', False) else 'false')</defaultValue>
        </hudson.model.BooleanParameterDefinition>
@[elif parameter['type'] == 'string']@
        <hudson.model.StringParameterDefinition>
          <name>@parameter['name']</name>
          <description>@(parameter['description'] if 'description' in parameter and parameter['description'] is not None else '')</description>
          <defaultValue>@(parameter['default_value'] if 'default_value' in parameter and parameter['default_value'] is not None else '')</defaultValue>
          <trim>false</trim>
        </hudson.model.StringParameterDefinition>
@[else]@
@{assert False, "Unsupported parameter type '%s'" % parameter['type']}@
@[end if]@
@[end for]@
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
