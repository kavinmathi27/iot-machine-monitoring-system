#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <DHT.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

#define DHTPIN 4
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);
Adafruit_MPU6050 mpu;

const char* ssid = "Wokwi-GUEST";
const char* password = "";
const char* serverURL = "http://10.178.253.192/push";

void setup() {
  Serial.begin(115200);
  dht.begin();
  Wire.begin(21, 22);

  if (!mpu.begin()) {
    Serial.println("MPU6050 not detected");
    while (1);
  }

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected");
}

void loop() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("DHT read failed");
    delay(2000);
    return;
  }

  sensors_event_t accel, gyro, temp;
  mpu.getEvent(&accel, &gyro, &temp);

  float vibration = sqrt(
    accel.acceleration.x * accel.acceleration.x +
    accel.acceleration.y * accel.acceleration.y +
    accel.acceleration.z * accel.acceleration.z
  );

  Serial.printf("Temp: %.1f | Hum: %.1f | Vib: %.2f\n",
                temperature, humidity, vibration);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");

    String payload = "{";
    payload += "\"temperature\":" + String(temperature,1) + ",";
    payload += "\"humidity\":" + String(humidity,1) + ",";
    payload += "\"vibration\":" + String(vibration,2) + ",";
    payload += "\"status\":\"RUNNING\"}";
    
    http.POST(payload);
    http.end();
  }

  delay(5000);
}
