@[if recipients or dynamic_recipients]@
    <hudson.tasks.Mailer plugin="mailer@@1.11">
      <recipients>@ESCAPE(' '.join(sorted(recipients)))@ESCAPE(('\t' + ' '.join(sorted(dynamic_recipients))) if dynamic_recipients else '')</recipients>
      <dontNotifyEveryUnstableBuild>false</dontNotifyEveryUnstableBuild>
      <sendToIndividuals>@(send_to_individuals ? 'true' ! 'false')</sendToIndividuals>
    </hudson.tasks.Mailer>
@[end if]@
