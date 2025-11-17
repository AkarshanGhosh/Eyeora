// proto1.ino
#include <WiFi.h>
#include <WebServer.h>
#include <EEPROM.h>
#include <DNSServer.h>
#include "esp_camera.h"

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

#define SERVO_PIN_PAN 12
#define SERVO_PIN_TILT 13

#define CAMERA_UID "proto1#firsttest264802"
#define CAMERA_NAME "proto 1"

#define AP_SSID "proto1"
#define AP_PASSWORD "12345678"

#define DNS_PORT 53
IPAddress apIP(192, 168, 4, 1);
DNSServer dnsServer;

#define EEPROM_SIZE 512
#define SSID_ADDR 0
#define PASS_ADDR 100

WebServer server(80);

String wifi_ssid = "";
String wifi_pass = "";
String backend_url = "";

int pan_angle = 90;
int tilt_angle = 90;

camera_config_t camera_config = {
    .pin_pwdn = PWDN_GPIO_NUM,
    .pin_reset = RESET_GPIO_NUM,
    .pin_xclk = XCLK_GPIO_NUM,
    .pin_sscb_sda = SIOD_GPIO_NUM,
    .pin_sscb_scl = SIOC_GPIO_NUM,
    .pin_d7 = Y9_GPIO_NUM,
    .pin_d6 = Y8_GPIO_NUM,
    .pin_d5 = Y7_GPIO_NUM,
    .pin_d4 = Y6_GPIO_NUM,
    .pin_d3 = Y5_GPIO_NUM,
    .pin_d2 = Y4_GPIO_NUM,
    .pin_d1 = Y3_GPIO_NUM,
    .pin_d0 = Y2_GPIO_NUM,
    .pin_vsync = VSYNC_GPIO_NUM,
    .pin_href = HREF_GPIO_NUM,
    .pin_pclk = PCLK_GPIO_NUM,
    .xclk_freq_hz = 20000000,
    .ledc_timer = LEDC_TIMER_0,
    .ledc_channel = LEDC_CHANNEL_0,
    .pixel_format = PIXFORMAT_JPEG,
    .frame_size = FRAMESIZE_VGA,
    .jpeg_quality = 12,
    .fb_count = 1
};

void setup() {
    Serial.begin(115200);
    Serial.println("\n\n🎥 ESP32-CAM Proto1 Starting...");
    
    EEPROM.begin(EEPROM_SIZE);
    
    wifi_ssid = readEEPROM(SSID_ADDR);
    wifi_pass = readEEPROM(PASS_ADDR);
    
    if (wifi_ssid.length() > 0) {
        Serial.println("📡 Saved WiFi: " + wifi_ssid);
    }
    
    setupServos();
    
    if (esp_camera_init(&camera_config) != ESP_OK) {
        Serial.println("❌ Camera init failed");
        return;
    }
    Serial.println("✅ Camera initialized");
    
    if (wifi_ssid.length() > 0) {
        connectWiFi();
    }
    
    if (WiFi.status() != WL_CONNECTED) {
        startAPMode();
    } else {
        startCameraMode();
    }
}

void loop() {
    if (WiFi.getMode() == WIFI_AP) {
        dnsServer.processNextRequest();
    }
    
    server.handleClient();
    
    if (WiFi.status() != WL_CONNECTED && WiFi.getMode() == WIFI_STA) {
        Serial.println("⚠️ Lost connection, switching to AP");
        startAPMode();
    }
}

void setupServos() {
    ledcAttach(SERVO_PIN_PAN, 50, 16);
    ledcAttach(SERVO_PIN_TILT, 50, 16);
    
    setServoAngle(SERVO_PIN_PAN, 90);
    setServoAngle(SERVO_PIN_TILT, 90);
    
    Serial.println("✅ Servos initialized at 90°");
}

void setServoAngle(int pin, int angle) {
    angle = constrain(angle, 0, 180);
    int dutyCycle = map(angle, 0, 180, 3277, 6554);
    ledcWrite(pin, dutyCycle);
}

void connectWiFi() {
    Serial.println("📡 Connecting to: " + wifi_ssid);
    WiFi.mode(WIFI_STA);
    WiFi.begin(wifi_ssid.c_str(), wifi_pass.c_str());
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n✅ Connected!");
        Serial.println("📍 IP: " + WiFi.localIP().toString());
        discoverBackend();
    } else {
        Serial.println("\n❌ Connection failed");
    }
}

void discoverBackend() {
    Serial.println("\n🔍 Discovering backend server...");
    
    IPAddress localIP = WiFi.localIP();
    String subnet = "";
    
    for (int i = 0; i < 3; i++) {
        subnet += String(localIP[i]) + ".";
    }
    
    String possibleBackends[] = {
        "http://" + subnet + "34:8000",
        "http://192.168.50.34:8000",
        "http://192.168.97.12:8000",
        "http://" + subnet + "1:8000"
    };
    
    for (int i = 0; i < 4; i++) {
        if (pingBackend(possibleBackends[i])) {
            backend_url = possibleBackends[i];
            Serial.println("✅ Backend found: " + backend_url);
            return;
        }
    }
    
    backend_url = "http://192.168.50.34:8000";
    Serial.println("⚠️ Using fallback: " + backend_url);
}

bool pingBackend(String url) {
    WiFiClient client;
    
    int portStart = url.lastIndexOf(":");
    int hostStart = url.indexOf("//") + 2;
    String host = url.substring(hostStart, portStart);
    int port = url.substring(portStart + 1).toInt();
    
    Serial.print("  Trying " + host + ":" + String(port) + "... ");
    
    if (client.connect(host.c_str(), port, 2000)) {
        client.println("GET /health HTTP/1.1");
        client.println("Host: " + host);
        client.println("Connection: close");
        client.println();
        
        unsigned long timeout = millis();
        while (client.available() == 0) {
            if (millis() - timeout > 2000) {
                Serial.println("timeout");
                client.stop();
                return false;
            }
        }
        
        String response = client.readStringUntil('\n');
        client.stop();
        
        if (response.indexOf("200") >= 0) {
            Serial.println("OK");
            return true;
        }
    }
    
    Serial.println("failed");
    return false;
}

void startAPMode() {
    Serial.println("\n📡 Starting AP Mode");
    WiFi.mode(WIFI_AP);
    WiFi.softAPConfig(apIP, apIP, IPAddress(255, 255, 255, 0));
    WiFi.softAP(AP_SSID, AP_PASSWORD);
    
    Serial.println("✅ AP Started");
    Serial.println("   SSID: " + String(AP_SSID));
    Serial.println("   Password: " + String(AP_PASSWORD));
    Serial.println("   IP: " + WiFi.softAPIP().toString());
    
    dnsServer.start(DNS_PORT, "*", apIP);
    
    server.on("/", handleConfigPage);
    server.on("/generate_204", handleConfigPage);
    server.on("/fwlink", handleConfigPage);
    server.on("/hotspot-detect.html", handleConfigPage);
    server.on("/save", HTTP_POST, handleSaveConfig);
    server.onNotFound(handleConfigPage);
    
    server.begin();
    Serial.println("✅ Captive portal active");
}

void startCameraMode() {
    Serial.println("\n🎥 Starting Camera Mode");
    Serial.println("   IP: " + WiFi.localIP().toString());
    
    server.on("/", handleRoot);
    server.on("/stream", handleStream);
    server.on("/servo", HTTP_GET, handleServo);
    server.on("/status", handleStatus);
    server.begin();
    Serial.println("✅ Camera server running");
    
    registerWithBackend();
}

void handleRoot() {
    String html = "<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>";
    html += "<style>body{font-family:Arial;padding:20px;background:#0f172a;color:#fff;text-align:center}";
    html += "h1{color:#38bdf8}img{max-width:100%;border:2px solid #38bdf8;border-radius:8px;margin-top:20px}</style></head>";
    html += "<body><h1>🎥 Proto1 Camera</h1>";
    html += "<p>UID: <code>" + String(CAMERA_UID) + "</code></p>";
    html += "<p>Backend: <code>" + backend_url + "</code></p>";
    html += "<p style='color:#10b981'>● Online</p>";
    html += "<img src='/stream' alt='Camera Stream'>";
    html += "</body></html>";
    
    server.send(200, "text/html", html);
}

void handleConfigPage() {
    String html = "<!DOCTYPE html><html><head>";
    html += "<meta name='viewport' content='width=device-width,initial-scale=1'>";
    html += "<style>body{font-family:Arial;padding:20px;background:#0f172a;color:#fff;text-align:center}";
    html += "input,button{width:80%;max-width:400px;padding:12px;margin:10px 0;border-radius:5px;border:none;font-size:16px}";
    html += "input{background:#1e293b;color:#fff;border:1px solid #38bdf8}";
    html += "button{background:#38bdf8;cursor:pointer;font-weight:bold;color:#0f172a}";
    html += "h1{color:#38bdf8}.info{color:#94a3b8;margin:20px 0}</style></head>";
    html += "<body><h1>🎥 Proto1 Setup</h1>";
    html += "<p class='info'>Connect Proto1 to WiFi</p>";
    html += "<form action='/save' method='post'>";
    html += "<input name='ssid' placeholder='WiFi Network Name' required>";
    html += "<input name='pass' type='password' placeholder='WiFi Password' required>";
    html += "<button type='submit'>Connect</button>";
    html += "</form>";
    html += "<p class='info' style='font-size:12px;margin-top:30px'>Backend server will be auto-detected</p>";
    html += "</body></html>";
    
    server.send(200, "text/html", html);
}

void handleSaveConfig() {
    wifi_ssid = server.arg("ssid");
    wifi_pass = server.arg("pass");
    
    Serial.println("\n💾 Saving configuration...");
    Serial.println("   SSID: " + wifi_ssid);
    
    writeEEPROM(SSID_ADDR, wifi_ssid);
    writeEEPROM(PASS_ADDR, wifi_pass);
    EEPROM.commit();
    
    String html = "<!DOCTYPE html><html><head><style>body{font-family:Arial;padding:20px;background:#0f172a;color:#fff;text-align:center}";
    html += "h1{color:#38bdf8}.spinner{border:4px solid #1e293b;border-top:4px solid #38bdf8;";
    html += "border-radius:50%;width:50px;height:50px;animation:spin 1s linear infinite;margin:20px auto}";
    html += "@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}</style></head>";
    html += "<body><h1>✅ Saved</h1>";
    html += "<div class='spinner'></div>";
    html += "<p>Connecting to " + wifi_ssid + "...</p>";
    html += "</body></html>";
    
    server.send(200, "text/html", html);
    delay(3000);
    ESP.restart();
}

void handleStream() {
    WiFiClient client = server.client();
    
    client.println("HTTP/1.1 200 OK");
    client.println("Content-Type: multipart/x-mixed-replace; boundary=frame");
    client.println("Connection: close");
    client.println();
    
    while (client.connected()) {
        camera_fb_t *fb = esp_camera_fb_get();
        if (!fb) continue;
        
        client.println("--frame");
        client.println("Content-Type: image/jpeg");
        client.printf("Content-Length: %d\r\n\r\n", fb->len);
        client.write(fb->buf, fb->len);
        client.println();
        
        esp_camera_fb_return(fb);
    }
}

void handleServo() {
    if (server.hasArg("pan")) {
        pan_angle = server.arg("pan").toInt();
        setServoAngle(SERVO_PIN_PAN, pan_angle);
    }
    
    if (server.hasArg("tilt")) {
        tilt_angle = server.arg("tilt").toInt();
        setServoAngle(SERVO_PIN_TILT, tilt_angle);
    }
    
    server.send(200, "application/json", "{\"pan\":" + String(pan_angle) + ",\"tilt\":" + String(tilt_angle) + "}");
}

void handleStatus() {
    String json = "{\"uid\":\"" + String(CAMERA_UID) + "\",\"name\":\"" + String(CAMERA_NAME) + "\",";
    json += "\"ip\":\"" + WiFi.localIP().toString() + "\",\"rssi\":" + String(WiFi.RSSI()) + ",";
    json += "\"backend\":\"" + backend_url + "\"}";
    server.send(200, "application/json", json);
}

void registerWithBackend() {
    if (backend_url.length() == 0) return;
    
    Serial.println("\n📡 Registering with backend...");
    
    WiFiClient client;
    int portStart = backend_url.lastIndexOf(":");
    int hostStart = backend_url.indexOf("//") + 2;
    String host = backend_url.substring(hostStart, portStart);
    int port = backend_url.substring(portStart + 1).toInt();
    
    if (client.connect(host.c_str(), port)) {
        String postData = "uid=" + String(CAMERA_UID) + "&name=" + String(CAMERA_NAME) + "&ip=" + WiFi.localIP().toString();
        
        client.println("POST /api/cameras/register HTTP/1.1");
        client.println("Host: " + host);
        client.println("Content-Type: application/x-www-form-urlencoded");
        client.println("Content-Length: " + String(postData.length()));
        client.println();
        client.print(postData);
        
        Serial.println("✅ Registration sent");
        client.stop();
    } else {
        Serial.println("❌ Registration failed");
    }
}

String readEEPROM(int addr) {
    String data = "";
    char ch = EEPROM.read(addr);
    int i = 0;
    while (ch != '\0' && i < 100) {
        data += ch;
        i++;
        ch = EEPROM.read(addr + i);
    }
    return data;
}

void writeEEPROM(int addr, String data) {
    for (int i = 0; i < data.length(); i++) {
        EEPROM.write(addr + i, data[i]);
    }
    EEPROM.write(addr + data.length(), '\0');
}