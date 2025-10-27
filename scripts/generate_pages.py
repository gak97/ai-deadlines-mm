import json
import html
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any
import yaml

DATA_PATH = Path('_data/conferences.yml')
INDEX_TEMPLATE_PATH = Path('templates/index.template.html')
CONF_TEMPLATE_PATH = Path('templates/conference.template.html')
INDEX_OUTPUT_PATH = Path('index.html')
CONF_OUTPUT_PATH = Path('conference/index.html')

TAG_DISPLAY = {
    'ML': 'Machine Learning',
    'CV': 'Computer Vision',
    'CG': 'Computer Graphics',
    'NLP': 'Natural Language Proc',
    'RO': 'Robotics',
    'SP': 'Speech/SigProc',
    'DM': 'Data Mining',
    'AP': 'Automated Planning',
    'KR': 'Knowledge Representation',
    'HCI': 'Human-Computer Interaction',
}

TAG_CLASS_PREFIX = {
    'ML': 'ml-conf',
    'CV': 'cv-conf',
    'CG': 'cg-conf',
    'NLP': 'nlp-conf',
    'RO': 'ro-conf',
    'SP': 'sp-conf',
    'DM': 'dm-conf',
    'AP': 'ap-conf',
    'KR': 'kr-conf',
    'HCI': 'hci-conf',
}


def load_conferences() -> List[Dict[str, Any]]:
    data = yaml.safe_load(DATA_PATH.read_text(encoding='utf-8'))
    return data


def build_conference_card(conf: Dict[str, Any], index: int) -> str:
    conf_id = conf['id']
    title = conf.get('title', '')
    year = conf.get('year')
    full_name = conf.get('full_name', '')
    url = conf.get('url', '')
    date = conf.get('date', '')
    location = conf.get('location', '')
    note = conf.get('note')
    submission_rounds = conf.get('submission_rounds') or []
    tags = conf.get('tags', [])

    classes = ['ConfItem'] + [TAG_CLASS_PREFIX.get(tag, '').strip() for tag in tags if TAG_CLASS_PREFIX.get(tag)]
    class_attr = ' '.join(filter(None, classes))

    title_text = f"{title} {year}" if year else title
    short_year = f"{year}"[-2:] if year else ''
    short_title = f"{title} '{short_year}" if short_year else title
    conf_link = f"/ai-deadlines-mm/conference?id={conf_id}"

    safe_title = html.escape(title_text)
    safe_short_title = html.escape(short_title)
    safe_full_name = html.escape(full_name)
    safe_url = html.escape(url)
    safe_date = html.escape(date)
    safe_location = html.escape(location)
    location_href = 'http://maps.google.com/?q=' + urllib.parse.quote(location) if location else '#'

    tags_html_parts = []
    for tag in tags:
        label = TAG_DISPLAY.get(tag, tag)
        tags_html_parts.append(
            f'                  <span class="conf-sub" data-sub="{html.escape(tag)}">{html.escape(label)}</span>'
        )
    tags_html = '\n'.join(tags_html_parts)

    note_html = f'                <div class="note">{html.escape(note)}</div>\n' if note else ''

    rounds_data = submission_rounds if submission_rounds else []
    if not rounds_data and conf.get('deadline'):
        rounds_data = [
            {
                'name': 'Paper Submission',
                'deadline': conf.get('deadline'),
            }
        ]

    round_items = []
    for round_index, round_info in enumerate(rounds_data):
        round_name = html.escape(round_info.get('name', f'Round {round_index + 1}'))
        round_items.append(
            (
                "                  <li class=\"deadline-round\" data-round-index=\"{idx}\">\n"
                "                    <div class=\"round-name\">{name}</div>\n"
                "                    <div class=\"round-countdown\">\n"
                "                      <span class=\"round-timer\"></span>\n"
                "                      <span class=\"round-timer-small\"></span>\n"
                "                    </div>\n"
                "                    <div class=\"round-status text-muted\"></div>\n"
                "                    <div class=\"round-deadline\">\n"
                "                      Deadline:\n"
                "                      <span class=\"round-deadline-time\"></span>\n"
                "                    </div>\n"
                "                    <div class=\"calendar round-calendar\"></div>\n"
                "                  </li>"
            ).format(idx=round_index, name=round_name)
        )

    if not round_items:
        round_items.append(
            "                  <li class=\"deadline-round no-rounds\">\n"
            "                    <div class=\"round-status text-muted\">Deadline to be announced</div>\n"
            "                  </li>"
        )

    rounds_html = '\n'.join(round_items)

    card = f"""
          <div id="{html.escape(conf_id)}" class="{class_attr}" data-order-index="{index}">
            <div class="row conf-row">
                <div class="col-6">
                  <span class="conf-title">
                      <a title="{safe_full_name} Details" href="{conf_link}">{safe_title}</a>
                  </span>
                  <span class="conf-title-small">
                      <a title="{safe_full_name} Details" href="{conf_link}">{safe_short_title}</a>
                  </span>
                  <span class="conf-title-icon">
                    <a title="Conference Website" href="{safe_url}" target="_blank"><img src="/ai-deadlines-mm/static/img/203-earth.svg" class="badge-link" alt="Link to Conference Website" /></a>
                  </span>
                </div>
                <div class="col-6">
                  <span class="timer"></span>
                  <span class="timer-small"></span>
                </div>
            </div>
            <div class="row">
              <div class="col-12 col-sm-6">
                <div class="meta">
                  <span class="conf-date">{safe_date}.</span>
                  <span class="conf-place">
                    <a href="{location_href}">{safe_location}</a>.
                  </span>
                </div>
{note_html}                <div class="conf-subjects">
{tags_html}
                </div>
              </div>
              <div class="col-12 col-sm-6">
                <div class="deadline">
                  <div class="current-round-name text-muted"></div>
                  <ul class="deadline-rounds">
{rounds_html}
                  </ul>
                </div>
              </div>
            </div>
            <div class="row">
              <div class="col-12">

              </div>
            </div>
            <hr>
          </div>"""
    return card


def build_index_script(conferences: List[Dict[str, Any]]) -> str:
    data_json = json.dumps(conferences, ensure_ascii=False)
    data_json = data_json.replace('</', '<' + '\\' + '/')
    script = f"""
    $(function() {{
        var subs = [];
var _all_subs = [];
// Get all subs
var conf_type_data = [{{"name":"Machine Learning","sub":"ML","color":"#ffd300"}},{{"name":"Computer Vision","sub":"CV","color":"#deff0a"}},{{"name":"Computer Graphics","sub":"CG","color":"#0aefff"}},{{"name":"Natural Language Proc","sub":"NLP","color":"#147df5"}},{{"name":"Robotics","sub":"RO","color":"#0aff99"}},{{"name":"Speech/SigProc","sub":"SP","color":"#580aff"}},{{"name":"Data Mining","sub":"DM","color":"#be0aff"}},{{"name":"Automated Planning","sub":"AP","color":"#a432a8"}},{{"name":"Knowledge Representation","sub":"KR","color":"#32a855"}},{{"name":"Human-Computer Interaction","sub":"HCI","color":"#a83232"}}];
var sub2name = {{}}; var name2sub = {{}};
for (var i = 0; i < conf_type_data.length; i++) {{
    _all_subs[i] = conf_type_data[i]['sub'];
    sub2name[conf_type_data[i]['sub']] = conf_type_data[i]['name'];
    name2sub[conf_type_data[i]['name']] = conf_type_data[i]['sub'];
}}
const all_subs = _all_subs;
        // Borrowed from https://github.com/moment/moment-timezone/issues/167
// Adds support for time zones 'UTC-12'..'UTC+12'
function addUtcTimeZones() {{
  for (let offset = -12; offset <= 12; offset++) {{
    const posixSign = offset <= 0 ? "+" : "-";
    const isoSign = offset >= 0 ? "+" : "-";
    const link = `Etc/GMT${{posixSign}}${{Math.abs(offset)}}|UTC${{isoSign}}${{Math.abs(offset)}}`;
    moment.tz.link(link);
  }}
}}

function update_filtering(data) {{
  var page_url = "/ai-deadlines-mm";
  store.set("gak97.github.io-subs", data.subs);

  $(".ConfItem").hide();
  for (const j in data.all_subs) {{
    const s = data.all_subs[j];
    const identifier = "." + s + "-conf";
    if (data.subs.includes(s)) {{
      $(identifier).show();
    }}
  }}

  if (subs.length == 0) {{
    window.history.pushState("", "", page_url);
  }} else {{
    window.history.pushState("", "", page_url + "/?sub=" + data.subs.join());
  }}
}}

function createCalendarFromObject(data) {{
  return createCalendar({{
    options: {{
      class: "calendar-obj",
      id: data.id,
    }},
    data: {{
      title: data.title,
      start: data.date,
      duration: 60,
    }},
  }});
}}

function getSubmissionRounds(conf) {{
  if (Array.isArray(conf.submission_rounds) && conf.submission_rounds.length > 0) {{
    return conf.submission_rounds;
  }}
  if (conf.deadline) {{
    return [{{ name: conf.round_label || 'Paper Submission', deadline: conf.deadline }}];
  }}
  return [];
}}

function ensureRoundElement(list, index) {{
  var existing = list.find('.deadline-round[data-round-index="' + index + '"]');
  if (existing.length) {{
    return existing.first();
  }}
  var item = $('<li class="deadline-round" data-round-index="' + index + '"></li>');
  item.append('<div class="round-name"></div>');
  item.append('<div class="round-countdown"><span class="round-timer"></span><span class="round-timer-small"></span></div>');
  item.append('<div class="round-status text-muted"></div>');
  item.append('<div class="round-deadline">Deadline: <span class="round-deadline-time"></span></div>');
  item.append('<div class="calendar round-calendar"></div>');
  list.append(item);
  return item;
}}
        // Multi-select handler
$("#subject-select").multiselect({{
  includeSelectAllOption: true,
  numberDisplayed: 5,
  onChange: function (option, checked, select) {{
    var csub = $(option).val();
    if (checked == true) {{
      if (subs.indexOf(csub) < 0) subs.push(csub);
    }} else {{
      var idx = subs.indexOf(csub);
      if (idx >= 0) subs.splice(idx, 1);
    }}
    update_filtering({{ subs: subs, all_subs: all_subs }});
  }},
  onSelectAll: function (options) {{
    subs = all_subs;
    update_filtering({{ subs: subs, all_subs: all_subs }});
  }},
  onDeselectAll: function (options) {{
    subs = [];
    update_filtering({{ subs: subs, all_subs: all_subs }});
  }},
  buttonText: function (options, select) {{
    if (options.length === 0) {{
      return "None selected";
    }} else {{
      var labels = [];
      options.each(function () {{
        if ($(this).attr("value") !== undefined) {{
          labels.push($(this).attr("value"));
        }} else {{
          labels.push($(this).html());
        }}
      }});
      return labels.join(", ") + "";
    }}
  }},
  buttonTitle: function (options, select) {{
    return "";
  }},
}});

        addUtcTimeZones();

        var display_timezone = 'Europe/London';

        try {{
          var local_timezone = display_timezone;
          $('.local-timezone').text(local_timezone.toString());
        }} catch (err) {{
          console.log('Error setting local timezone label', err);
        }}

        var conferenceData = {data_json};
        var upcoming = [];
        var past = [];
        var comingContainer = $("#coming_confs");
        var pastContainer = $("#past_confs");

        conferenceData.forEach(function(conf, index) {{
          var el = $('#' + conf.id);
          if (!el.length) {{
            return;
          }}
          el.attr('data-order-index', index);

          var list = el.find('.deadline-rounds');
          if (!list.length) {{
            list = $('<ul class="deadline-rounds"></ul>');
            el.find('.deadline').append(list);
          }}

          var rounds = getSubmissionRounds(conf);
          var timezone = conf.timezone || 'UTC-12';
          var now = moment();
          var summaryTimer = el.find('.conf-row .timer').first();
          var summaryTimerSmall = el.find('.conf-row .timer-small').first();
          var summaryLabel = el.find('.current-round-name');
          var upcomingRound = null;
          var latestPastRound = null;

          if (rounds.length === 0) {{
            list.empty().append('<li class="deadline-round no-rounds"><div class="round-status text-muted">Deadline to be announced</div></li>');
            summaryLabel.text('');
            summaryTimer.text('Date TBD');
            summaryTimerSmall.text('');
            el.removeClass('past');
            el.attr('data-diff', '');
            upcoming.push({{ el: el, diff: Number.POSITIVE_INFINITY, order: index, deadlineMoment: null }});
            return;
          }}

          var existingRounds = list.find('.deadline-round');
          if (existingRounds.length > rounds.length) {{
            existingRounds.slice(rounds.length).remove();
          }}
          for (var r = existingRounds.length; r < rounds.length; r++) {{
            ensureRoundElement(list, r);
          }}
          list.find('.deadline-round').each(function(i) {{
            $(this).attr('data-round-index', i);
          }});

          rounds.forEach(function(roundInfo, roundIndex) {{
            var roundName = (roundInfo && roundInfo.name) ? roundInfo.name : ('Round ' + (roundIndex + 1));
            var roundEl = list.find('.deadline-round[data-round-index="' + roundIndex + '"]');
            if (!roundEl.length) {{
              roundEl = ensureRoundElement(list, roundIndex);
            }}
            roundEl.find('.round-name').text(roundName);
            var statusEl = roundEl.find('.round-status');
            var countdownEl = roundEl.find('.round-countdown');
            var timerEl = roundEl.find('.round-timer');
            var timerSmallEl = roundEl.find('.round-timer-small');
            var deadlineSpan = roundEl.find('.round-deadline-time');
            var calendarSlot = roundEl.find('.round-calendar');
            statusEl.text('');
            deadlineSpan.text('');
            countdownEl.show();
            timerEl.show().text('');
            timerSmallEl.show().text('');
            calendarSlot.show().empty();
            roundEl.removeClass('round-past');
            roundEl.attr('data-diff', '');

            if (!roundInfo || !roundInfo.deadline) {{
              countdownEl.hide();
              statusEl.text('Deadline to be announced');
              calendarSlot.hide();
              return;
            }}

            try {{
              var confDeadline = moment.tz(roundInfo.deadline, timezone);
              if (!confDeadline.isValid()) {{
                countdownEl.hide();
                statusEl.text('Invalid deadline');
                calendarSlot.hide();
                return;
              }}
              var diff = confDeadline.diff(now, 'seconds');
              roundEl.attr('data-diff', diff);
              deadlineSpan.text(confDeadline.format('ddd MMM DD YYYY HH:mm:ss [GMT]Z'));

              var calendarNode = createCalendarFromObject({{
                id: conf.id + '-round-' + roundIndex,
                title: conf.title + ' ' + (conf.year || '') + ' ' + roundName + ' deadline',
                date: confDeadline.toDate(),
              }});
              calendarSlot.show().empty().append(calendarNode);

              if (diff > 0) {{
                countdownEl.show();
                timerEl.countdown(confDeadline.toDate(), function(event) {{
                  $(this).html(event.strftime('%D days %H:%M:%S'));
                }});
                timerSmallEl.countdown(confDeadline.toDate(), function(event) {{
                  $(this).html(event.strftime('%D days %H:%M:%S'));
                }});
                statusEl.text('');
                roundEl.removeClass('round-past');
                if (!upcomingRound || diff < upcomingRound.diff) {{
                  upcomingRound = {{ diff: diff, moment: confDeadline, name: roundName }};
                }}
              }} else {{
                countdownEl.hide();
                timerEl.text('');
                timerSmallEl.text('');
                statusEl.text('Deadline passed');
                roundEl.addClass('round-past');
                if (!latestPastRound || diff > latestPastRound.diff) {{
                  latestPastRound = {{ diff: diff, moment: confDeadline, name: roundName }};
                }}
              }}
            }} catch (err) {{
              console.log('Error processing conference round for', conf.id, roundName, err);
              countdownEl.hide();
              statusEl.text('Deadline unavailable');
              calendarSlot.hide();
            }}
          }});

          summaryTimer.text('');
          summaryTimerSmall.text('');

          if (upcomingRound) {{
            summaryLabel.text('Next: ' + upcomingRound.name);
            summaryTimer.countdown(upcomingRound.moment.toDate(), function(event) {{
              $(this).html(event.strftime('%D days %H:%M:%S'));
            }});
            summaryTimerSmall.countdown(upcomingRound.moment.toDate(), function(event) {{
              $(this).html(event.strftime('%D days %H:%M:%S'));
            }});
            el.attr('data-diff', upcomingRound.diff);
            el.removeClass('past');
            upcoming.push({{ el: el, diff: upcomingRound.diff, order: index, deadlineMoment: upcomingRound.moment }});
          }} else {{
            var passedText = latestPastRound ? 'Deadline passed' : 'Date TBD';
            summaryLabel.text(latestPastRound ? 'Last: ' + latestPastRound.name : '');
            summaryTimer.text(passedText);
            summaryTimerSmall.text(passedText);
            var diffValue = latestPastRound ? latestPastRound.diff : '';
            el.attr('data-diff', diffValue);
            el.addClass('past');
            past.push({{ el: el, diff: diffValue, order: index, deadlineMoment: latestPastRound ? latestPastRound.moment : null }});
          }}
        }});

        comingContainer.empty();
        upcoming.sort(function(a, b) {{
          return a.order - b.order;
        }});
        upcoming.forEach(function(item) {{
          comingContainer.append(item.el);
        }});

        function renderPast(items) {{
          if (items.length > 0) {{
            $('#past-deadlines-heading').show();
          }} else {{
            $('#past-deadlines-heading').hide();
          }}
          pastContainer.empty();
          items.forEach(function(item) {{
            pastContainer.append(item.el);
          }});
        }}

        past.sort(function(a, b) {{
          return a.order - b.order;
        }});
        renderPast(past);

        $('#sort-order-checkbox').on('change', function() {{
          var sorted = past.slice();
          if (this.checked) {{
            sorted.sort(function(a, b) {{
              if (!a.deadlineMoment && !b.deadlineMoment) return a.order - b.order;
              if (!a.deadlineMoment) return 1;
              if (!b.deadlineMoment) return -1;
              return a.deadlineMoment.diff(b.deadlineMoment);
            }});
          }} else {{
            sorted.sort(function(a, b) {{ return a.order - b.order; }});
          }}
          renderPast(sorted);
        }});

        var THREE_MONTHS_SEC = 90 * 24 * 60 * 60;
        pastContainer.find('.ConfItem').each(function() {{
          var $el = $(this);
          var diffAttr = parseFloat($el.attr('data-diff'));
          if (!isFinite(diffAttr)) {{
            $el.removeClass('past');
            $el.find('.timer,.timer-small,.calendar').remove();
            comingContainer.append($el);
          }} else if (Math.abs(diffAttr) > THREE_MONTHS_SEC) {{
            $el.remove();
          }}
        }});
        if (pastContainer.find('.ConfItem').length === 0) {{
          $('#past-deadlines-heading').hide();
        }}

        try {{
          $('.ConfItem .round-deadline-time').each(function() {{
            var txt = $(this).text().trim();
            if (!txt) return;
            var m = moment(txt, 'ddd MMM DD YYYY HH:mm:ss [GMT]Z', true);
            if (!m.isValid()) {{
              m = moment.parseZone(txt);
            }}
            if (m.isValid()) {{
              $(this).text(m.tz(display_timezone).format('ddd MMM DD YYYY HH:mm:ss [GMT]Z'));
            }}
          }});
        }} catch (e) {{ console.log('Post-processing error', e); }}

        var url = new URL(window.location);
        subs = url.searchParams.get('sub');
        if (subs == undefined) {{
          subs = store.get('gak97.github.io-subs');
        }} else {{
          subs = subs.toUpperCase().split(',');
        }}
        if (subs == undefined) {{
          subs = all_subs;
        }}
        $("#subject-select").multiselect("select", subs);
        update_filtering({{ subs: subs, all_subs: all_subs }});

        $('.conf-sub').click(function (e) {{
            var csub = $(this).data('sub');
            subs = [csub];
            $("#subject-select").multiselect('deselect', all_subs);
            $("#subject-select").multiselect('select', subs);
            update_filtering({{ subs: subs, all_subs: all_subs}});
        }});
    }});
    (function (i, s, o, g, r, a, m) {{
      i["GoogleAnalyticsObject"] = r;
      (i[r] =
        i[r] ||
        function () {{
          (i[r].q = i[r].q || []).push(arguments);
        }}),
        (i[r].l = 1 * new Date());
      (a = s.createElement(o)), (m = s.getElementsByTagName(o)[0]);
      a.async = 1;
      a.src = g;
      m.parentNode.insertBefore(a, m);
    }})(
      window,
      document,
      "script",
      "https://www.google-analytics.com/analytics.js",
      "ga"
    );
    ga("create", "", "auto");
    ga("send", "pageview");
    """
    return script


def build_conference_script(conferences: List[Dict[str, Any]]) -> str:
    data_json = json.dumps(conferences, ensure_ascii=False)
    data_json = data_json.replace('</', '<' + '\\' + '/')
    script = f"""
    $(function() {{
        var url = new URL(window.location);
        var conf = url.searchParams.get('id');

var subs = [];
var _all_subs = [];
// Get all subs
var conf_type_data = [{{"name":"Machine Learning","sub":"ML","color":"#ffd300"}},{{"name":"Computer Vision","sub":"CV","color":"#deff0a"}},{{"name":"Computer Graphics","sub":"CG","color":"#0aefff"}},{{"name":"Natural Language Proc","sub":"NLP","color":"#147df5"}},{{"name":"Robotics","sub":"RO","color":"#0aff99"}},{{"name":"Speech/SigProc","sub":"SP","color":"#580aff"}},{{"name":"Data Mining","sub":"DM","color":"#be0aff"}},{{"name":"Automated Planning","sub":"AP","color":"#a432a8"}},{{"name":"Knowledge Representation","sub":"KR","color":"#32a855"}},{{"name":"Human-Computer Interaction","sub":"HCI","color":"#a83232"}}];
var sub2name = {{}}; var name2sub = {{}};
for (var i = 0; i < conf_type_data.length; i++) {{
    _all_subs[i] = conf_type_data[i]['sub'];
    sub2name[conf_type_data[i]['sub']] = conf_type_data[i]['name'];
    name2sub[conf_type_data[i]['name']] = conf_type_data[i]['sub'];
}}
const all_subs = _all_subs;

function addUtcTimeZones() {{
  for (let offset = -12; offset <= 12; offset++) {{
    const posixSign = offset <= 0 ? "+" : "-";
    const isoSign = offset >= 0 ? "+" : "-";
    const link = `Etc/GMT${{posixSign}}${{Math.abs(offset)}}|UTC${{isoSign}}${{Math.abs(offset)}}`;
    moment.tz.link(link);
  }}
}}

function createCalendarFromObject(data) {{
  return createCalendar({{
    options: {{
      class: "calendar-obj",
      id: data.id,
    }},
    data: {{
      title: data.title,
      start: data.date,
      duration: 60,
    }},
  }});
}}

function getSubmissionRounds(conf) {{
  if (Array.isArray(conf.submission_rounds) && conf.submission_rounds.length > 0) {{
    return conf.submission_rounds;
  }}
  if (conf.deadline) {{
    return [{{ name: conf.round_label || 'Paper Submission', deadline: conf.deadline }}];
  }}
  return [];
}}

        addUtcTimeZones();
        var london_timezone = 'Europe/London';
        var local_timezone = london_timezone;
        $('.local-timezone').text(london_timezone);

        var conferenceData = {data_json};
        var confIndex = {{}};
        conferenceData.forEach(function(item) {{
          confIndex[item.id] = item;
        }});

        if (!conf || !confIndex[conf]) {{
          conf = conferenceData.length > 0 ? conferenceData[0].id : null;
        }}

        if (!conf || !confIndex[conf]) {{
          $('#conf-title-href').text('Conference not found');
          return;
        }}

        var data = confIndex[conf];
        $('#conf-title-href').text(data.title + ' ' + (data.year || ''));
        $('#conf-title-href').attr('href', '/ai-deadlines-mm/conference?id=' + data.id);
        $('#conf-full-name').text(data.full_name || '');

        $('#conf-subs').empty();
        if (data.tags) {{
          data.tags.forEach(function(tag) {{
            if (sub2name[tag]) {{
              var span = $('<span></span>');
              span.addClass('conf-sub conf-' + tag);
              span.text(sub2name[tag]);
              $('#conf-subs').append(span);
            }}
          }});
        }}

        if (data.date) {{
          $('#conf-date').text(data.date);
        }}
        if (data.location) {{
          $('#conf-place').text(data.location);
          $('#conf-place').attr('href', 'https://maps.google.com/?q=' + encodeURIComponent(data.location));
          $('#conf-place').removeAttr('nohref');
        }}
        if (data.url) {{
          $('#conf-website').text(data.url);
          $('#conf-website').attr('href', data.url);
          $('#conf-website').removeAttr('nohref');
        }}

        if (data.note) {{
          $('#conf-note-row').show();
          $('#conf-note-text').text(data.note);
        }} else {{
          $('#conf-note-row').hide();
        }}

        $('#conf-abstract-row').hide();

        var rounds = getSubmissionRounds(data);
        var timezone = data.timezone || 'UTC-12';
        var now = moment();
        var infoContainer = $('#conf-deadline-info');
        var timerContainer = $('#conf-deadline-timer');
        infoContainer.empty();
        timerContainer.empty();

        var nextRound = null;

        if (!rounds.length) {{
          infoContainer.hide();
          timerContainer.hide();
        }} else {{
          infoContainer.show();
          timerContainer.show();
          rounds.forEach(function(roundInfo, idx) {{
            var roundName = (roundInfo && roundInfo.name) ? roundInfo.name : ('Round ' + (idx + 1));
            var roundRow = $('<div class="conf-round-row row" data-round-index="' + idx + '"></div>');
            roundRow.append('<div class="meta deadline col-12 col-md-6">Download ' + roundName + ' deadline:</div>');
            var calendarCell = $('<div class="calendar meta col-sm-12 col-md-6 round-calendar" data-round-index="' + idx + '"></div>');
            roundRow.append(calendarCell);
            roundRow.append('<div class="meta deadline col-12 col-md-6">Deadline in conference timezone:</div>');
            var confTimeCell = $('<div class="meta col-sm-12 col-md-6"><span class="round-deadline-time" data-round-index="' + idx + '"></span></div>');
            roundRow.append(confTimeCell);
            roundRow.append('<div class="meta deadline col-12 col-md-6">Deadline in ' + local_timezone + ' timezone:</div>');
            var localTimeCell = $('<div class="local-timezone-hide meta col-sm-12 col-md-6"><span class="round-local-time" data-round-index="' + idx + '"></span></div>');
            roundRow.append(localTimeCell);
            infoContainer.append(roundRow);

            var timerRow = $('<div class="conf-round-timer col-12" data-round-index="' + idx + '"></div>');
            timerRow.append('<div class="round-timer-label">' + roundName + ' countdown:</div>');
            timerRow.append('<div class="round-timer-display" data-round-index="' + idx + '"></div>');
            timerContainer.append(timerRow);
          }});

          rounds.forEach(function(roundInfo, idx) {{
            var roundName = (roundInfo && roundInfo.name) ? roundInfo.name : ('Round ' + (idx + 1));
            var timeSpan = infoContainer.find('.round-deadline-time[data-round-index="' + idx + '"]');
            var localSpan = infoContainer.find('.round-local-time[data-round-index="' + idx + '"]');
            var calendarSlot = infoContainer.find('.round-calendar[data-round-index="' + idx + '"]');
            var timerDisplay = timerContainer.find('.round-timer-display[data-round-index="' + idx + '"]');
            if (!roundInfo || !roundInfo.deadline) {{
              timeSpan.text('Date TBD');
              localSpan.text('');
              calendarSlot.hide();
              timerDisplay.text('Deadline to be announced');
              return;
            }}
            try {{
              var confDeadline = moment.tz(roundInfo.deadline, timezone);
              if (!confDeadline.isValid()) {{
                timeSpan.text('Invalid deadline');
                localSpan.text('');
                calendarSlot.hide();
                timerDisplay.text('Invalid deadline');
                return;
              }}
              timeSpan.text(confDeadline.format('ddd MMM DD YYYY HH:mm:ss [GMT]Z'));
              try {{
                var localDeadline = moment.tz(confDeadline, local_timezone);
                localSpan.text(localDeadline.format('ddd MMM DD YYYY HH:mm:ss [GMT]Z'));
              }} catch (err) {{
                console.log('Error converting to local timezone for conference detail', err);
              }}
              var calendarNode = createCalendarFromObject({{
                id: data.id + '-round-' + idx,
                title: data.title + ' ' + (data.year || '') + ' ' + roundName + ' deadline',
                date: confDeadline.toDate(),
              }});
              calendarSlot.show().empty().append(calendarNode);
              var diff = confDeadline.diff(now, 'seconds');
              if (diff > 0) {{
                timerDisplay.countdown(confDeadline.toDate(), function(event) {{
                  $(this).html(event.strftime('%D days %Hh %Mm %Ss'));
                }});
                if (!nextRound || diff < nextRound.diff) {{
                  nextRound = {{ diff: diff, moment: confDeadline, name: roundName }};
                }}
              }} else {{
                timerDisplay.text('Deadline passed');
              }}
            }} catch (err) {{
              console.log('Error rendering detail deadline for', data.id, roundName, err);
              timeSpan.text('Date unavailable');
              localSpan.text('');
              calendarSlot.hide();
              timerDisplay.text('Date unavailable');
            }}
          }});

          if (!nextRound) {{
            timerContainer.find('.round-timer-display').each(function() {{
              if (!$(this).text()) {{
                $(this).text('Deadline passed');
              }}
            }});
          }}
        }}

        var twitterText = 'Countdown to the ' + data.title + ' ' + (data.year || '') + ' deadline!';
        if (nextRound && nextRound.name) {{
          twitterText = 'Countdown to the ' + nextRound.name + ' deadline for ' + data.title + ' ' + (data.year || '') + '!';
        }}
        var twitter_slug = '<a href="https://twitter.com/share" class="twitter-share-button" data-text="' + twitterText + '" data-show-count="false" style="font-size:13px;">Tweet</a><script async src="//platform.twitter.com/widgets.js" charset="utf-8">';
        $('#twitter-box').html(twitter_slug);

    }});
    """
    return script


def main():
    conferences = load_conferences()
    cards = '\n\n'.join(build_conference_card(conf, idx) for idx, conf in enumerate(conferences))
    index_template = INDEX_TEMPLATE_PATH.read_text(encoding='utf-8')
    index_script = build_index_script(conferences)
    index_content = index_template.replace('{{CONFERENCE_CARDS}}', cards).replace('{{SCRIPT_CONTENT}}', index_script)
    INDEX_OUTPUT_PATH.write_text(index_content, encoding='utf-8')

    # Update conference detail page
    conf_template = CONF_TEMPLATE_PATH.read_text(encoding='utf-8')
    conf_script = build_conference_script(conferences)
    conference_content = conf_template.replace('{{SCRIPT_CONTENT}}', conf_script)
    CONF_OUTPUT_PATH.write_text(conference_content, encoding='utf-8')


if __name__ == '__main__':
    main()
