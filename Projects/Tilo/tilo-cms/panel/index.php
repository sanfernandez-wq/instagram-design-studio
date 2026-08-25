<?php
/**
 * Puerta de entrada al panel de administración — Tilo Estudio.
 * Pide la misma contraseña de config.php; una vez logueada, la sesión
 * de PHP queda guardada y api.php la reconoce automáticamente (mismas
 * cookies, mismo sitio) sin que el panel tenga que mandar nada más.
 */
session_start();

$config = require __DIR__ . '/../config.php';
$error = '';

if (isset($_GET['logout'])) {
    session_destroy();
    header('Location: index.php');
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $password = $_POST['password'] ?? '';
    if ($password !== '' && password_verify($password, $config['ADMIN_PASSWORD_HASH'])) {
        session_regenerate_id(true);
        $_SESSION['tilo_admin'] = true;
        header('Location: index.php');
        exit;
    }
    $error = 'Contraseña incorrecta.';
}

if (!empty($_SESSION['tilo_admin'])) {
    // Ya logueada: mostrar el panel de verdad.
    require __DIR__ . '/admin.html';
    exit;
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ingresar — Panel Tilo Estudio</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    background: #1b1812;
  }
  .box {
    background: #F9F9F6; border-radius: 14px; padding: 36px 32px; width: 100%; max-width: 340px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  }
  h1 { font-size: 17px; margin: 0 0 22px; color: #1b1812; text-align: center; }
  input[type=password] {
    width: 100%; padding: 12px 14px; border: 1px solid #E5E1D6; border-radius: 8px; font-size: 15px;
    margin-bottom: 14px;
  }
  button {
    width: 100%; padding: 12px; border: none; border-radius: 30px; background: #B8942A; color: #fff;
    font-weight: 700; font-size: 14px; cursor: pointer;
  }
  button:hover { background: #a3810f; }
  .error { color: #c0392b; font-size: 13px; margin: -6px 0 14px; text-align: center; }
</style>
</head>
<body>
  <div class="box">
    <h1>Panel de administración — Tilo Estudio</h1>
    <form method="POST">
      <?php if ($error): ?><div class="error"><?php echo htmlspecialchars($error); ?></div><?php endif; ?>
      <input type="password" name="password" placeholder="Contraseña" autofocus required>
      <button type="submit">Ingresar</button>
    </form>
  </div>
</body>
</html>
