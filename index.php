<?php
// Cloud platform compatibility
if (getenv('PORT')) {
    $port = getenv('PORT');
    // For Render/Koyeb, we might need to adjust the base URL
    if (empty($_SERVER['HTTP_HOST'])) {
        $_SERVER['HTTP_HOST'] = getenv('RENDER_EXTERNAL_HOSTNAME') ?: getenv('KOYEB_APP_DOMAIN') ?: 'localhost';
    }
    if (empty($_SERVER['REQUEST_SCHEME'])) {
        $_SERVER['REQUEST_SCHEME'] = 'https';
    }
}

// Session configuration for cloud
if (getenv('PORT')) {
    ini_set('session.save_path', '/tmp');
}

session_start();

// Load configuration
require_once 'includes/config.php';

// Route handling with cloud compatibility
$request_uri = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
$query_params = $_GET;

// API Routes
if (strpos($request_uri, '/api/') === 0) {
    require_once 'includes/api_router.php';
    exit;
}

// Admin Routes
if ($request_uri === '/manage' || strpos($request_uri, '/manage/') === 0) {
    require_once 'includes/admin_router.php';
    exit;
}

// Public Routes - Main tracking functionality
if (empty($query_params['id'])) {
    // No ID parameter - show 403 error image
    header('HTTP/1.0 403 Forbidden');
    echo '<!DOCTYPE html><html><head><title>403 Forbidden</title></head><body style="margin:0;padding:0;display:flex;justify-content:center;align-items:center;height:100vh;background:#f5f5f5;">';
    echo '<img src="https://www.drlinkcheck.com/images/errors/403.png" alt="403 Forbidden" style="max-width:100%;max-height:100%;">';
    echo '</body></html>';
    exit;
}

// Process tracking request with ID
require_once 'includes/tracking_handler.php';
?>
