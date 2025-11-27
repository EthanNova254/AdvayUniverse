<?php
// Set CORS headers for API
setCorsHeaders();

// Handle preflight requests
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

$db = getDB();
$api_key = $_SERVER['HTTP_X_API_KEY'] ?? '';

// Get the endpoint from request
$request_uri = $_SERVER['REQUEST_URI'];
$endpoint = preg_replace('/^\/api\//', '', $request_uri);
$endpoint = explode('?', $endpoint)[0]; // Remove query string

// Verify API key for protected endpoints
function verifyApiKey() {
    global $api_key;
    if ($api_key !== ADMIN_PASSWORD) {
        jsonResponse(['error' => 'Invalid API key'], 401);
    }
}

switch($endpoint) {
    case 'locations/capture':
        handleLocationCapture($db);
        break;
    case 'locations/get':
        verifyApiKey();
        handleGetLocations($db);
        break;
    case 'items/create':
        verifyApiKey();
        handleCreateItem($db);
        break;
    case 'items/list':
        verifyApiKey();
        handleListItems($db);
        break;
    case 'items/update':
        verifyApiKey();
        handleUpdateItem($db);
        break;
    case 'items/delete':
        verifyApiKey();
        handleDeleteItem($db);
        break;
    case 'cleanup':
        verifyApiKey();
        handleCleanup($db);
        break;
    default:
        jsonResponse(['error' => 'Endpoint not found'], 404);
}

function handleLocationCapture($db) {
    $item_slug = sanitizeInput($_GET['item_slug'] ?? '');
    $lat = $_GET['lat'] ?? null;
    $long = $_GET['long'] ?? null;
    
    if (empty($item_slug)) {
        jsonResponse(['error' => 'Item slug required'], 400);
    }
    
    try {
        $stmt = $db->prepare("
            INSERT INTO locations (item_slug, latitude, longitude, ip_address, user_agent) 
            VALUES (?, ?, ?, ?, ?)
        ");
        
        $stmt->execute([
            $item_slug,
            $lat ? (float)$lat : null,
            $long ? (float)$long : null,
            $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? 'Unknown',
            $_SERVER['HTTP_USER_AGENT'] ?? 'Unknown'
        ]);
        
        jsonResponse(['success' => true]);
    } catch (Exception $e) {
        error_log("Location capture error: " . $e->getMessage());
        jsonResponse(['success' => true]); // Still return success to user
    }
}

function handleGetLocations($db) {
    $item_slug = $_GET['item_slug'] ?? null;
    $start_date = $_GET['start_date'] ?? null;
    $end_date = $_GET['end_date'] ?? null;
    $limit = min($_GET['limit'] ?? 1000, 5000); // Prevent excessive data retrieval
    
    $sql = "SELECT l.*, i.title as item_title FROM locations l LEFT JOIN items i ON l.item_slug = i.slug WHERE 1=1";
    $params = [];
    
    if ($item_slug) {
        $sql .= " AND l.item_slug = ?";
        $params[] = $item_slug;
    }
    
    if ($start_date) {
        $sql .= " AND l.timestamp >= ?";
        $params[] = $start_date;
    }
    
    if ($end_date) {
        $sql .= " AND l.timestamp <= ?";
        $params[] = $end_date;
    }
    
    $sql .= " ORDER BY l.timestamp DESC LIMIT ?";
    $params[] = $limit;
    
    try {
        $stmt = $db->prepare($sql);
        $stmt->execute($params);
        $locations = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        jsonResponse($locations);
    } catch (Exception $e) {
        error_log("Get locations error: " . $e->getMessage());
        jsonResponse(['error' => 'Failed to fetch locations'], 500);
    }
}

function handleCreateItem($db) {
    $input = $_POST;
    
    // Handle JSON input
    if (empty($_POST) && !empty(file_get_contents('php://input'))) {
        $input = json_decode(file_get_contents('php://input'), true) ?? [];
    }
    
    $required = ['title', 'media_type'];
    foreach ($required as $field) {
        if (empty($input[$field])) {
            jsonResponse(['error' => "Missing required field: $field"], 400);
        }
    }
    
    try {
        $slug = $input['slug'] ?? generateSlug($input['title']);
        $media_url = $input['media_url'] ?? null;
        $file_path = null;
        
        // Handle file upload
        if (!empty($_FILES['media_file'])) {
            $upload_dir = '../uploads/';
            if (!is_dir($upload_dir)) {
                mkdir($upload_dir, 0755, true);
            }
            
            $file_extension = pathinfo($_FILES['media_file']['name'], PATHINFO_EXTENSION);
            $filename = $slug . '.' . $file_extension;
            $file_path = '/uploads/' . $filename;
            
            if (!move_uploaded_file($_FILES['media_file']['tmp_name'], $upload_dir . $filename)) {
                jsonResponse(['error' => 'File upload failed'], 500);
            }
        }
        
        // Validate expiry (max 7 days)
        $expires_at = null;
        if (!empty($input['expires_at'])) {
            $expiry_time = strtotime($input['expires_at']);
            $max_expiry = strtotime('+7 days');
            
            if ($expiry_time > $max_expiry) {
                jsonResponse(['error' => 'Expiry cannot be more than 7 days'], 400);
            }
            $expires_at = date('Y-m-d H:i:s', $expiry_time);
        }
        
        $stmt = $db->prepare("
            INSERT INTO items (slug, title, description, media_type, media_url, file_path, expires_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ");
        
        $stmt->execute([
            $slug,
            sanitizeInput($input['title']),
            sanitizeInput($input['description'] ?? ''),
            $input['media_type'],
            $media_url,
            $file_path,
            $expires_at,
            $input['is_active'] ?? 1
        ]);
        
        jsonResponse(['success' => true, 'slug' => $slug]);
    } catch (PDOException $e) {
        if (strpos($e->getMessage(), 'UNIQUE constraint failed') !== false) {
            jsonResponse(['error' => 'Slug already exists'], 400);
        }
        error_log("Create item error: " . $e->getMessage());
        jsonResponse(['error' => 'Failed to create item'], 500);
    }
}

function handleListItems($db) {
    try {
        $stmt = $db->prepare("SELECT * FROM items ORDER BY created_at DESC");
        $stmt->execute();
        $items = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        jsonResponse($items);
    } catch (Exception $e) {
        error_log("List items error: " . $e->getMessage());
        jsonResponse(['error' => 'Failed to fetch items'], 500);
    }
}

function handleUpdateItem($db) {
    $input = json_decode(file_get_contents('php://input'), true) ?? $_POST;
    
    if (empty($input['slug'])) {
        jsonResponse(['error' => 'Item slug required'], 400);
    }
    
    try {
        // Build dynamic update query
        $updates = [];
        $params = [];
        
        $allowed_fields = ['title', 'description', 'media_type', 'media_url', 'file_path', 'expires_at', 'is_active'];
        foreach ($allowed_fields as $field) {
            if (isset($input[$field])) {
                $updates[] = "$field = ?";
                $params[] = $input[$field];
            }
        }
        
        if (empty($updates)) {
            jsonResponse(['error' => 'No fields to update'], 400);
        }
        
        $params[] = $input['slug'];
        $sql = "UPDATE items SET " . implode(', ', $updates) . " WHERE slug = ?";
        
        $stmt = $db->prepare($sql);
        $stmt->execute($params);
        
        jsonResponse(['success' => true]);
    } catch (Exception $e) {
        error_log("Update item error: " . $e->getMessage());
        jsonResponse(['error' => 'Failed to update item'], 500);
    }
}

function handleDeleteItem($db) {
    $input = json_decode(file_get_contents('php://input'), true) ?? $_POST;
    $slug = $input['slug'] ?? $_GET['slug'] ?? '';
    
    if (empty($slug)) {
        jsonResponse(['error' => 'Item slug required'], 400);
    }
    
    try {
        // Get item to delete associated file
        $stmt = $db->prepare("SELECT file_path FROM items WHERE slug = ?");
        $stmt->execute([$slug]);
        $item = $stmt->fetch(PDO::FETCH_ASSOC);
        
        if ($item && $item['file_path']) {
            $file_path = '../' . ltrim($item['file_path'], '/');
            if (file_exists($file_path)) {
                unlink($file_path);
            }
        }
        
        // Delete from database
        $stmt = $db->prepare("DELETE FROM items WHERE slug = ?");
        $stmt->execute([$slug]);
        
        jsonResponse(['success' => true]);
    } catch (Exception $e) {
        error_log("Delete item error: " . $e->getMessage());
        jsonResponse(['error' => 'Failed to delete item'], 500);
    }
}

function handleCleanup($db) {
    try {
        // Delete locations older than 60 hours (2.5 days)
        $stmt = $db->prepare("DELETE FROM locations WHERE timestamp < datetime('now', '-60 hours')");
        $stmt->execute();
        $locations_count = $stmt->rowCount();

        // Deactivate expired items
        $stmt = $db->prepare("UPDATE items SET is_active = 0 WHERE expires_at < datetime('now') AND is_active = 1");
        $stmt->execute();
        $items_count = $stmt->rowCount();

        jsonResponse([
            'success' => true,
            'locations_deleted' => $locations_count,
            'items_deactivated' => $items_count
        ]);
    } catch (Exception $e) {
        error_log("Cleanup error: " . $e->getMessage());
        jsonResponse(['error' => 'Cleanup failed'], 500);
    }
}
?>
