<?php
/**
 * Configuración del panel de administración — Tilo Estudio.
 *
 * IMPORTANTE: cambiá la contraseña por defecto ("tilo2026") antes de
 * subir el sitio a tu hosting. Para generar el código de una contraseña
 * nueva, corré esto en la Terminal de tu compu:
 *
 *   php -r "echo password_hash('tu-contraseña-nueva', PASSWORD_DEFAULT), PHP_EOL;"
 *
 * Copiá el resultado completo (empieza con $2y$) y pegalo abajo, en
 * lugar del valor actual.
 */
return [
    // Contraseña por defecto: tilo2026 — CAMBIAR antes de publicar.
    'ADMIN_PASSWORD_HASH' => '$2y$12$4ftS6prAxRq4.BcoM7e16.7givPnq9vtgbw0F6Uq/DAWz91.GvkRi',
];
