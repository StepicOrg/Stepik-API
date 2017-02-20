<?php
# Bioinformatics Contest 2017 Final Round – public monitor (mon.stepik.org)
# 1. Enter client_id & client_secret
# 2. Run as /usr/bin/php5.6 /home/ubuntu/monf.php > /var/www/html/index.html
# 3. Add it to crontab -e to run every minute

date_default_timezone_set('UTC');

session_start();

# Get your app keys on https://stepik.org/oauth2/applications (Client Type = confidential; Authorization Grant Type: client credentials)
$token = apiRequest(
    'https://stepik.org/oauth2/token/', 
    array(
        'grant_type' => 'client_credentials', 
        'client_id' => '...', 
        'client_secret' => '...')
);
$_SESSION['access_token'] = $token->access_token;

if (session('access_token')) {
?>

<html>
<head>
<meta charset="UTF-8"> 
<title>Bioinformatics Contest 2017 Final Round</title>
<style>
    tr:nth-child(2n) { /* even rows */ 
      background-color:#eef;
    }     
    tr:nth-child(2n+1) { /* odd rows */
      background-color:#ccf;
    }
    th {
        background-color: lightblue;
    }
    .total {
        border-right: 2px black solid;
    }
</style>
</head>
<body>
<h1>Bioinformatics Contest 2017 Final Round (finished!)</h1>
<h3>
    Round Started: <a href="https://www.timeanddate.com/worldclock/fixedtime.html?msg=Bioinformatics+Contest+Final+Round&iso=20170218T0001&p1=1440&ah=23&am=55">00:01:00 (UTC)</a>.
    Round Ended: 23:59:00 (UTC).
    Round Date: 18 Feb 2017.
</h3>
<h3>Last Update: <?php echo date('H:i:s, d M Y'); ?> (UTC).</h3>
<table border=1 cellpadding=10 cellspacing=0 style="text-align: center; background-color: lightblue"><tbody>
<tr>
    <th rowspan=2>#</th>
    <th rowspan=2>Name</th>
    <th rowspan=2 class="total">Total</th>
    <th colspan=2>Gene Expression</th>
    <th colspan=2>Reconstruction of Bacteria</th>
    <th colspan=10>Genetic Linkage Map</th>
    <th colspan=6>Locating Insertions</th>
    <th colspan=7>Pathway Dissection</th>
</tr>
<tr>
    <th><a href="https://stepik.org/lesson/32224/step/3">Easy</a></th>
    <th><a href="https://stepik.org/lesson/32224/step/4">Hard</a></th>
    <th><a href="https://stepik.org/lesson/33452/step/3">Easy</a></th>
    <th><a href="https://stepik.org/lesson/33452/step/4">Hard</a></th>
    <th><a href="https://stepik.org/lesson/40779/step/3">#1</a></th>
    <th><a href="https://stepik.org/lesson/40779/step/4">#2</a></th>
    <th><a href="https://stepik.org/lesson/40779/step/5">#3</a></th>
    <th><a href="https://stepik.org/lesson/40779/step/6">#4</a></th>
    <th><a href="https://stepik.org/lesson/40779/step/7">#5</a></th>
    <th><a href="https://stepik.org/lesson/40779/step/8">#6</a></th>
    <th><a href="https://stepik.org/lesson/40779/step/9">#7</a></th>
    <th><a href="https://stepik.org/lesson/40779/step/10">#8</a></th>
    <th><a href="https://stepik.org/lesson/40779/step/11">#9</a></th>
    <th><a href="https://stepik.org/lesson/40779/step/12">#10</a></th>
    <th><a href="https://stepik.org/lesson/40285/step/3">#1</a></th>
    <th><a href="https://stepik.org/lesson/40285/step/4">#2</a></th>
    <th><a href="https://stepik.org/lesson/40285/step/5">#3</a></th>
    <th><a href="https://stepik.org/lesson/40285/step/6">#4</a></th>
    <th><a href="https://stepik.org/lesson/40285/step/7">#5</a></th>
    <th><a href="https://stepik.org/lesson/40285/step/8">#6</a></th>
    <th><a href="https://stepik.org/lesson/40926/step/3">#1</a></th>
    <th><a href="https://stepik.org/lesson/40926/step/4">#2</a></th>
    <th><a href="https://stepik.org/lesson/40926/step/5">#3</a></th>
    <th><a href="https://stepik.org/lesson/40926/step/6">#4</a></th>
    <th><a href="https://stepik.org/lesson/40926/step/7">#5</a></th>
    <th><a href="https://stepik.org/lesson/40926/step/8">#6</a></th>
    <th><a href="https://stepik.org/lesson/40926/step/9">#7</a></th>
</tr>

<?php
    $page = 1;
    $steps = array(
        156700, 165437,
        164064, 163802,
        164524, 164528, 164527, 164533, 164531, 164525, 164529, 164532, 164530, 164526,
        164979, 165431, 165432, 165433, 165435, 165436,
        165033, 165359, 165361, 165358, 165360, 165362, 165363,
    );
    do {
        $grades = apiRequest('https://stepik.org/api/course-grades?course=1995&page=' . $page);
        foreach ($grades->{'course-grades'} as $course_grade) {
            if (!$course_grade->rank) continue;
            echo '<tr>';
            echo '<td>' . $course_grade->rank . '</td>';
            $users = apiRequest('https://stepik.org/api/users/' . $course_grade->user);
            $full_name = $users->users[0]->first_name . ' ' . $users->users[0]->last_name;
            $full_name = transliterate($full_name);
            echo '<td>' . $full_name . '</td>';
            echo '<td class="total"><b>' . round($course_grade->score - 1, 2) . '</b></td>';
            foreach ($steps as $step) {
                $ok = False;
                foreach ($course_grade->results as $result) {
                    if ($result->step_id != $step) continue;
                    $color = 'white';
                    if ($result->score) {
                        $color = 'yellow';
                    }
                    if ($result->is_passed) {
                        $color = 'lightgreen';
                    }
                    echo '<td style="background-color: ' . $color. '">' . round($result->score, 2) . '</td>';
                    $ok = True;
                    break;
                }
                if (!$ok) {
                    echo '<td style="background-color: white"> 0 </td>';
                }
            }
            echo '</tr>';
        }
        $page++;
    } while ($grades->meta->has_next);
    echo '</tbody></table></body></html>';
}

// # =================
// # HELPER FUNCTIONS
// # =================

function apiRequest($url, $post = FALSE, $headers = array())
{
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, TRUE);

    if ($post)
        curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($post));

    $headers[] = 'Accept: application/json';

    if (session('access_token'))
        $headers[] = 'Authorization: Bearer ' . session('access_token');

    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

    $response = curl_exec($ch);
    return json_decode($response);
}

function get($key, $default = NULL)
{
    return array_key_exists($key, $_GET) ? $_GET[$key] : $default;
}

function session($key, $default = NULL)
{
    return array_key_exists($key, $_SESSION) ? $_SESSION[$key] : $default;
}

// http://stackoverflow.com/a/8285804
function transliterate($textcyr = null, $textlat = null) {
    $cyr = array(
        'а','б','в','г','д','е','ё','ж','з','и','й','к','л','м','н','о','п',
        'р','с','т','у','ф','х','ц','ч','ш','щ','ъ','ы','ь','э','ю','я',
        'А','Б','В','Г','Д','Е','Ё','Ж','З','И','Й','К','Л','М','Н','О','П',
        'Р','С','Т','У','Ф','Х','Ц','Ч','Ш','Щ','Ъ','Ы','Ь','Э','Ю','Я'
    );
    $lat = array(
        'a','b','v','g','d','e','io','zh','z','i','y','k','l','m','n','o','p',
        'r','s','t','u','f','h','ts','ch','sh','sht','a','i','y','e','yu','ya',
        'A','B','V','G','D','E','Io','Zh','Z','I','Y','K','L','M','N','O','P',
        'R','S','T','U','F','H','Ts','Ch','Sh','Sht','A','I','Y','e','Yu','Ya'
    );
    if($textcyr) return str_replace($cyr, $lat, $textcyr);
    else if($textlat) return str_replace($lat, $cyr, $textlat);
    else return null;
}
?>
