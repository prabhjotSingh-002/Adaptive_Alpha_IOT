#include <stdio.h>
#include <string.h>
#include <assert.h>
#include "speck.h"
#include "present.h"

int main() {
    printf("--- Testing Speck 64/128 Test Vector ---\n");
    // Official NSA Test Vector
    // Key: 1b1a1918 13121110 0b0a0908 03020100
    uint8_t speck_k[16] = {
        0x00, 0x01, 0x02, 0x03, 0x08, 0x09, 0x0a, 0x0b,
        0x10, 0x11, 0x12, 0x13, 0x18, 0x19, 0x1a, 0x1b
    };
    // Plaintext: 3b726574 7475432d (little-endian bytes)
    uint8_t speck_pt[8] = { 0x74, 0x65, 0x72, 0x3b, 0x2d, 0x43, 0x75, 0x74 };
    uint8_t speck_ct[8] = { 0 };
    uint8_t speck_expected_ct[8] = { 0x48, 0xa5, 0x6f, 0x8c, 0x8b, 0x02, 0x4e, 0x45 };

    speck64_128_encrypt_block(speck_k, speck_pt, speck_ct);
    if (memcmp(speck_ct, speck_expected_ct, 8) != 0) {
        printf("Speck Block Test FAILED!\n");
        printf("Computed: "); for (int i=0; i<8; i++) printf("%02x ", speck_ct[i]); printf("\n");
        printf("Expected: "); for (int i=0; i<8; i++) printf("%02x ", speck_expected_ct[i]); printf("\n");
        return 1;
    }
    printf("Speck Block Test PASSED (100%% bit match)!\n");

    uint8_t speck_dec[8] = { 0 };
    speck64_128_decrypt_block(speck_k, speck_ct, speck_dec);
    assert(memcmp(speck_dec, speck_pt, 8) == 0);
    printf("Speck Block Decrypt PASSED!\n");


    printf("--- Testing Present 128 Test Vector ---\n");
    // Standard Present-128 Test Vector:
    // Key: 0123456789abcdef0123456789abcdef
    // Plaintext: 0123456789abcdef
    // Ciphertext: 0e9d28685e671dd6
    uint8_t pres_k[16] = {
        0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
        0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef
    };
    uint8_t pres_pt[8] = {
        0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef
    };
    uint8_t pres_ct[8] = { 0 };
    uint8_t pres_expected_ct[8] = {
        0x0e, 0x9d, 0x28, 0x68, 0x5e, 0x67, 0x1d, 0xd6
    };

    present128_encrypt_block(pres_k, pres_pt, pres_ct);
    if (memcmp(pres_ct, pres_expected_ct, 8) != 0) {
        printf("Present Block Test FAILED!\n");
        printf("Computed: "); for (int i=0; i<8; i++) printf("%02x ", pres_ct[i]); printf("\n");
        printf("Expected: "); for (int i=0; i<8; i++) printf("%02x ", pres_expected_ct[i]); printf("\n");
        return 1;
    }
    printf("Present Block Test PASSED (100%% bit match)!\n");


    printf("--- Testing AEAD Seal & Open for Speck ---\n");
    uint8_t nonce[16] = { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 };
    uint8_t aad[11] = { 1, 0, 2, 3, 0, 1, 0, 0, 0, 1, 2 }; // Sample header (version, sender, profile, epoch, counter, cap)
    uint8_t plain[28] = "Sample sensor data readings!"; // 28 bytes
    uint8_t wire[64] = { 0 };
    uint8_t opened[64] = { 0 };
    size_t wire_len = 0, opened_len = 0;

    assert(lab_speck_seal(speck_k, nonce, aad, sizeof(aad), plain, sizeof(plain), wire, sizeof(wire), &wire_len));
    assert(wire_len == sizeof(plain) + 16);
    assert(lab_speck_open(speck_k, nonce, aad, sizeof(aad), wire, wire_len, opened, sizeof(opened), &opened_len));
    assert(opened_len == sizeof(plain));
    assert(memcmp(opened, plain, sizeof(plain)) == 0);

    // Tamper test
    wire[0] ^= 0x01;
    assert(!lab_speck_open(speck_k, nonce, aad, sizeof(aad), wire, wire_len, opened, sizeof(opened), &opened_len));
    printf("Speck AEAD Seal & Open & Anti-tamper PASSED!\n");


    printf("--- Testing AEAD Seal & Open for Present ---\n");
    wire_len = 0; opened_len = 0;
    assert(lab_present_seal(pres_k, nonce, aad, sizeof(aad), plain, sizeof(plain), wire, sizeof(wire), &wire_len));
    assert(wire_len == sizeof(plain) + 16);
    assert(lab_present_open(pres_k, nonce, aad, sizeof(aad), wire, wire_len, opened, sizeof(opened), &opened_len));
    assert(opened_len == sizeof(plain));
    assert(memcmp(opened, plain, sizeof(plain)) == 0);

    // Tamper test
    wire[5] ^= 0x02;
    assert(!lab_present_open(pres_k, nonce, aad, sizeof(aad), wire, wire_len, opened, sizeof(opened), &opened_len));
    printf("Present AEAD Seal & Open & Anti-tamper PASSED!\n");

    printf("\nALL CIPHER AND AEAD TESTS PASSED PERFECTLY!\n");
    return 0;
}
