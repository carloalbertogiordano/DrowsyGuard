#include <unity.h>
#include "aes_decrypt.h"
#include <cstring>

void setUp(void) {}
void tearDown(void) {}

// Vettore di test generato con SecurityManager.encrypt_data() lato Python
// (chiave di TEST dedicata, mai la chiave reale del progetto -- vedi
// security/key.py, quella non va mai in un file committato).
// Verifica l'interoperabilita' Python <-> C++ dello schema AES-256-CBC.

void test_decrypts_known_payload(void) {
    const uint8_t* key = (const uint8_t*)"0123456789ABCDEF0123456789ABCDEF";
    const char* base64_payload =
        "6LrTeum1xGVB7Oxc8IItvbuJ6UE1AuN87cGiMSy4a/kuF1Nj24+WdrTOPoKvKXoEtDQALRW0UF7wvSWyemLf4LiTXqUb7JQ8BCAr7UREvFmfuHPQVgWF+0EzvawlSM/g+CxJBN+ZNWypiHgtyexjCQ==";
    const char* expected =
        "{\"status\": \"DROWSY_DETECTED\", \"timestamp\": \"2026-01-01 00:00:00\", \"probability\": 0.99}";

    char out_buffer[256] = {0};
    int len = aes_decrypt(base64_payload, key, out_buffer, sizeof(out_buffer));

    TEST_ASSERT_EQUAL_INT(86, len);
    TEST_ASSERT_EQUAL_STRING(expected, out_buffer);
}

void test_returns_negative_on_buffer_too_small(void) {
    const uint8_t* key = (const uint8_t*)"0123456789ABCDEF0123456789ABCDEF";
    const char* base64_payload =
        "6LrTeum1xGVB7Oxc8IItvbuJ6UE1AuN87cGiMSy4a/kuF1Nj24+WdrTOPoKvKXoEtDQALRW0UF7wvSWyemLf4LiTXqUb7JQ8BCAr7UREvFmfuHPQVgWF+0EzvawlSM/g+CxJBN+ZNWypiHgtyexjCQ==";

    char out_buffer[4];  // troppo piccolo per contenere il risultato
    int len = aes_decrypt(base64_payload, key, out_buffer, sizeof(out_buffer));

    TEST_ASSERT_EQUAL_INT(-1, len);
}

int main(int argc, char** argv) {
    UNITY_BEGIN();
    RUN_TEST(test_decrypts_known_payload);
    RUN_TEST(test_returns_negative_on_buffer_too_small);
    return UNITY_END();
}
