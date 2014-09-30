		<hudson.tasks.Mailer plugin="mailer@@1.11">
			<recipients>@{
import sys
sys.stdout.write(' '.join(recipients))
			}</recipients>
			<dontNotifyEveryUnstableBuild>false</dontNotifyEveryUnstableBuild>
			<sendToIndividuals>@(send_to_individuals ? 'true' ! 'false')</sendToIndividuals>
		</hudson.tasks.Mailer>
