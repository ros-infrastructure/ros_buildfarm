<!DOCTYPE html>
<html>
<head>
  <title>Bloom Status Page - @start_time_local_str</title>
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>

  <script type="text/javascript" src="js/moment.min.js"></script>
  <script type="text/javascript" src="js/zepto.min.js"></script>
  <script type="text/javascript">
    window.META_COLUMNS = 5;
  </script>
  <script type="text/javascript" src="js/setup.js"></script>

  <link rel="stylesheet" type="text/css" href="css/status_page.css" />
</head>
<body>
  <script type="text/javascript">
    window.body_ready_with_age(moment.duration(moment() - moment("@start_time", "X")));
  </script>
  <div class="top logo search">
    <h1><img src="http://wiki.ros.org/custom/images/ros_org.png" alt="ROS.org" width="150" height="32" /></h1>
    <h2>Bloom Status Page</h2>
    <p>Quick filter:
      <a href="?q=" title="Show all packages">*</a>,
      <a href="?q=NO SOURCE">NO SOURCE</a>,
      <a href="?q=NO RELEASE">NO RELEASE</a>,
      <a href="?q=CHANGED">CHANGED</a>,
      <a href="?q=BLOOMED">BLOOMED</a>,
      <a href="?q=BROKEN">BROKEN</a>
    </p>
    <form action="?">
      <input type="text" name="q" id="q" title="A query string can contain multiple '+' separated parts which must all be satisfied. Each part can also be a RegExp (e.g. to combine two parts with 'OR': 'foo|bar'), but can't contain '+'." />
      <p id="search-count"></p>
    </form>
  </div>
  <div class="top age">
    <p>This should show the age of the page...</p>
  </div>
  <table>
    <caption></caption>
    <thead>
      <tr>
        <th class="sortable"><div>Name</div></th>
@[for distro in distros]@
        <th class="sortable"><div>@distro<br/>Status</div></th>
        <th><div>@distro<br/>Version</div></th>
@[end for]@
      </tr>
    </thead>
    <tbody>
      <script type="text/javascript">window.tbody_ready();</script>

@[for pkg in sorted(packages)]@
<tr><th><div>@pkg</div></th>
@[for distro in distros]@
        <td><div>@(packages[pkg].get(distro, {}).get('status', ''))</div></td>
        <td><div>@(packages[pkg].get(distro, {}).get('release', ''))</div></td>
@[end for]@
</tr>
@[end for]@

    </tbody>
  </table>
  <script type="text/javascript">window.body_done();</script>
</body>
</html>
