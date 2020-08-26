    <org.jenkinsci.plugins.benchmark.core.BenchmarkPublisher plugin="benchmark@@1.0.12-SNAPSHOT">
      <inputLocation>@(';'.join(patterns))</inputLocation>
      <schemaSelection>@('customSchema' if schema else 'defaultSchema')</schemaSelection>
      <truncateStrings>true</truncateStrings>
@[if schema]@
      <altInputSchema>@(schema)</altInputSchema>
@[else]@
      <altInputSchema />
@[end if]@
      <altInputSchemaLocation />
      <altThresholds />
    </org.jenkinsci.plugins.benchmark.core.BenchmarkPublisher>
