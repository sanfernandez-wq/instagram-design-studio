<?php
/**
 * Backend de producción del CMS de Tilo Estudio — reemplaza a server.py
 * (que solo sirve para probar en tu compu) cuando el sitio vive en un
 * hosting real. Misma lógica: lee y escribe los archivos data/*.json.
 *
 * Requiere que .htaccess esté subido junto a este archivo (arma las
 * rutas /api/slides, /api/services, etc. para que apunten acá).
 */

header('Content-Type: application/json; charset=utf-8');

$ROOT = __DIR__;
$DATA_DIR = $ROOT . '/data';
$ASSET_DIR = $ROOT . '/assets';
$config = require $ROOT . '/config.php';

$COLLECTIONS = [
    'slides'    => ['file' => $DATA_DIR . '/slides.json',    'key' => 'slides',     'kind' => 'list'],
    'manifesto' => ['file' => $DATA_DIR . '/manifesto.json', 'key' => 'manifiesto', 'kind' => 'dict'],
    'services'  => ['file' => $DATA_DIR . '/services.json',  'key' => 'services',   'kind' => 'list'],
    'projects'  => ['file' => $DATA_DIR . '/projects.json',  'key' => 'projects',   'kind' => 'list'],
];

function send_json($data, $status = 200) {
    http_response_code($status);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function require_admin_key($config) {
    $key = $_SERVER['HTTP_X_ADMIN_KEY'] ?? '';
    if ($key === '' || !password_verify($key, $config['ADMIN_PASSWORD_HASH'])) {
        send_json(['ok' => false, 'error' => 'Contraseña incorrecta.'], 401);
    }
}

$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'OPTIONS') {
    header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, X-Admin-Key');
    exit;
}

$name = $_GET['name'] ?? '';

if ($name === 'upload-image') {
    if ($method !== 'POST') send_json(['ok' => false, 'error' => 'method not allowed'], 405);
    require_admin_key($config);

    $body = json_decode(file_get_contents('php://input'), true) ?: [];
    $dataUrl = $body['dataUrl'] ?? '';
    $prefix = preg_replace('/[^a-zA-Z0-9_-]/', '', $body['prefix'] ?? 'img');
    if ($prefix === '') $prefix = 'img';

    if (!preg_match('/^data:image\/(\w+);base64,(.+)$/s', $dataUrl, $m)) {
        send_json(['ok' => false, 'error' => 'La imagen no tiene un formato válido (data URL esperada).'], 400);
    }
    $ext = strtolower($m[1]);
    if ($ext === 'jpeg') $ext = 'jpg';
    if (!in_array($ext, ['jpg', 'png', 'webp', 'gif'], true)) $ext = 'jpg';

    $raw = base64_decode($m[2]);
    if (!is_dir($ASSET_DIR)) mkdir($ASSET_DIR, 0755, true);
    $fname = $prefix . '-' . substr(bin2hex(random_bytes(6)), 0, 10) . '.' . $ext;
    file_put_contents($ASSET_DIR . '/' . $fname, $raw);

    send_json(['ok' => true, 'path' => 'assets/' . $fname]);
}

if (!isset($COLLECTIONS[$name])) {
    send_json(['ok' => false, 'error' => 'not found'], 404);
}
$col = $COLLECTIONS[$name];

if ($method === 'GET') {
    if (file_exists($col['file'])) {
        $raw = file_get_contents($col['file']);
        $data = json_decode($raw, true);
        send_json($data);
    }
    send_json([$col['key'] => $col['kind'] === 'list' ? [] : new stdClass()]);
}

if ($method === 'POST') {
    require_admin_key($config);

    $data = json_decode(file_get_contents('php://input'), true);
    if (!is_array($data) || !array_key_exists($col['key'], $data)) {
        send_json(['ok' => false, 'error' => "Formato inválido: se esperaba { {$col['key']}: ... }"], 400);
    }
    $value = $data[$col['key']];
    if (!is_array($value)) {
        $tipo = $col['kind'] === 'list' ? '[...]' : '{...}';
        send_json(['ok' => false, 'error' => "Formato inválido: se esperaba { {$col['key']}: {$tipo} }"], 400);
    }

    if (!is_dir($DATA_DIR)) mkdir($DATA_DIR, 0755, true);
    $out = [$col['key'] => $value];
    $flags = JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT;
    if ($col['kind'] === 'dict' && empty($value)) $flags |= JSON_FORCE_OBJECT;
    file_put_contents($col['file'], json_encode($out, $flags));

    send_json(['ok' => true]);
}

send_json(['ok' => false, 'error' => 'method not allowed'], 405);
