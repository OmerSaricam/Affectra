/*
 * ESP32-CAM Video Streaming Server for Affectra
 * This code sets up a simple HTTP server on ESP32-CAM to stream JPEG images
 * that can be consumed by the Affectra emotion tracking application.
 */

#include "esp_camera.h"
#include <WiFi.h>
#include "esp_timer.h"
#include "img_converters.h"
#include "fb_gfx.h"
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
#include "esp_http_server.h"

// Pin definitions for AI Thinker ESP32-CAM module
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Web server port
#define WEB_SERVER_PORT 80

// Frame rate control
#define FRAME_RATE_LIMIT_MS 100  // Minimum time between frames (10 fps)
uint32_t last_frame_time = 0;

// LED control
#define FLASH_LED_PIN 4
bool led_state = false;

// Basic HTTP authentication (optional)
// Set both to empty strings to disable authentication
const char* http_username = "";
const char* http_password = "";

typedef struct {
    httpd_req_t *req;
    size_t len;
} jpg_chunking_t;

// Forward declarations
void startCameraServer();
void setup_wifi();
void setup_camera();

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();
  Serial.println("ESP32-CAM Video Streaming Server for Affectra");
  
  // Disable brownout detector
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);
  
  // Initialize flash LED pin as output
  pinMode(FLASH_LED_PIN, OUTPUT);
  digitalWrite(FLASH_LED_PIN, 0);  // Turn off flash
  
  // Setup camera
  setup_camera();
  
  // Connect to WiFi
  setup_wifi();
  
  // Start HTTP server for video streaming
  startCameraServer();
  
  Serial.print("Camera Ready! Use 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("' to connect");
}

void loop() {
  // Nothing to do here - everything is handled by the HTTP server
  delay(10000);
}

void setup_wifi() {
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  // Wait for connection
  int timeout_counter = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    
    // Blink LED while connecting
    led_state = !led_state;
    digitalWrite(FLASH_LED_PIN, led_state);
    
    // Timeout after 20 seconds, restart ESP
    timeout_counter++;
    if (timeout_counter >= 40) {
      Serial.println("\nWiFi connection failed! Restarting...");
      ESP.restart();
    }
  }
  
  // Turn off LED once connected
  digitalWrite(FLASH_LED_PIN, 0);
  Serial.println("\nWiFi connected");
}

void setup_camera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  // Initial settings
  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA;  // 640x480
    config.jpeg_quality = 10;           // 0-63, lower is higher quality
    config.fb_count = 2;                // Number of frame buffers
  } else {
    config.frame_size = FRAMESIZE_SVGA; // 800x600
    config.jpeg_quality = 12;           // Lower quality due to memory constraints
    config.fb_count = 1;                // Only one frame buffer
  }
  
  // Initialize camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    ESP.restart();
  }
  
  // Camera sensor settings
  sensor_t * s = esp_camera_sensor_get();
  // Adjusting for better image quality
  s->set_brightness(s, 1);      // -2 to 2
  s->set_contrast(s, 0);        // -2 to 2
  s->set_saturation(s, 0);      // -2 to 2
  s->set_special_effect(s, 0);  // 0 = No Effect, 1 = Negative, etc.
  s->set_whitebal(s, 1);        // 0 = disable, 1 = enable
  s->set_awb_gain(s, 1);        // 0 = disable, 1 = enable
  s->set_wb_mode(s, 0);         // 0 auto
  s->set_exposure_ctrl(s, 1);   // 0 = disable, 1 = enable
  s->set_aec2(s, 0);            // 0 = disable, 1 = enable
  s->set_gain_ctrl(s, 1);       // 0 = disable, 1 = enable
  s->set_agc_gain(s, 0);        // 0 to 30
  s->set_gainceiling(s, (gainceiling_t)0); // 0 to 6
  s->set_bpc(s, 0);             // 0 = disable, 1 = enable
  s->set_wpc(s, 1);             // 0 = disable, 1 = enable
  s->set_raw_gma(s, 1);         // 0 = disable, 1 = enable
  s->set_lenc(s, 1);            // 0 = disable, 1 = enable
  s->set_hmirror(s, 0);         // 0 = disable, 1 = enable
  s->set_vflip(s, 0);           // 0 = disable, 1 = enable
  s->set_dcw(s, 1);             // 0 = disable, 1 = enable
  s->set_colorbar(s, 0);        // 0 = disable, 1 = enable
}

// Handler for / root web page
static esp_err_t root_handler(httpd_req_t *req) {
  httpd_resp_set_type(req, "text/html");
  
  // Simple HTML with JavaScript to show the stream and controls
  const char *html = "<!DOCTYPE html>\n"
    "<html>\n"
    "<head>\n"
    "  <title>ESP32-CAM Streaming for Affectra</title>\n"
    "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
    "  <style>\n"
    "    body { font-family: Arial, sans-serif; text-align: center; margin: 0px auto; padding: 10px; }\n"
    "    img { max-width: 100%; width: auto; height: auto; }\n"
    "    .button {\n"
    "      background-color: #4CAF50; border: none; color: white;\n"
    "      padding: 10px 20px; text-align: center; border-radius: 5px;\n"
    "      margin: 10px 5px; cursor: pointer;\n"
    "    }\n"
    "    .button.flash { background-color: #f44336; }\n"
    "    .button.quality { background-color: #2196F3; }\n"
    "    .button:hover { opacity: 0.8; }\n"
    "    .stream-container { margin-top: 15px; }\n"
    "  </style>\n"
    "</head>\n"
    "<body>\n"
    "  <h1>ESP32-CAM Streaming for Affectra</h1>\n"
    "  <div>\n"
    "    <button class=\"button flash\" onclick=\"toggleFlash()\">Toggle Flash</button>\n"
    "    <button class=\"button quality\" onclick=\"toggleQuality()\">Toggle Quality</button>\n"
    "  </div>\n"
    "  <div class=\"stream-container\">\n"
    "    <img src=\"/stream\" id=\"stream\">\n"
    "  </div>\n"
    "  <p>Stream URL (use this in Affectra): <br><code>http://" + String(WiFi.localIP().toString()) + "/stream</code></p>\n"
    "  <script>\n"
    "    function toggleFlash() {\n"
    "      fetch('/control?cmd=flash').then(response => response.text())\n"
    "        .then(data => console.log(data));\n"
    "    }\n"
    "    function toggleQuality() {\n"
    "      fetch('/control?cmd=quality').then(response => response.text())\n"
    "        .then(data => console.log(data));\n"
    "    }\n"
    "  </script>\n"
    "</body>\n"
    "</html>\n";
  
  return httpd_resp_send(req, html, strlen(html));
}

// Control handler for flash LED and quality settings
static esp_err_t control_handler(httpd_req_t *req) {
  char *buf;
  size_t buf_len;
  char cmd[32] = {0,};
  
  buf_len = httpd_req_get_url_query_len(req) + 1;
  if (buf_len > 1) {
    buf = (char *)malloc(buf_len);
    if (!buf) {
      httpd_resp_send_500(req);
      return ESP_FAIL;
    }
    if (httpd_req_get_url_query_str(req, buf, buf_len) == ESP_OK) {
      if (httpd_query_key_value(buf, "cmd", cmd, sizeof(cmd)) == ESP_OK) {
        // Flash control
        if (!strcmp(cmd, "flash")) {
          led_state = !led_state;
          digitalWrite(FLASH_LED_PIN, led_state);
          httpd_resp_set_type(req, "text/plain");
          httpd_resp_sendstr(req, led_state ? "Flash ON" : "Flash OFF");
        }
        // Quality control
        else if (!strcmp(cmd, "quality")) {
          sensor_t *s = esp_camera_sensor_get();
          int current_quality = s->status.quality;
          // Toggle between high and low quality
          if (current_quality > 15) {
            s->set_quality(s, 10); // High quality
          } else {
            s->set_quality(s, 30); // Lower quality, faster streaming
          }
          httpd_resp_set_type(req, "text/plain");
          httpd_resp_sendstr(req, (current_quality > 15) ? "Higher Quality" : "Lower Quality");
        }
        else {
          httpd_resp_send_404(req);
        }
      } else {
        httpd_resp_send_404(req);
      }
    } else {
      httpd_resp_send_404(req);
    }
    free(buf);
  } else {
    httpd_resp_send_404(req);
  }
  return ESP_OK;
}

// Callback function for sending JPEG chunks
static size_t jpg_encode_stream(void *arg, size_t index, const void *data, size_t len) {
  jpg_chunking_t *j = (jpg_chunking_t *)arg;
  if (!index) {
    j->len = 0;
  }
  if (httpd_resp_send_chunk(j->req, (const char *)data, len) != ESP_OK) {
    return 0;
  }
  j->len += len;
  return len;
}

// Handler for video streaming
static esp_err_t stream_handler(httpd_req_t *req) {
  camera_fb_t *fb = NULL;
  esp_err_t res = ESP_OK;
  size_t _jpg_buf_len = 0;
  uint8_t *_jpg_buf = NULL;
  char *part_buf[64];
  static int64_t last_frame = 0;
  
  // Set response headers
  httpd_resp_set_type(req, "multipart/x-mixed-replace; boundary=frame");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  
  // Check for HTTP authentication if required
  if (strlen(http_username) > 0 && strlen(http_password) > 0) {
    if (!httpd_req_get_hdr_value_str(req, "Authorization", (char *)part_buf, sizeof(part_buf))) {
      httpd_resp_set_status(req, "401 Unauthorized");
      httpd_resp_set_hdr(req, "WWW-Authenticate", "Basic realm=\"ESP32-CAM\"");
      return httpd_resp_send(req, NULL, 0);
    }
    
    // TODO: Add basic authentication validation here if needed
  }
  
  // Main video streaming loop
  while (true) {
    uint32_t current_time = millis();
    if (current_time - last_frame_time < FRAME_RATE_LIMIT_MS) {
      // Limit frame rate
      delay(1);
      continue;
    }
    last_frame_time = current_time;
    
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      res = ESP_FAIL;
      break;
    }
    
    // If frame is already JPEG, send it directly
    if (fb->format == PIXFORMAT_JPEG) {
      // Define the HTTP boundary and content headers for multipart
      const char *boundary = "--frame\r\n"
                            "Content-Type: image/jpeg\r\n"
                            "Content-Length: %u\r\n\r\n";
      
      uint32_t hlen = snprintf((char *)part_buf, sizeof(part_buf), boundary, fb->len);
      res = httpd_resp_send_chunk(req, (const char *)part_buf, hlen);
      
      if (res == ESP_OK) {
        res = httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len);
      }
      if (res == ESP_OK) {
        res = httpd_resp_send_chunk(req, "\r\n", 2);
      }
    } else {
      // Convert non-JPEG frame to JPEG
      jpg_chunking_t jchunk = {req, 0};
      res = frame2jpg_cb(fb, 80, jpg_encode_stream, &jchunk) ? ESP_OK : ESP_FAIL;
      httpd_resp_send_chunk(req, "\r\n", 2);
    }
    
    // Release the frame buffer
    esp_camera_fb_return(fb);
    
    // Check if client disconnected
    if (res != ESP_OK) {
      break;
    }
  }
  
  return res;
}

void startCameraServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = WEB_SERVER_PORT;
  config.max_uri_handlers = 16;
  config.stack_size = 8192;
  
  httpd_uri_t index_uri = {
    .uri       = "/",
    .method    = HTTP_GET,
    .handler   = root_handler,
    .user_ctx  = NULL
  };
  
  httpd_uri_t stream_uri = {
    .uri       = "/stream",
    .method    = HTTP_GET,
    .handler   = stream_handler,
    .user_ctx  = NULL
  };
  
  httpd_uri_t control_uri = {
    .uri       = "/control",
    .method    = HTTP_GET,
    .handler   = control_handler,
    .user_ctx  = NULL
  };
  
  httpd_handle_t server = NULL;
  
  if (httpd_start(&server, &config) == ESP_OK) {
    httpd_register_uri_handler(server, &index_uri);
    httpd_register_uri_handler(server, &stream_uri);
    httpd_register_uri_handler(server, &control_uri);
    Serial.println("HTTP server started");
  } else {
    Serial.println("Failed to start HTTP server");
  }
} 