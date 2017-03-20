<?php
# Get your app keys on https://stepik.org/oauth2/applications (Client Type = confidential; Authorization Grant Type: authorization code)
define('OAUTH2_CLIENT_ID', '...');
define('OAUTH2_CLIENT_SECRET', '...');

# OAuth2 flow based on https://gist.github.com/aaronpk/3612742

$authorizeURL = 'https://stepik.org/oauth2/authorize/';
$tokenURL = 'https://stepik.org/oauth2/token/';
$apiURLBase = 'https://stepik.org/api/';
$scriptPath = 'http://vyahhi.net/data/'; # if you want more general than use = 'http://' . $_SERVER['SERVER_NAME'] . $_SERVER['PHP_SELF'];
date_default_timezone_set('UTC');

session_start();

if (get('action') == 'logout') {
    session_start();
    session_unset();
    session_destroy();
    header('Location: ' . $scriptPath);
    die();
}

# Start the login process by sending the user to Github's authorization page
if (get('action') == 'login') {
    # Generate a random hash and store in the session for security
    $_SESSION['state'] = hash('sha256', microtime(TRUE) . rand() . $_SERVER['REMOTE_ADDR']);
    unset($_SESSION['access_token']);

    $params = array(
        'client_id' => OAUTH2_CLIENT_ID,
        'redirect_uri' => $scriptPath,
        'scope' => 'read',
        'state' => $_SESSION['state'],
        'response_type' => 'code'
    );

    # Redirect the user to Github's authorization page
    header('Location: ' . $authorizeURL . '?' . http_build_query($params));
    die();
}

# When Github redirects the user back here, there will be a "code" and "state" parameter in the query string

if (get('code')) {
    # Verify the state matches our stored state
    if (!get('state') || $_SESSION['state'] != get('state')) {
        header('Location: ' . $scriptPath);
        die();
    }

    # Exchange the auth code for a token
    $token = apiRequest($tokenURL, array(
        'client_id' => OAUTH2_CLIENT_ID,
        'client_secret' => OAUTH2_CLIENT_SECRET,
        'redirect_uri' => $scriptPath,
        'state' => $_SESSION['state'],
        'code' => get('code'),
        'grant_type' => 'authorization_code'
    ));
    $_SESSION['access_token'] = $token->access_token;

    header('Location: ' . $scriptPath);
}

if (session('access_token')) {

    # =========
    # WELCOME!
    # =========

    $stepics = apiRequest($apiURLBase . 'stepics/1');
    $user_id = $stepics->profiles[0]->id;
    $first_name = $stepics->profiles[0]->first_name;
    $last_name = $stepics->profiles[0]->last_name;
    echo '<html><head>';
    echo '<title>Личный кабинет онлайн-программы «Анализ данных»</title>';
    echo '<link rel="stylesheet" href="https://stepik.org/static/frontend/cli-build/stepic.css">';
    echo '<link rel="shortcut icon" href="https://static.tildacdn.com/tild6662-3335-4663-b334-643039313631/data_fav.ico" type="image/x-icon" />';
    echo '</head><body style="padding:20px">';
    echo '<h3>Личный кабинет онлайн-программы «<a href="http://data.stepik.org">Анализ данных</a>» на <a href="https://stepik.org">Stepik.org</a></h3>';
    echo '<h4>Добро пожаловать, <a href="https://stepik.org/users/' . $user_id . '">' . $first_name . '  ' . $last_name . '</a>!</h4>';
    echo '<hr>';

    # =============
    # COURSES LIST
    # =============

    $courses = array(
        array('id' => 217, 'required' => True, 'sections' => array(2, 4), 'need_to_pass' => 85, 'exams' => 1536), # Алгоритмы: теория и практика. Методы
        array('id' => 129, 'required' => True, 'sections' => array(1, 2, 3), 'need_to_pass' => 85, 'exams' => 1425), # Анализ данных в R
        array('id' => 724, 'required' => True, 'sections' => array(1, 2, 3), 'need_to_pass' => 85, 'exams' => null), # Анализ данных в R. Часть 2
        array('id' => 1240, 'required' => True, 'sections' => array(1, 2, 5, 6), 'need_to_pass' => 85, 'exams' => 1534), # Введение в базы данных
        array('id' => 253, 'required' => True, 'sections' => array(1, 3, 4, 5), 'need_to_pass' => 85, 'exams' => 1535), # Введение в архитектуру ЭВМ. Элементы операционных систем.
        array('id' => 902, 'required' => True, 'sections' => array(1, 2, 3, 4), 'need_to_pass' => 90, 'exams' => 1424), # Дискретная математика
        array('id' => 73, 'required' => True, 'sections' => array(1, 2, 3), 'need_to_pass' => 90, 'exams' => 1427), # Введение в Linux
        array('id' => 497, 'required' => True, 'sections' => array(1, 2, 3), 'need_to_pass' => 85, 'exams' => 1426), # Основы программирования на R
        array('id' => 76, 'required' => True, 'sections' => array(1, 2, 3), 'need_to_pass' => 90, 'exams' => 1423), # Основы статистики
        array('id' => 524, 'required' => True, 'sections' => array(1, 2, 3), 'need_to_pass' => 85, 'exams' => null), # Основы статистики. Часть 2
        array('id' => 67, 'required' => True, 'sections' => array(1, 2, 3), 'need_to_pass' => 90, 'exams' => 1428), # Программирование на Python
        array('id' => 512, 'required' => True, 'sections' => array(1, 2, 3), 'need_to_pass' => 90, 'exams' => null), # Python: основы и применение
        array('id' => 217, 'required' => False, 'sections' => array(6, 8), 'need_to_pass' => 85, 'exams' => 1537), # Алгоритмы: теория и практика. Методы
        array('id' => 253, 'required' => False, 'sections' => array(2, 6, 7), 'need_to_pass' => 85, 'exams' => 1538), # Введение в архитектуру ЭВМ. Элементы операционных систем.
        array('id' => 1240, 'required' => False, 'sections' => array(3, 4, 7), 'need_to_pass' => 85, 'exams' => 1544), # Введение в базы данных
        array('id' => 95, 'required' => False, 'sections' => array(1, 2, 3, 4), 'need_to_pass' => 85, 'exams' => 1429), # Введение в математический анализ
        array('id' => 401, 'required' => False, 'sections' => array(1, 2, 3, 4), 'need_to_pass' => 85, 'exams' => 1432), # Нейронные сети
        array('id' => 7, 'required' => False, 'sections' => array(1, 2, 3, 4, 5, 6), 'need_to_pass' => 85, 'exams' => 1430), # Программирование на языке C++
        array('id' => 187, 'required' => False, 'sections' => array(1, 2, 3, 4, 5, 6), 'need_to_pass' => 85, 'exams' => 1431), # Java. Базовый курс
        array('id' => 2152, 'required' => False, 'sections' => array(1, 2, 3), 'need_to_pass' => 85, 'exams' => 2387), # Основы статистики. ч.3
        # TO ADD WHEN READY: Управление вычислениями (required)
        # TO ADD WHEN READY: Machine Learning (not required)
    );

    echo '<h4>Курсы программы (<a href="https://static.tildacdn.com/tild3430-6633-4163-b839-326632353161/schemefix.png">взаимосвязи</a>):</h4>';
    echo '<table border=1 cellspacing=0 cellpadding=10>';
    echo '<tr><th colspan=6><b>Обязательные курсы:</b></th></tr>';
    echo '<tr><th>Курс</th><th>Количество<br>модулей</th><th>Модули</th><th>Ваши баллы</th><th>Ваш процент</th><th>Допуск к экзамену</th></tr>';

    $previousCourse = null;
    foreach ($courses as $course) {
        $info = apiRequest($apiURLBase . 'courses/' . $course['id'])->courses[0];
        $section_ids = array();
        foreach ($course['sections'] as $i) {
            $section_ids[] = $info->sections[$i - 1];
        }
        $sections = apiRequest($apiURLBase . 'sections?ids[]=' . implode('&ids[]=', $section_ids))->sections;
        $progress_ids = array();
        foreach ($sections as $section) {
            $progress_ids[] = $section->progress;
        }
        $progresses = apiRequest($apiURLBase . 'progresses?ids[]=' . implode('&ids[]=', $progress_ids))->progresses;
        $score = 0;
        $cost = 0;
        foreach ($progresses as $progress) {
            $score += $progress->score;
            $cost += $progress->cost;
        }

        $percentage = $cost ? round(100 * $score / $cost, 2) : 0;
        if ($percentage >= $course['need_to_pass']) {
            try {
                $exam = apiRequest($apiURLBase . 'courses/' . $course['exams'])->courses[0];
                $progress = apiRequest($apiURLBase . 'progresses/' . $exam->progress)->progresses[0];
                $exam_message = $progress->score . ' / ' . $progress->cost;
            } catch (Exception $e) {
                $exam_message = '<a href="https://stepik.org/courses/' . $exam->slug . '">можно начать</a>';
            }
        } else {
            $exam_message = 'нет доступа (нужно ' . $course['need_to_pass'] . '% за курс)';
        }
        if ($previousCourse['required'] and !$course['required']) {
            echo '<tr><th colspan=6><b>Курсы по выбору:</b></th></tr>';
            echo '<tr><th>Курс</th><th>Количество<br>модулей</th><th>Модули</th><th>Ваши баллы</th><th>Ваш процент</th><th>Экзамен</th></tr>';
        }

        echo '<tr>';
        echo '<td><a href="https://stepik.org/course/' . $info->slug . '">' . $info->title . '</a></td>';
        echo '<td>' . count($course['sections']) . '</td>';
        echo '<td>' . implode(", ", $course['sections']) . '</td>';

        if ($cost) {
            echo '<td>' . $score . ' / ' . $cost . '</td>';
            echo '<td>' . $percentage . '%</td>';
        } else {
            echo '<td colspan=2>Запишитесь на курс</td>';
        }

        echo '<td>' . $exam_message . '</td>';
        echo '</tr>';
        $previousCourse = $course;
    }

    echo '</table>';

    # =============
    # PAYMENTS LOG
    # =============

    $subscription_plans = array(10 => 0, 1999 => 1, 5397 => 3, 6000 => 3, 9595 => 6, 16791 => 12);
    $format = 'M d, Y (H:i)';
    $page = 1;
    $payments_list = array();
    $payment_start = 0;
    $payment_valid_until = 0;
    do {
        $payments = apiRequest($apiURLBase . 'payments?page=' . $page);
        foreach ($payments->payments as $payment) {
            if ($payment->destination_type != 'au_data') {
                continue;
            }

            $payment_date = strtotime($payment->payment_date);
            $payment_start = max($payment_date, $payment_start);
            $months = $subscription_plans[intval($payment->amount)];
            $payment_valid_until = paymentDue($payment_start, $months);
            $payments_list[] = array(
                intval($payment->amount),
                date($format, $payment_date),
                date($format, $payment_start),
                date($format, $payment_valid_until)
            );
            $payment_start = $payment_valid_until;
        }
        $page += 1;
    } while ($payments->meta->has_next);

    if ($payment_valid_until >= time()) {
        $color = ($payment_valid_until - time() >= 60 * 60 * 24 * 7) ? "#66cc66" : "cccc00"; # yellow if less than one week left
        echo '<h4>Ваша подписка на программу <span style="background-color:' . $color . '">&nbsp;активна до ' . date($format, $payment_valid_until) . '&nbsp;</span></h4>';
    } else {
        echo '<h4>Ваша подписка на программу <span style="background-color:#ff6666">&nbsp;не активна&nbsp;</span></h4>';
    }

    echo '<h4>Ваши платежи:</h4>';
    echo '<table border=1 cellspacing=0 cellpadding=10>';
    echo '<tr><th>Сумма (руб)</th><th>Дата и время платежа (UTC)</th><th>Действует от</th><th>Действует до</th></tr>';
    foreach (array_reverse($payments_list) as $payment) {
        echo '<tr><td>';
        echo implode('</td><td>', $payment);
        echo '</td></tr>';
    }
    echo '</table>';

    # LOGOUT
    echo '<p><a href="?action=logout">[Выйти из кабинета]</a></p>';
    echo '</body></html>';
} else {
    echo '<h3>Личный кабинет онлайн-программы «<a href="http://data.stepik.org">Анализ данных</a>» на <a href="https://stepik.org">Stepik.org</a></h3>';
    echo '<h3>Вы не вошли</h3>';
    echo '<p><a href="?action=login">Войти через Stepik.org</a></p>';
}

# =================
# HELPER FUNCTIONS
# =================

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

# Based on http://stackoverflow.com/a/24014541/92396 but fixed and simplified:
function paymentDue($timestamp, $months)
{
    $date = new DateTime('@' . $timestamp);
    $next = clone $date;
    $next->modify('last day of +' . $months . ' month');
    if ($date->format('d') > $next->format('d')) {
        $add = $date->diff($next);
    } else {
        $add = new DateInterval('P' . $months . 'M');
    }
    $newDate = $date->add($add);
    return $newDate->getTimestamp();
}
