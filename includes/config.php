<?php
// Cloud platform detection and configuration
function isCloudPlatform() {
    return getenv('PORT') !== false || getenv('RENDER') !== false || getenv('KOYEB') !== false;
}

// Load environment variables with cloud compatibility
function loadEnv() {
    $env = [];
    
    // Try to load from .env file first
    if (file_exists('../.env')) {
        $env = parse_ini_file('../.env');
    }
    
    // Cloud platform environment variables override .env
    $cloudVars = [
        'ADMIN_USERNAME' => getenv('ADMIN_USERNAME'),
        'ADMIN_PASSWORD' => getenv('ADMIN_PASSWORD'),
        'SITE_BASE_URL' => getenv('SITE_BASE_URL'),
        'DB_PATH' => getenv('DB_PATH')
    ];
    
    foreach ($cloudVars as $key => $value) {
        if ($value !== false) {
            $env[$key] = $value;
        }
    }
    
    // Set defaults for cloud platforms
    if (isCloudPlatform()) {
        if (empty($env['DB_PATH'])) {
            $env['DB_PATH'] = './data/tracking.db';
        }
        if (empty($env['SITE_BASE_URL'])) {
            $env['SITE_BASE_URL'] = 'https://' . ($_SERVER['HTTP_HOST'] ?? 'localhost');
        }
    }
    
    return $env;
}

$env = loadEnv();

if (empty($env)) {
    error_log('Configuration error: No environment variables found');
    http_response_code(500);
    die('Configuration error: Please check environment setup');
}

// Database configuration
define('DB_PATH', $env['DB_PATH']);
define('ADMIN_USERNAME', $env['ADMIN_USERNAME'] ?? 'admin');
define('ADMIN_PASSWORD', $env['ADMIN_PASSWORD'] ?? 'password');
define('SITE_BASE_URL', $env['SITE_BASE_URL'] ?? 'http://localhost');

// Create database directory if it doesn't exist
$db_dir = dirname(DB_PATH);
if (!is_dir($db_dir)) {
    if (!mkdir($db_dir, 0755, true)) {
        error_log("Failed to create database directory: $db_dir");
        die('Failed to create database directory');
    }
}

// Initialize database
function getDB() {
    try {
        $db_path = DB_PATH;
        
        // Ensure directory exists
        $db_dir = dirname($db_path);
        if (!is_dir($db_dir)) {
            mkdir($db_dir, 0755, true);
        }
        
        $db = new PDO('sqlite:' . $db_path);
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        
        // Enable WAL mode for better concurrent access
        $db->exec('PRAGMA journal_mode=WAL;');
        
        // Create tables if they don't exist
        $db->exec("
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                media_type TEXT NOT NULL,
                media_url TEXT,
                file_path TEXT,
                is_active INTEGER DEFAULT 1,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ");
        
        $db->exec("
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_slug TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                ip_address TEXT NOT NULL,
                user_agent TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_slug) REFERENCES items(slug)
            )
        ");
        
        // Create indexes
        $db->exec("CREATE INDEX IF NOT EXISTS idx_locations_item_slug ON locations(item_slug)");
        $db->exec("CREATE INDEX IF NOT EXISTS idx_locations_timestamp ON locations(timestamp)");
        $db->exec("CREATE INDEX IF NOT EXISTS idx_items_expires ON items(expires_at)");
        $db->exec("CREATE INDEX IF NOT EXISTS idx_items_active ON items(is_active)");
        
        return $db;
    } catch(PDOException $e) {
        error_log("Database error: " . $e->getMessage());
        http_response_code(500);
        die('Database connection failed. Please check file permissions.');
    }
}

// Security functions
function sanitizeInput($data) {
    if (is_array($data)) {
        return array_map('sanitizeInput', $data);
    }
    return htmlspecialchars(strip_tags(trim($data)), ENT_QUOTES, 'UTF-8');
}

function generateSlug($title) {
    $slug = preg_replace('/[^a-z0-9]+/', '-', strtolower($title));
    $slug = trim($slug, '-');
    return $slug . '-' . substr(md5(uniqid()), 0, 6);
}

// CORS headers for API
function setCorsHeaders() {
    header('Access-Control-Allow-Origin: *');
    header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
    header('Access-Control-Allow-Headers: X-API-Key, Content-Type');
}

// JSON response helper
function jsonResponse($data, $statusCode = 200) {
    http_response_code($statusCode);
    header('Content-Type: application/json');
    echo json_encode($data);
    exit;
}
?>
