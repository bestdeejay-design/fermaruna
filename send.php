<?php
/**
 * Обработчик формы обратной связи (хостинг с PHP 7.4+, например sweb.ru).
 *
 * Настройка: скопируйте config.example.php в config.php и впишите адрес,
 * на который должны приходить заявки. config.php не попадает в репозиторий.
 *
 * Защита: скрытое поле-ловушка (honeypot), проверка полей, ограничение частоты
 * отправок с одного IP, защита заголовков письма от инъекций.
 * Ничего не пишет в лог и не хранит персональные данные на сервере.
 */

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');

function respond($code, $data)
{
    http_response_code($code);
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

function clean($value, $max)
{
    $value = is_string($value) ? $value : '';
    $value = trim(preg_replace('/[\r\n\t]+/', ' ', $value));
    return mb_substr($value, 0, $max, 'UTF-8');
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    respond(405, ['ok' => false, 'error' => 'method_not_allowed']);
}

$config = is_file(__DIR__ . '/config.php') ? (require __DIR__ . '/config.php') : [];
$to = isset($config['to']) ? trim((string) $config['to']) : '';
if ($to === '' || !filter_var($to, FILTER_VALIDATE_EMAIL)) {
    respond(503, ['ok' => false, 'error' => 'not_configured']);
}

// Ловушка для ботов: люди это поле не видят и не заполняют.
if (!empty($_POST['website'])) {
    respond(200, ['ok' => true]);
}

$name    = clean($_POST['name'] ?? '', 80);
$contact = clean($_POST['contact'] ?? '', 120);
$product = clean($_POST['product'] ?? '', 80);
$message = trim((string) ($_POST['message'] ?? ''));
$message = mb_substr(str_replace("\0", '', $message), 0, 2000, 'UTF-8');
$consent = !empty($_POST['consent']);

if (mb_strlen($name, 'UTF-8') < 2 || mb_strlen($contact, 'UTF-8') < 5 || !$consent) {
    respond(422, ['ok' => false, 'error' => 'validation']);
}

$isEmail = filter_var($contact, FILTER_VALIDATE_EMAIL) !== false;
$digits  = preg_replace('/\D+/', '', $contact);
if (!$isEmail && strlen($digits) < 6) {
    respond(422, ['ok' => false, 'error' => 'contact']);
}

// Не чаще одной заявки в 30 секунд с одного IP.
$ip   = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
$lock = sys_get_temp_dir() . '/fermaruna_form_' . md5($ip);
if (is_file($lock) && (time() - (int) @filemtime($lock)) < 30) {
    respond(429, ['ok' => false, 'error' => 'too_many']);
}
@touch($lock);

$host = preg_replace('/^www\./', '', $_SERVER['HTTP_HOST'] ?? 'localhost');
$host = preg_replace('/[^a-z0-9.\-]/i', '', $host) ?: 'localhost';
$from = isset($config['from']) && filter_var($config['from'], FILTER_VALIDATE_EMAIL) ? $config['from'] : 'no-reply@' . $host;

$subject = 'Заявка с сайта: ' . ($product !== '' ? $product : 'вопрос фермеру');
$body = "Новая заявка с сайта {$host}\n\n"
    . "Имя: {$name}\n"
    . "Контакт: {$contact}\n"
    . 'Интересует: ' . ($product !== '' ? $product : '—') . "\n\n"
    . "Сообщение:\n" . ($message !== '' ? $message : '—') . "\n\n"
    . 'Согласие на обработку персональных данных: да, ' . date('d.m.Y H:i') . "\n";

$headers = [
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
    'From: =?UTF-8?B?' . base64_encode('Сайт фермы «Рунская»') . "?= <{$from}>",
];
if ($isEmail) {
    $headers[] = 'Reply-To: ' . $contact;
}

$sent = @mail($to, '=?UTF-8?B?' . base64_encode($subject) . '?=', $body, implode("\r\n", $headers));

if (!$sent) {
    @unlink($lock);
    respond(500, ['ok' => false, 'error' => 'mail_failed']);
}

respond(200, ['ok' => true]);
