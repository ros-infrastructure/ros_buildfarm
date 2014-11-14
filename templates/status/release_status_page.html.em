<!DOCTYPE html>
<html>
<head>
  <title>ROS @(rosdistro_name.capitalize()) - release status page - @start_time</title>
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>

  <script type="text/javascript" src="js/zepto.min.js"></script>
  <script type="text/javascript">
    window.VERSION_COLUMN = 3;
    window.META_COLUMNS = 5;
    window.repos = ['building', 'testing / shadow-fixed', 'main / ros / public'];
    window.job_url_templates = [
@[for target in targets]@
      '@jenkins_job_urls[target]',
@[end for]@
    ];
  </script>
  <script type="text/javascript" src="js/setup.js?@(resource_hashes['setup.js'])"></script>

  <link rel="stylesheet" type="text/css" href="css/status_page.css?@(resource_hashes['status_page.css'])" />
</head>
<body>
  <script type="text/javascript">window.body_ready();</script>
  <div class="top logo search">
    <h1><img src="http://wiki.ros.org/custom/images/ros_org.png" alt="ROS.org" width="150" height="32" /></h1>
    <h2>ROS @(rosdistro_name.capitalize()) Build Status</h2>
    <p>Quick filter:
      <a href="?q=" title="Show all packages">*</a>,
      <a href="?q=SYNC" title="Filter packages which are affected by a sync from testing / shadow-fixed to main / ros / public">SYNC</a>,
      <a href="?q=REGRESSION" title="Filter packages which disappear by a sync from testing / shadow-fixed to main / ros / public">REGRESSION</a>,
      <a href="?q=DIFF" title="Filter packages which are different between architectures">DIFF</a>,
      <a href="?q=BLUE">BLUE</a>,
      <a href="?q=RED">RED</a>,
      <a href="?q=ORANGE">ORANGE</a>,
      <a href="?q=YELLOW">YELLOW</a>,
      <a href="?q=GRAY">GRAY</a>
    </p>
    <form action="?">
      <input type="text" name="q" id="q" />
      <p id="search-count"></p>
    </form>
  </div>
  <div class="top legend">
    <ul class="squares">
      <li>
        <a class="w" href="@repo_urls[0]" title="building repo"></a>
        <a class="w" href="@repo_urls[1]" title="testing / shadow-fixed repo"></a>
        <a class="w" href="@repo_urls[2]" title="main / ros / public repo"></a>
        three repository types
      </li>
      <li><a class=""></a> same version</li>
      <li><a class="l"></a> lower version</li>
      <li><a class="h"></a> higher version</li>
      <li><a class="m"></a> missing</li>
      <li><a class="o"></a> obsolete</li>
      <li><a class="i"></a> intentionally missing</li>
    </ul>
  </div>
  <table>
    <caption></caption>
    <thead>
      <tr>
        <th><div>Name</div></th>
        <th><div>Repo</div></th>
        <th><div>Version</div></th>
        <th><div>Status</div></th>
        <th><div>Maintainer</div></th>
@[for target in targets]@
        <th><div>@(rosdistro_name[0].upper())@('src' if target.arch == 'source' else 'bin')@(target.os_code_name[0].upper())@('32' if target.arch == 'i386' else ('64' if target.arch == 'amd64' else ''))</div>@
@[for count in package_counts[target]]@
<span class="sum">@count</span>@
@[end for]@
</th>
@[end for]@
      </tr>
    </thead>
    <tbody>
      <script type="text/javascript">window.tbody_ready();</script>
@{
rosdistro_info_ordered_values = []
for pkg_name in sorted(rosdistro_info.keys()):
    rosdistro_info_ordered_values.append(rosdistro_info[pkg_name])
}@

@[for pkg in rosdistro_info_ordered_values]@
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
</td>@
@
@# repository name
@
<td>@
@ <div>@
@ @ @[if pkg.repository_url]@
@ @ @ <a href="@pkg.repository_url">@
@ @ @[end if]@
@ @ @ @pkg.repository_name@
@ @ @[if pkg.repository_url]@
@ @ @ </a>@
@ @ @[end if]@
@ </div>@
@{
hidden_texts = []
if not homogeneous[pkg.name]:
    hidden_texts.append('DIFF')
if True in affected_by_sync[pkg.name].values():
    hidden_texts.append('SYNC')
if True in regressions[pkg.name].values():
    hidden_texts.append('REGRESSION')
}@
@ @[if hidden_texts]@
@ @  <span class="ht">@(' '.join(hidden_texts))</span>@
@ @[end if]@
</td>@
@
@# package version
@
<td><div>@pkg.version</div></td>@
@
@# package status
@
<td><a class="@pkg.status"@((' title="%s"' % pkg.status_description) if pkg.status_description else '')/></td>@
@
@# package maintainers
@
<td>@
@ @[for m in pkg.maintainers]@
@ @ <a href="mailto:@m.email">@m.name</a>@
@ @[end for]@
</td>@
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
@ @ @[if status == 'equal']@
@ @ @ <a/>@
@ @ @[elif status in ['ignore', 'missing']]@
@ @ @ <a class="@status[0]"/>@
@ @ @[else]@
@ @ @ <a class="@status[0]">@repos_data[i][target][pkg.debian_name]</a>@
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
