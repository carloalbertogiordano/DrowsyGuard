#include <unity.h>
#include "telemetry_handler.h"
#include "MockBuzzer.h"

// --- fixture: recreated for each test by setUp() ---
MockBuzzer* mock_buzzer;
TelemetryHandler* handler;

void setUp(void) {
    mock_buzzer = new MockBuzzer();
    handler = new TelemetryHandler(*mock_buzzer, 2000);  // 2000ms timeout
}

void tearDown(void) {
    delete handler;
    delete mock_buzzer;
}

// --- test cases ---

void test_buzzer_starts_on_drowsy_message(void) {
    const char* json = "{\"status\":\"DROWSY_DETECTED\",\"timestamp\":\"t\",\"probability\":0.9}";

    handler->onMessage(json, 1000);

    TEST_ASSERT_EQUAL_INT(1, mock_buzzer->start_calls);
    TEST_ASSERT_TRUE(mock_buzzer->is_running);
}

void test_buzzer_does_not_restart_if_already_active(void) {
    const char* json = "{\"status\":\"DROWSY_DETECTED\",\"timestamp\":\"t\",\"probability\":0.9}";

    handler->onMessage(json, 1000);
    handler->onMessage(json, 1100);  // second message, shortly after

    TEST_ASSERT_EQUAL_INT(1, mock_buzzer->start_calls);  // not called again
}

void test_buzzer_stops_after_timeout_via_update(void) {
    const char* json = "{\"status\":\"DROWSY_DETECTED\",\"timestamp\":\"t\",\"probability\":0.9}";

    handler->onMessage(json, 1000);
    handler->update(2999);  // still within the timeout (2000ms from 1000)
    TEST_ASSERT_TRUE(mock_buzzer->is_running);

    handler->update(3001);  // timeout exceeded
    TEST_ASSERT_FALSE(mock_buzzer->is_running);
    TEST_ASSERT_EQUAL_INT(1, mock_buzzer->stop_calls);
}

void test_ignores_message_without_drowsy_status(void) {
    const char* json = "{\"status\":\"OK\",\"timestamp\":\"t\",\"probability\":0.1}";

    handler->onMessage(json, 1000);

    TEST_ASSERT_EQUAL_INT(0, mock_buzzer->start_calls);
}

// Real bug risk found via coverage review: valid JSON with no "status" key
// makes jdoc["status"] return nullptr, and strncmp(nullptr, ...) is
// undefined behavior (likely a crash on real hardware). Decryption always
// produces a "status" field in normal operation, but malformed/garbage
// input reaching this point should never crash the board. This test only
// passes once onMessage() null-checks status before strncmp.
void test_does_not_crash_on_json_without_status_field(void) {
    const char* json = "{\"timestamp\":\"t\",\"probability\":0.9}";

    handler->onMessage(json, 1000);

    TEST_ASSERT_EQUAL_INT(0, mock_buzzer->start_calls);
}

int main(int argc, char** argv) {
    UNITY_BEGIN();
    RUN_TEST(test_buzzer_starts_on_drowsy_message);
    RUN_TEST(test_buzzer_does_not_restart_if_already_active);
    RUN_TEST(test_buzzer_stops_after_timeout_via_update);
    RUN_TEST(test_ignores_message_without_drowsy_status);
    RUN_TEST(test_does_not_crash_on_json_without_status_field);
    return UNITY_END();
}
