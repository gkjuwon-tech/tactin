// TACTIN arm firmware — ESP32 + 5x Feetech STS3215 serial-bus servos + vacuum pickup.
//
// Speaks the line protocol used by tactin.arm.driver.SerialDriver over USB:
//
//   M b s e w r f   move joints to angles (degrees), f = feedrate (mm/s, advisory)
//   V 1 | V 0       vacuum solenoid + pump on / off
//   H               move to the home pose
//
// Every accepted command is acknowledged with "ok\n"; malformed input replies
// "err\n". Joint angles are clamped to per-servo limits before being sent.
//
// Wiring (reference build):
//   - STS3215 bus  -> Serial2 (half-duplex TTL) on GPIO16(RX)/GPIO17(TX)
//   - Vacuum pump MOSFET gate -> GPIO25
//   - Solenoid valve MOSFET gate -> GPIO26  (vents the nozzle to drop parts fast)
//   - Servo bus and pump share a 6-12V supply; ESP32 powered over USB.

#include <Arduino.h>
#include <SCServo.h>  // Feetech STS/SMS serial-bus servo library

static const uint8_t NUM_JOINTS = 5;
static const uint8_t SERVO_ID[NUM_JOINTS] = {1, 2, 3, 4, 5};

// Degrees at servo "centre" (tick 2048) for each joint, so the firmware and the
// Python kinematics agree on what 0 rad means at each joint.
static const float JOINT_OFFSET_DEG[NUM_JOINTS] = {0.0, 90.0, 0.0, -90.0, 0.0};
static const float JOINT_MIN_DEG[NUM_JOINTS]    = {-180, -15, -160, -120, -180};
static const float JOINT_MAX_DEG[NUM_JOINTS]    = { 180, 195,  160,  120,  180};
static const float HOME_DEG[NUM_JOINTS]         = {0.0, 90.0, 0.0, -90.0, 0.0};

static const int PIN_PUMP     = 25;
static const int PIN_SOLENOID = 26;

// STS3215: 4096 ticks over 360 degrees.
static const float TICKS_PER_DEG = 4096.0f / 360.0f;
static const int   TICK_CENTRE   = 2048;

SMS_STS servos;

static float clampf(float v, float lo, float hi) {
  return v < lo ? lo : (v > hi ? hi : v);
}

static int degToTicks(uint8_t j, float deg) {
  deg = clampf(deg, JOINT_MIN_DEG[j], JOINT_MAX_DEG[j]);
  return TICK_CENTRE + (int)lroundf((deg - JOINT_OFFSET_DEG[j]) * TICKS_PER_DEG);
}

static void moveJoints(const float deg[NUM_JOINTS], float feed_mm_s) {
  // Map the advisory Cartesian feedrate to a per-servo speed (ticks/s).
  int speed = (int)clampf(feed_mm_s * 12.0f, 200.0f, 3400.0f);
  for (uint8_t j = 0; j < NUM_JOINTS; j++) {
    servos.WritePosEx(SERVO_ID[j], degToTicks(j, deg[j]), speed, 50);
  }
}

static void setVacuum(bool on) {
  digitalWrite(PIN_PUMP, on ? HIGH : LOW);
  digitalWrite(PIN_SOLENOID, on ? LOW : HIGH);  // energize valve to vent on release
}

void setup() {
  Serial.begin(115200);
  Serial2.begin(1000000, SERIAL_8N1, 16, 17);
  servos.pSerial = &Serial2;
  pinMode(PIN_PUMP, OUTPUT);
  pinMode(PIN_SOLENOID, OUTPUT);
  setVacuum(false);
}

static bool handleLine(const String& line) {
  if (line.length() == 0) return true;
  char cmd = line.charAt(0);

  if (cmd == 'H') {
    moveJoints(HOME_DEG, 80.0f);
    return true;
  }
  if (cmd == 'V') {
    setVacuum(line.indexOf('1') >= 0);
    return true;
  }
  if (cmd == 'M') {
    float deg[NUM_JOINTS];
    float feed = 100.0f;
    int parsed = sscanf(line.c_str(), "M %f %f %f %f %f %f",
                        &deg[0], &deg[1], &deg[2], &deg[3], &deg[4], &feed);
    if (parsed < NUM_JOINTS) return false;
    moveJoints(deg, feed);
    return true;
  }
  return false;
}

void loop() {
  static String buffer;
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n') {
      buffer.trim();
      Serial.println(handleLine(buffer) ? "ok" : "err");
      buffer = "";
    } else if (c != '\r') {
      buffer += c;
    }
  }
}
