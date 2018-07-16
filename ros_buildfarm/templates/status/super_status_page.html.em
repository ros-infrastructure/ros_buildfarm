<!DOCTYPE html>
<html>
<head>
  <title>@title - @start_time_local_str</title>
  <meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>

  <script type="text/javascript" src="js/moment.min.js"></script>
  <script type="text/javascript" src="js/zepto.min.js"></script>
  </script>
  <script type="text/javascript">
    window.META_COLUMNS = 4;
  </script>
  <script type="text/javascript" src="js/setup.js"></script>

  <link rel="stylesheet" type="text/css" href="css/status_page.css" />
  <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.1.0/css/all.css" integrity="sha384-lKuwvrZot6UHsBSfcMvOkWwlCMgc0TaWr+30HWe3a4ltaBwTZhyTEggF5tJv8tbt" crossorigin="anonymous">
  <style>
  tbody tr td span { display: inline; }
  td { vertical-align:top; }
  .distro {
    font-weight: 900;
    font-style: normal;
    font-size: 150%;
  }
  .status:before {
    font-weight: 900;
    font-family: "Font Awesome 5 Free";
    font-style: normal;
    font-size: 150%;
  }
  .status:before {
    content: "\f0a3";
  }
  .released:before {
    content: "\f14a";
    color: green;
  }
  .waiting:before {
    content: "\f055";
    color: blue;
  }
  .source:before {
    content: "\f1c9";
    color: red;
  }
  .broken:before {
    content: "\f057";
    color: red
  }
  .complicated:before {
    content: "\f1d0";
    font-family: "Font Awesome 5 Brands";
    color: red
  }
  .moreinfo {
    position: absolute;
    right: 0px;
    bottom: 0px;
    display: none;
    text-align: center;
  }
  .expand_button:before {
    content: "\f078";
  }
  .collapse_button:before {
    content: "\f077";
  }
  </style>
</head>
@{
def status_cell(status):
    if not status:
        return '<td></td>'
    css_class = ''
    if status == 'released':
        css_class = status
    elif 'waiting' in status:
        css_class = 'waiting'
    elif 'source' in status:
        css_class = 'source'
    elif 'build' in status:
        css_class = 'broken'
    elif 'complicated' in status:
        css_class = 'complicated'
    return '<td class="{} status" title="{}"></td>'.format(css_class, status)
}
<body>
  <script type="text/javascript">
    window.body_ready_with_age(moment.duration(moment() - moment("@start_time", "X")));
  </script>
  <div class="top logo search">
    <h1><img src="http://wiki.ros.org/custom/images/ros_org.png" alt="ROS.org" width="150" height="32" /></h1>
    <h2>@title</h2>
    <p>Quick filter:
      <a href="?q=" title="Show all packages">*</a>,
      <a href="?q=RELEASED">RELEASED</a>,
      <a href="?q=WAITING">WAITING</a>,
      <a href="?q=SOURCE_PROBLEM">SOURCE_PROBLEM</a>,
      <a href="?q=BROKEN">BROKEN</a>,
      <a href="?q=COMPLICATED">COMPLICATED</a>
    </p>
    <form action="?">
      <input type="text" name="q" id="q" title="A query string can contain multiple '+' separated parts which must all be satisfied. Each part can also be a RegExp (e.g. to combine two parts with 'OR': 'foo|bar'), but can't contain '+'." />
      <p id="search-count"></p>
    </form>
  </div>
  <div class="top legend">
    <ul class="squares">
      <li class="released status">Released
      <li class="waiting status">Waiting for Release
      <li class="source status">Problem with Source
      <li class="broken status">Broken
      <li class="complicated status">Complicated
    </ul>
  </div>
  <div class="top age">
    <p>This should show the age of the page...</p>
  </div>
  <table>
    <caption></caption>
    <thead>
      <tr>
        <th class="sortable"><div>Package</div></th>
        <th class="sortable"><div>Organization</div></th>
        <th class="sortable"><div>Repo</div></th>
        <th><div>Maintainers</div>
    @[for distro in distros]@
        <th><div class="distro" title="@distro">@distro[0].upper()</div>
    @[end for]@
        <th>
    </thead>
    <tbody>
    @[for org in sorted(super_status, key=lambda d: d.lower())]@
        @[for repo in sorted(super_status[org]['repos'])]@
            @[for pkg in sorted(super_status[org]['repos'][repo]['pkgs'])]@
            <tr><td class="pkg">@pkg<td>@org<td>@repo
                <td><div>@[for email, name in super_status[org]['repos'][repo]['pkgs'][pkg]['maintainers'].items() ]@
                    <a href="mailto:@email">@name.encode('ascii', 'xmlcharrefreplace')</a><br />
                    @[end for]@</div>
                @[for distro in distros]@
                @status_cell(super_status[org]['repos'][repo]['pkgs'][pkg]['status'].get(distro))
                @[end for]@
                <td style="position:relative; text-align: right">
                  <span class="expand_button status" onclick="expand(this)">
                    <span class="moreinfo">
                        @[for distro in distros]@
                        @[if distro in super_status[org]['repos'][repo]['pkgs'][pkg]['status'] ]@
                        <b>@distro</b>: @super_status[org]['repos'][repo]['pkgs'][pkg]['status'][distro] <br />
                        @[end if]@
                        @[end for]@
                    </span>
                  </span>
                </td>
            </tr>
            @[end for]@
        @[end for]@
    @[end for]@
    </tbody>

    <script type="text/javascript">
        window.tbody_ready();
    </script>
  </table>
  <script type="text/javascript">window.body_done();</script>
</body>
</html>
