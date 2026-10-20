/*  
 ESP32-S3 Gemini Bridge Client para Omni.AI
   
 Este código conecta el ESP32-S3 a tu red Wi-Fi local y envía un prompt  
 en formato JSON al servidor puente en tu PC: {"prompt": "Hola Gemini"}  
 Recibe la respuesta: {"response": "..."} y la muestra en el monitor serial.  
*/  
  
#include <WiFi.h>  
#include <HTTPClient.h>  
  
// Reemplaza con los datos de tu red Wi-Fi  
const char* ssid = "TU_RED_WIFI";  
const char* password = "TU_PASSWORD_WIFI";  
  
// Reemplaza con la IP que muestra la consola de Python al ejecutar server.py  
// URL de tu servidor puente (IP local detectada de tu PC)  
const char* serverUrl = "http://172.20.10.11:8000/chat";  
  
void sendPromptToGemini(String promptText) {  
  if (WiFi.status() == WL_CONNECTED) {  
    HTTPClient http;  
    http.begin(serverUrl);  
    http.addHeader("Content-Type", "application/json");  
  
    // Construcción del JSON {"prompt": "..."}  
    String jsonPayload = "{\"prompt\":\"" + promptText + "\"}";  
  
    Serial.println("\n[ESP32] Enviando a Gemini...");  
    Serial.println("Payload: " + jsonPayload);  
  
    int httpResponseCode = http.POST(jsonPayload);  
  
    if (httpResponseCode > 0) {  
      String response = http.getString();  
      Serial.print("[ESP32] Código HTTP: ");  
      Serial.println(httpResponseCode);  
      Serial.println("[ESP32] Respuesta recibida:");  
      Serial.println(response);  
    } else {  
      Serial.print("[ESP32] Error en la petición HTTP: ");  
      Serial.println(httpResponseCode);  
    }  
  
    http.end();  
  } else {  
    Serial.println("[ESP32] Error: Desconectado de Wi-Fi");  
  }  
}  
  
void setup() {  
  Serial.begin(115200);  
  delay(1000);  
  
  Serial.println("\nConectando a Wi-Fi...");  
  WiFi.begin(ssid, password);  
  
  while (WiFi.status() != WL_CONNECTED) {  
    delay(500);  
    Serial.print(".");  
  }  
  
  Serial.println("\nConectado con éxito a Wi-Fi!");  
  Serial.print("IP del ESP32: ");  
  Serial.println(WiFi.localIP());  
  
  // Prueba inicial enviando un mensaje a Gemini  
  sendPromptToGemini("Hola Gemini, soy un ESP32-S3. Responde en una sola frase breve.");  
}  
  
void loop() {  
  // Aquí puedes enviar lecturas de sensores o activar prompts mediante botones  
  delay(10000);  
}
