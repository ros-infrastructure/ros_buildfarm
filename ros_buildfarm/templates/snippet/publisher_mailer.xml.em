@[if recipients or dynamic_recipients or send_to_individuals]@
    <hudson.tasks.Mailer plugin="mailer@@489.vd4b_25144138f">
      <recipients>@ESCAPE(' '.join(sorted(recipients)))@ESCAPE(('\t' + ' '.join(sorted(dynamic_recipients))) if dynamic_recipients else '')</recipients>
      <dontNotifyEveryUnstableBuild>false</dontNotifyEveryUnstableBuild>
      <sendToIndividuals>@(send_to_individuals ? 'true' ! 'false')</sendToIndividuals>
    </hudson.tasks.Mailer>
@[end if]@
