<?php
// Admin router - fixed session and path issues
$db = getDB();

// Check if user is already logged in
$is_logged_in = isset($_SESSION['admin_logged_in']) && $_SESSION['admin_logged_in'] === true;

// Handle login
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['username']) && isset($_POST['password'])) {
    if ($_POST['username'] === ADMIN_USERNAME && $_POST['password'] === ADMIN_PASSWORD) {
        $_SESSION['admin_logged_in'] = true;
        $is_logged_in = true;
        header('Location: /manage/dashboard');
        exit;
    } else {
        $login_error = "Invalid credentials";
    }
}

// Handle logout
if (isset($_GET['logout'])) {
    session_destroy();
    header('Location: /manage');
    exit;
}

// If not logged in, show login page
if (!$is_logged_in) {
    showLoginPage($login_error ?? '');
    exit;
}

// Admin is logged in - show requested page
$admin_path = str_replace('/manage', '', $_SERVER['REQUEST_URI']);
$admin_path = ltrim($admin_path, '/');
$admin_path = explode('?', $admin_path)[0]; // Remove query string

switch($admin_path) {
    case '':
    case 'dashboard':
        showDashboard($db);
        break;
    case 'locations':
        showLocationsPage($db);
        break;
    case 'items':
        showItemsPage($db);
        break;
    default:
        showDashboard($db);
}

// [Rest of the admin functions remain the same as previous version]
// ... (include all the showLoginPage, showDashboard, showLocationsPage, showItemsPage functions from previous version)
// Due to length, I'm omitting the full repetition but they should be included
?>
