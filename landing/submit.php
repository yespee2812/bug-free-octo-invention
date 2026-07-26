<?php
/**
 * ScriptLens waitlist handler for Hostinger shared hosting.
 * Appends valid emails to waitlist.csv and redirects to thank-you.html.
 */

declare(strict_types=1);

const WAITLIST_FILE = __DIR__ . '/waitlist.csv';
const THANK_YOU_URL = 'thank-you.html';
const ERROR_URL = 'index.html?error=1';

/**
 * Redirect the browser to a relative URL and exit.
 */
function redirect_to(string $url): void
{
    header('Location: ' . $url, true, 303);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    redirect_to('index.html');
}

// Honeypot — bots often fill hidden fields.
$honeypot = trim((string) ($_POST['website'] ?? ''));
if ($honeypot !== '') {
    redirect_to(THANK_YOU_URL);
}

$email = strtolower(trim((string) ($_POST['email'] ?? '')));
if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    redirect_to(ERROR_URL);
}

$timestamp = gmdate('c');
$ip = substr((string) ($_SERVER['REMOTE_ADDR'] ?? ''), 0, 64);
$ua = substr((string) ($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 200);

if (!file_exists(WAITLIST_FILE)) {
    $header = "email,subscribed_at,ip,user_agent\n";
    if (file_put_contents(WAITLIST_FILE, $header, LOCK_EX) === false) {
        redirect_to(ERROR_URL);
    }
}

// Skip exact duplicates (same email already on the list).
$existing = @file(WAITLIST_FILE, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
if (is_array($existing)) {
    foreach ($existing as $line) {
        $parts = str_getcsv($line);
        if (isset($parts[0]) && strtolower($parts[0]) === $email) {
            redirect_to(THANK_YOU_URL);
        }
    }
}

$row = [$email, $timestamp, $ip, $ua];
$fh = fopen(WAITLIST_FILE, 'ab');
if ($fh === false) {
    redirect_to(ERROR_URL);
}

if (!flock($fh, LOCK_EX)) {
    fclose($fh);
    redirect_to(ERROR_URL);
}

fputcsv($fh, $row);
flock($fh, LOCK_UN);
fclose($fh);

redirect_to(THANK_YOU_URL);
