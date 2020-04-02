<!DOCTYPE html>
<html>
<head>
  <title>@title - @start_time_local_str</title>
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>

  <script type="text/javascript" src="js/moment.min.js"></script>
  <script type="text/javascript" src="js/zepto.min.js"></script>
  <script type="text/javascript">
    window.VERSION_COLUMN = 2;
@[if has_repository_column]@
    window.VERSION_COLUMN += 1;  // repository column inserted before
@[end if]@

    window.META_COLUMNS = 2;  // name and version columns
@[if has_repository_column]@
    window.META_COLUMNS += 1;  // repository column
@[end if]@
@[if has_status_column]@
    window.META_COLUMNS += 1;  // status column
@[end if]@
@[if has_maintainer_column]@
    window.META_COLUMNS += 1;  // maintainer column
@[end if]@
    window.repos = [];
@[for repo_name in repo_names]@
      window.repos.push('@repo_name'),
@[end for]@

    window.job_url_templates = [
@[if jenkins_job_urls]@
@[for target in targets]@
      '@jenkins_job_urls[target]',
@[end for]@
@[end if]@
    ];
  </script>
  <script type="text/javascript" src="js/setup.js?@(resource_hashes['setup.js'])"></script>

  <link rel="stylesheet" type="text/css" href="css/status_page.css?@(resource_hashes['status_page.css'])" />
</head>
<body>
  <script type="text/javascript">
    window.body_ready_with_age(moment.duration(moment() - moment("@start_time", "X")));
  </script>
  <div class="top logo search">
    <h1><img src="http://wiki.ros.org/custom/images/ros_org.png" alt="ROS.org" width="150" height="32" /></h1>
    <h2>@title</h2>
    <p>Quick filter:
      <a href="?q=" title="Show all packages">*</a>,
@[if affected_by_sync]@
      <a href="?q=SYNC" title="Filter packages which are affected by a sync from testing / shadow-fixed to main / ros / public">SYNC</a>,
@[end if]@
@[if regressions]@
      <a href="?q=REGRESSION" title="Filter packages which disappear by a sync from testing / shadow-fixed to main / ros / public">REGRESSION</a>,
@[end if]@
      <a href="?q=DIFF" title="Filter packages which are different between architectures">DIFF</a>,
      <a href="?q=BLUE">BLUE</a>,
      <a href="?q=RED">RED</a>,
      <a href="?q=ORANGE">ORANGE</a>,
      <a href="?q=YELLOW">YELLOW</a>,
      <a href="?q=GRAY">GRAY</a>,
      <a href="?q=ORPHANED" title="Filter packages with unmaintained or end-of-life status">ORPHANED</a>
    </p>
    <form action="?">
      <input type="text" name="q" id="q" title="A query string can contain multiple '+' separated parts which must all be satisfied. Each part can also be a RegExp (e.g. to combine two parts with 'OR': 'foo|bar'), but can't contain '+'." />
      <p id="search-count"></p>
    </form>
  </div>
  <div class="top legend">
    <ul class="squares">
      <li>
@[for repo_name, repo_url in zip(repo_names, repo_urls)]@
        <a class="w" href="@repo_url" title="@repo_name">@(repo_name[0].upper())</a>
@[end for]@
        the repositories
      </li>
      <li><a class=""></a> same version</li>
      <li><a class="l"></a> lower version</li>
      <li><a class="h"></a> higher version</li>
      <li><a class="m"></a> missing</li>
      <li><a class="o"></a> obsolete</li>
      <li><a class="i"></a> intentionally missing</li>
    </ul>
  </div>
  <div class="top age">
    <p>This should show the age of the page...</p>
  </div>
  <table>
    <caption></caption>
    <thead>
      <tr>
        <th class="sortable"><div>Name</div></th>
@[if has_repository_column]@
        <th class="sortable"><div>Repo</div></th>
@[end if]@
        <th class="sortable"><div>Version</div></th>
@[if has_status_column]@
        <th class="sortable"><div>Status</div></th>
@[end if]@
@[if has_maintainer_column]@
        <th class="sortable"><div>Maintainer</div></th>
@[end if]@
@[for target in targets]@
        <th><div title="@(target.os_name.capitalize()) @(target.os_code_name.capitalize()) @(target.arch)">@(short_code_names[target.os_code_name])@(short_arches[target.arch])</div>@
@[for count in package_counts[target]]@
<span class="sum">@count</span>@
@[end for]@
</th>
@[end for]@
      </tr>
    </thead>
    <tbody @(' class="longversion"' if not has_repository_column and not has_status_column and not has_maintainer_column else '')>
      <script type="text/javascript">window.tbody_ready();</script>

@[for pkg in ordered_pkgs]@
<tr>@
@
@# package name and hidden keywords
@
<td>@
@ <div>@
@ @ @[if pkg.url]@
@ @ <a href="@pkg.url">@
@ @ @[end if]@
@ @ @pkg.name@
@ @ @[if pkg.url]@
@ @ </a>@
@ @ @[end if]@
@ </div>@
@{
hidden_texts = []
if not homogeneous[pkg.name]:
    hidden_texts.append('DIFF')
if affected_by_sync and True in affected_by_sync[pkg.name].values():
    hidden_texts.append('SYNC')
if regressions and True in regressions[pkg.name].values():
    hidden_texts.append('REGRESSION')
}@
@ @[if hidden_texts]@
@ @  <span class="ht">@(' '.join(hidden_texts))</span>@
@ @[end if]@
</td>@
@
@# repository name
@
@[if has_repository_column]@
<td>@
@ <div class="repo">@
@ @ @[if pkg.repository_url]@
@ @ @ <a href="@pkg.repository_url">@
@ @ @[end if]@
@ @ @ @pkg.repository_name@
@ @ @[if pkg.repository_url]@
@ @ @ </a>@
@ @ @[end if]@
@ </div>@
</td>@
@[end if]@
@
@# package version
@
<td><span>@pkg.version</span></td>@
@
@# package status
@
@[if has_status_column]@
<td><span class="@pkg.status"@((' title="%s"' % pkg.status_description) if pkg.status_description else '')/></td>@
@[end if]@
@
@# package maintainers
@
@[if has_maintainer_column]@
<td class="main">@
@ <div>@
@ @ @[for m in pkg.maintainers]@
@ @ @ <a href="mailto:@m.email">@m.name</a>@
@ @ @[end for]@
@ </div>@
</td>@
@[end if]@
@
@[for target in targets]@
@
@# a column for each target
@
<td>@
@ @[for i, status in enumerate(version_status[pkg.name][target])]@
@
@ @# a square for each repo
@
@ @ @[if status == 'equal' and repos_data[i][target][pkg.debian_name].version == pkg.version]@
@ @ @ <a/>@
@ @ @[elif status in ['ignore', 'missing']]@
@ @ @ <a class="@status[0]"/>@
@ @ @[else]@
@ @ @ <a class="@status[0]">@repos_data[i][target][pkg.debian_name].version</a>@
@ @ @[end if]@
@ @[end for]@
</td>@
@[end for]@
@
</tr>
@[end for]@

    </tbody>
  </table>
  <script type="text/javascript">window.body_done();</script>
</body>
</html>
