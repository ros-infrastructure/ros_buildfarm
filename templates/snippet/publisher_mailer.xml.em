@[if recipients]@
		<hudson.tasks.Mailer plugin="mailer@@1.11">
			<recipients>@ESCAPE(' '.join(recipients))</recipients>
			<dontNotifyEveryUnstableBuild>false</dontNotifyEveryUnstableBuild>
			<sendToIndividuals>@(send_to_individuals ? 'true' ! 'false')</sendToIndividuals>
		</hudson.tasks.Mailer>
@[end if]@
