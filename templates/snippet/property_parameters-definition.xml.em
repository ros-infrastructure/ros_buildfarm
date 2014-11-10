		<hudson.model.ParametersDefinitionProperty>
			<parameterDefinitions>
@[for parameter in parameters]@
@[if parameter['type'] == 'string']@
				<hudson.model.StringParameterDefinition>
					<name>@parameter['name']</name>
					<description>@parameter['description']</description>
					<defaultValue>@parameter['default_value']</defaultValue>
				</hudson.model.StringParameterDefinition>
@[else]@
@{assert False, "Unsupported parameter type '%s'" % parameter['type']}@
@[end if]@
@[end for]@
			</parameterDefinitions>
		</hudson.model.ParametersDefinitionProperty>
