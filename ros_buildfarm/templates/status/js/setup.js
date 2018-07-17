var QUERY_TRANSFORMS = {
  'BLUE': 'class="l"',
  'ORANGE': 'class="h"',
  'RED': '<a class="m"></a>',
  'YELLOW': 'class="o"',
  'GRAY': '<a class="i"></a>',
  'RED1': '<td><a class="m"></a>',
  'RED2': '</a><a class="m"></a><a',
  'RED3': '<a class="m"></a></td>',
  'ORPHANED' : '<span class="unmaintained"|<span class="end-of-life"'
};

window.body_ready = function() {
  var url_parts = window.location.href.split('?');
  if (url_parts[1]) {
    var query_parts = url_parts[1].split('&');
    $.each(query_parts, function(i, query_part) {
      key_val = query_part.split('=');
      key_val[1] = decodeURIComponent(key_val[1]);
      switch(key_val[0]) {
        case 'q': window.queries = key_val[1]; break;
        case 's': window.sort = key_val[1]; break;
        case 'r': window.reverse = key_val[1]; break;
      }
    });
  }
};

window.age_threshold_green = moment.duration(30, 'minutes');
window.age_threshold_yellow = moment.duration(1, 'days');

window.body_ready_with_age = function(age) {
  // Do age stuff
  $(document).ready(function() {
    $('.age p').replaceWith("<p>Page was generated: <br/>" + age.humanize() + " ago</p>");
    if (age < window.age_threshold_green) {
      $('.age p').css('color', '#3c763d');
      $('.age').css('background-color', '#dff0d8');
      $('.age').css('border-color', '#d6e9c6');
    } else if (age < window.age_threshold_yellow) {
      $('.age p').css('color', '#8a6d3b');
      $('.age').css('background-color', '#fcf8e3');
      $('.age').css('border-color', '#faebcc');
    } else {
      $('.age p').css('color', '#a94442');
      $('.age').css('background-color', '#f2dede');
      $('.age').css('border-color', '#ebccd1');
    }
  });
  // Call normal "body_ready"
  return window.body_ready();
};

/* Counterpart to nth-child selectors—returns the number of the child that this
 * node is. eg, how many siblings preceed it. Do note that nth-child is 1-based,
 * while this function is zero based. */
function child_num(node) {
  return $.inArray(node, $(node).parent().children());
}

window.tbody_ready = function() {
  var table = $('table');

  // Populate the input box in the form.
  if (window.queries) {
    $('.search form input').val(window.queries.replace("+", " "));
  }

  // Hook up the event handler which fires when the input is changed.
  $('.search form input').on('input', function() {
    queries = $(this).val();
    window.filter_timeout && clearTimeout(window.filter_timeout);
    window.filter_timeout = setTimeout(function() {
      window.queries = queries;
      filter_table();
    }, 250);
  });

  // Disable submitting the form (eg, with an enter press).
  $('.search form').on('submit', function() { return false; });

  // Hook up click handlers to the keyword shortcuts.
  $('.search a').on('click', function(e) {
    e.preventDefault();
    var url_parts = $(this).attr('href').split('?');
    if (url_parts[1]) {
      var query_parts = url_parts[1].split('&');
      $.each(query_parts, function(i, query_part) {
        key_val = query_part.split('=');
        key_val[1] = decodeURIComponent(key_val[1]);
        if (key_val[0] == 'q') {
          window.queries = key_val[1];
        }
      });
    }
    $('.search form input').val(window.queries);
    filter_table();
  });

  // This mouseover handler wires up the tooltip and CI url in a JIT manner
  // when the mouse hovers on a version square. Critically important is that
  // there's only instance of this handler: on the tbody.
  // This is the "live" event pattern.
  $('tbody', table).on('mouseover', 'tr td:nth-child(n+' + (window.META_COLUMNS + 1) + ') a', function(e) {
    var a = $(this);
    var tr = a.closest('tr');
    var repo_num = child_num(this);
    var ver = a.text();
    if (!ver) {
      // If not included, then it's the same as the "latest", grab from that cell.
      ver = $('td:nth-child(' + window.VERSION_COLUMN + ')', tr).text();
      if (a.hasClass('m') || a.hasClass('i')) {
        // Unless this square is "missing" or "intentionally missing", in which case, it's None.
        ver = "None";
      }
    }
    a.attr('title', repos[repo_num] + ': ' + ver);
    if (repo_num === 0) {
      target_index = child_num(a.closest('td')[0]) - window.META_COLUMNS;
      if (window.job_url_templates.length > target_index) {
        var job_url = window.job_url_templates[target_index];
        var pkg_name_converted = $('td div', tr).text().split(' ')[0];
        if (!a.hasClass('i') && !a.hasClass('obs') ) {
          a.attr('href', job_url.replace('{pkg}', pkg_name_converted));
        }
      }
    }
  });

  /* CSS makes the original header in the document invisible. We create a clone of that
   * to be the "real" header, with the dimensions copied to the clone, and the clone alternatiing
   * between being position: absolute and position: fixed, depending on the scroll of the page. */
  var orig_header = $('thead', table);
  var header = orig_header.clone();
  header.addClass('floating').hide();
  $('table').prepend(header);
  // Insert spacer divs into the floating header to that it matches the
  // dimensions of the original table.
  $('th', header).each(function() {
    $(this).append($('<div class="spacer"></div>'));
  });
  $(window).on('resize', function() {
    // Resize the spacers to make the floating version match the original.
    $('th', header).each(function(i, el) {
      $('.spacer', this).css('width', $('tr th:nth-child(' + (i+1) + ')', orig_header).width());
    });
    header.show();
  });

  // This is an awkward race condition. The "better way" here would be to have the tfoot contain
  // dummy elements which lock the size of the table. Then the resize event could be triggered
  // immediately.
  setTimeout(function() {
    $(window).trigger('resize');
  }, 0);

  // When the page scrolls, check whether the header should be fixed or floating.
  var last_left = null;
  $(window).on('scroll', function() {
    if ($(window).scrollTop() > table.position().top) {
      // Fixed thead
      header.addClass('fixed');
      var left = window.scrollX;
      left = Math.max(left, 0);
      left = Math.min(left, Math.max(0, table.width() - document.documentElement.clientWidth));
      if (left != last_left) {
        header.css('left', -left);
        last_left = left;
      }
    } else {
      // Floating thead
      header.removeClass('fixed');
    }
  });

  // Hook up sort logic on click to table headers.
  $('th:nth-child(-n+' + window.META_COLUMNS + ')', header).on('click', function() {
    var sort = child_num(this) + 1;
    if (window.sort == sort) {
      window.reverse = window.reverse ? 0 : 1;
    } else {
      window.sort = sort;
      delete window.reverse;
    }
    filter_table();
  });

  /* If there is a load-time query string which will trigger an immediate
   * filter, hide the in-progress loading of the table. Deliberately do this
   * after the header cloning dingus above, so that the header dimensions are
   * correct. */
  if (window.queries || window.sort) {
    $('tbody').css('visibility', 'hidden');
    setTimeout(function() {
      $('tbody').css('visibility', 'visible');
      if (!$('tbody').data('body_done')) {
        $('tbody').hide();
      }
    }, 0);
  }
};

window.body_done = function() {
  if (window.queries || window.sort) {
    filter_table();
  } else {
    var count = $('tbody tr').length;
    $("#search-count").text("showing " + count + " of " + count + " total");
  }
  $('tbody').show();
  $('tbody').data('body_done', true);
};

function scan_rows() {
  // TODO: Potentially could make the initial load/search more responsive by having this
  // go in chunks, with timeouts in between.
  window.rows = [];
  $('table tbody tr').each(function() {
    var name_td = $('td:nth-child(' + window.META_COLUMNS + ')', this);
    var hidden_text = '';
    // Add lowercased version of name (which is the last meta column) for faster case-insensitive search.
    // Also, add a copy of the email to the hidden text for additional searching
    name_td.find('a').each(function() {
      hidden_text += this.text.toLowerCase()
      hidden_text += this['href'].replace('mailto:', ' ');
      hidden_text += ' ';
    });
    if (hidden_text.length > 0) {
      name_td.append(' <span class="ht">' + hidden_text + '</span>');
    }
    var row_info = [$(this).html()];
    for (var i = 1; i <= window.META_COLUMNS; i++) {
      var td = $("td:nth-child(" + i + ")", this);
      var sort_text = td.text();
      if (sort_text === '') sort_text = td.html();
      row_info.push(sort_text);
    }
    window.rows.push(row_info);
  });
  console.log("Total rows found: " + window.rows.length);
}

function filter_table() {
  // One time setup, to build up the array of row contents combined with sortable fields.
  if (!window.rows) { scan_rows(); }

  // If query provided, copy only the matching rows to the result set.
  // It not, just use the original. It gets mangled when sorting, but that's okay.
  var result_rows;
  if (window.queries) {
    var queries = window.queries.split("+");
    queries = $.map(queries, function(q) {
      // Disregard short terms.
      if (q.length < 3) return null;

      // Transform "magic" queries as necessary.
      return QUERY_TRANSFORMS[q] || q;
    });

    if (window.previous_queries && window.previous_queries.toString() == queries.toString() &&
        window.previous_sort == window.sort &&
        window.previous_reverse == window.reverse) {
      console.log("No change, skipping rebuilding table.");
      return;
    } else {
      window.previous_queries = queries;
      window.previous_sort = window.sort;
      window.previous_reverse = window.reverse;
    }

    if (queries.length > 0) {
      console.log("Filtering for queries:", queries);
      result_rows = $.map(window.rows, function(row) {
        for (var i = 0; i < queries.length; i++) {
          var is_known_query = false;
          for (var q in QUERY_TRANSFORMS) {
            // need to escape RegExp characters, for example |
            if (RegExp("^("+escape(QUERY_TRANSFORMS[q])+")$").test(escape(queries[i]))) {
              is_known_query = true;
              break;
            }
          }
          if (is_known_query) {
            // search in full row html
            if (! RegExp(queries[i]).test(row[0])) return null;
          } else {
            // search in plain text of each column
            match = false;
            for (var j = 1; j < row.length; j++) {
              if (row[j] && RegExp(queries[i]).test(row[j])) {
                match = true;
                break;
              }
            }
            if (!match) return null;
          }
        }
        return [row];
      });
    } else {
      console.log("No query terms, returning whole set.");
      result_rows = window.rows;
    }
  } else {
    console.log("No query, returning whole set.");
    result_rows = window.rows;
  }

  console.log("Result rows found: " + result_rows.length);
  $("#search-count").text("showing " + result_rows.length + " of " + rows.length + " total");

  if (window.sort) {
    var sort = parseInt(window.sort);
    var order = 1;
    if (window.reverse == 1) order = -1;
    // temporary store index of each row
    for (var i = 0; i < result_rows.length; ++i) {
      result_rows[i].push(i);
    }
    result_rows.sort(function(a, b) {
      var val1 = a[sort];
      var val2 = b[sort];
      
      // Convert strings to floats if appropriate
      var val1_float = parseFloat(val1);
      var val2_float = parseFloat(val2);   
      if (val1 == val1_float) val1 = val1_float;
      if (val2 == val2_float) val2 = val2_float;

      if (val1 > val2) return order;
      if (val1 < val2) return -order;

      // emulate stable sorting by considering the previous index of each row
      val1 = a[a.length - 1];
      val2 = b[b.length - 1];
      if (val1 > val2) return 1;
      if (val1 < val2) return -1;
      return 0;  // this should never be the case
    });
    // remove temporary index from each row
    for (var i = 0; i < result_rows.length; ++i) {
      result_rows[i].pop();
    }
  }

  var result_rows_plain = $.map(result_rows, function(row) { return row[0]; });

  // It's still a nasty rendering pause as the browser crunches through this. A possible
  // future optimization would be to have multiple tbody elements, chunk up the resulting
  // rows, and load them in in batches, separated by zero timeouts.
  $('table tbody').html("<tr/><tr>" + result_rows_plain.join("</tr><tr>") + "</tr>");

  if (window.history && window.history.replaceState) {
    var qs = [];
    if (window.queries) qs.push("q=" + encodeURIComponent(window.queries));
    if (window.sort) qs.push("s=" + encodeURIComponent(window.sort));
    if (window.reverse) qs.push("r=" + encodeURIComponent(window.reverse));
    var url = document.location.origin + document.location.pathname;
    if (qs.length > 0) {
      url += "?" + qs.join("&");
    }
    try {
      window.history.replaceState({}, document.title, url);
    } catch (e) {
      // ignore potential SecurityError when using file:// url
      console.log("Attempted to change URL to: " + url);
    }
  }
}

