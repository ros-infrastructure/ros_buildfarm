<hudson.model.ListView>
  <name>@view_name</name>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
  <filterExecutors>false</filterExecutors>
  <filterQueue>@('true' if filter_queue else 'false')</filterQueue>
  <properties class="hudson.model.View$PropertyList"/>
  <jobNames>
    <comparator class="hudson.util.CaseInsensitiveComparator"/>
  </jobNames>
  <jobFilters/>
  <columns>
    <hudson.views.StatusColumn/>
    <hudson.views.WeatherColumn/>
    <hudson.views.JobColumn/>
    <hudson.views.LastSuccessColumn/>
    <hudson.views.LastFailureColumn/>
    <hudson.views.LastDurationColumn/>
    <hudson.views.BuildButtonColumn/>
  </columns>
@[if include_regex]@
  <includeRegex>@include_regex</includeRegex>
@[end if]@
  <recurse>false</recurse>
</hudson.model.ListView>
