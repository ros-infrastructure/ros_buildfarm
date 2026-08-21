    <jenkins.model.BuildDiscarderProperty>
      <strategy class="hudson.tasks.LogRotator">
        <daysToKeep>@int(days_to_keep)</daysToKeep>
        <numToKeep>@int(num_to_keep)</numToKeep>
        <artifactDaysToKeep>@int(artifact_days_to_keep if 'artifact_days_to_keep' in vars() and artifact_days_to_keep is not None else -1)</artifactDaysToKeep>
        <artifactNumToKeep>@int(artifact_num_to_keep if 'artifact_num_to_keep' in vars() and artifact_num_to_keep is not None else -1)</artifactNumToKeep>
        <removeLastBuild>false</removeLastBuild>
      </strategy>
    </jenkins.model.BuildDiscarderProperty>
