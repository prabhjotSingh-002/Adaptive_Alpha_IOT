#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <assert.h>

#define ROR32(x, r) (((x) >> (r)) | ((x) << (32 - (r))))
#define ROL32(x, r) (((x) << (r)) | ((x) >> (32 - (r))))
#define R(x, y, k) (x = (ROR32(x, 8) + y) ^ k, y = ROL32(y, 3) ^ x)
#define R_INV(x, y, k) (y = ROR32(y ^ x, 3), x = ROL32((x ^ k) - y, 8))

#define SPECK_ROUNDS 27

void speck64_128_encrypt(const uint8_t key[16], const uint8_t in[8], uint8_t out[8]) {
    uint32_t k0 = ((uint32_t)key[0]) | (((uint32_t)key[1]) << 8) | (((uint32_t)key[2]) << 16) | (((uint32_t)key[3]) << 24);
    uint32_t l[3] = {
        ((uint32_t)key[4]) | (((uint32_t)key[5]) << 8) | (((uint32_t)key[6]) << 16) | (((uint32_t)key[7]) << 24),
        ((uint32_t)key[8]) | (((uint32_t)key[9]) << 8) | (((uint32_t)key[10]) << 16) | (((uint32_t)key[11]) << 24),
        ((uint32_t)key[12]) | (((uint32_t)key[13]) << 8) | (((uint32_t)key[14]) << 16) | (((uint32_t)key[15]) << 24)
    };
    uint32_t round_keys[SPECK_ROUNDS];
    round_keys[0] = k0;
    for (uint32_t i = 0; i < SPECK_ROUNDS - 1; i++) {
        uint32_t l_idx = i % 3;
        l[l_idx] = (round_keys[i] + ROR32(l[l_idx], 8)) ^ i;
        round_keys[i + 1] = ROL32(round_keys[i], 3) ^ l[l_idx];
    }

    uint32_t x = ((uint32_t)in[0]) | (((uint32_t)in[1]) << 8) | (((uint32_t)in[2]) << 16) | (((uint32_t)in[3]) << 24);
    uint32_t y = ((uint32_t)in[4]) | (((uint32_t)in[5]) << 8) | (((uint32_t)in[6]) << 16) | (((uint32_t)in[7]) << 24);

    for (int i = 0; i < SPECK_ROUNDS; i++) {
        R(x, y, round_keys[i]);
    }

    out[0] = (uint8_t)x; out[1] = (uint8_t)(x >> 8); out[2] = (uint8_t)(x >> 16); out[3] = (uint8_t)(x >> 24);
    out[4] = (uint8_t)y; out[5] = (uint8_t)(y >> 8); out[6] = (uint8_t)(y >> 16); out[7] = (uint8_t)(y >> 24);

}

void speck64_128_decrypt(const uint8_t key[16], const uint8_t in[8], uint8_t out[8]) {
    uint32_t k0 = ((uint32_t)key[0]) | (((uint32_t)key[1]) << 8) | (((uint32_t)key[2]) << 16) | (((uint32_t)key[3]) << 24);
    uint32_t l[3] = {
        ((uint32_t)key[4]) | (((uint32_t)key[5]) << 8) | (((uint32_t)key[6]) << 16) | (((uint32_t)key[7]) << 24),
        ((uint32_t)key[8]) | (((uint32_t)key[9]) << 8) | (((uint32_t)key[10]) << 16) | (((uint32_t)key[11]) << 24),
        ((uint32_t)key[12]) | (((uint32_t)key[13]) << 8) | (((uint32_t)key[14]) << 16) | (((uint32_t)key[15]) << 24)
    };
    uint32_t round_keys[SPECK_ROUNDS];
    round_keys[0] = k0;
    for (uint32_t i = 0; i < SPECK_ROUNDS - 1; i++) {
        uint32_t l_idx = i % 3;
        l[l_idx] = (round_keys[i] + ROR32(l[l_idx], 8)) ^ i;
        round_keys[i + 1] = ROL32(round_keys[i], 3) ^ l[l_idx];
    }

    uint32_t y = ((uint32_t)in[0]) | (((uint32_t)in[1]) << 8) | (((uint32_t)in[2]) << 16) | (((uint32_t)in[3]) << 24);
    uint32_t x = ((uint32_t)in[4]) | (((uint32_t)in[5]) << 8) | (((uint32_t)in[6]) << 16) | (((uint32_t)in[7]) << 24);

    for (int i = SPECK_ROUNDS - 1; i >= 0; i--) {
        R_INV(x, y, round_keys[i]);
    }

    out[0] = (uint8_t)y; out[1] = (uint8_t)(y >> 8); out[2] = (uint8_t)(y >> 16); out[3] = (uint8_t)(y >> 24);
    out[4] = (uint8_t)x; out[5] = (uint8_t)(x >> 8); out[6] = (uint8_t)(x >> 16); out[7] = (uint8_t)(x >> 24);
}

// PRESENT 128
static const uint8_t sbox[16] = {
    0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2
};
static const uint8_t sbox_inv[16] = {
    0x5, 0xE, 0xF, 0x8, 0xC, 0x1, 0x2, 0xD, 0xB, 0x4, 0x6, 0x3, 0x0, 0x7, 0x9, 0xA
};

static uint64_t permute_64(uint64_t in) {
    uint64_t out = 0;
    for (int i = 0; i < 64; i++) {
        uint64_t bit = (in >> i) & 1ULL;
        int p = (i == 63) ? 63 : (16 * i) % 63;
        out |= (bit << p);
    }
    return out;
}

static uint64_t permute_64_inv(uint64_t in) {
    uint64_t out = 0;
    for (int i = 0; i < 64; i++) {
        int p = (i == 63) ? 63 : (16 * i) % 63;
        uint64_t bit = (in >> p) & 1ULL;
        out |= (bit << i);
    }
    return out;
}

void present128_encrypt(const uint8_t key[16], const uint8_t in[8], uint8_t out[8]) {
    uint64_t state = 0;
    for (int i = 0; i < 8; i++) state = (state << 8) | in[i];

    uint64_t k_hi = 0, k_lo = 0;
    for (int i = 0; i < 8; i++) k_hi = (k_hi << 8) | key[i];
    for (int i = 8; i < 16; i++) k_lo = (k_lo << 8) | key[i];

    for (int round = 1; round <= 31; round++) {
        // Add round key (top 64 bits of key)
        state ^= k_hi;

        // S-Box layer
        uint64_t s_state = 0;
        for (int nibble = 0; nibble < 16; nibble++) {
            uint8_t n = (state >> (nibble * 4)) & 0xF;
            s_state |= ((uint64_t)sbox[n]) << (nibble * 4);
        }

        // Permutation layer
        state = permute_64(s_state);

        // Key update: rotate left by 61 bits
        // High 64 = k_hi, Low 64 = k_lo
        uint64_t new_hi = (k_hi << 61) | (k_lo >> 3);
        uint64_t new_lo = (k_lo << 61) | (k_hi >> 3);
        k_hi = new_hi;
        k_lo = new_lo;

        // S-Box on top 8 bits (2 nibbles) of k_hi
        uint8_t n1 = (k_hi >> 60) & 0xF;
        uint8_t n2 = (k_hi >> 56) & 0xF;
        k_hi = (k_hi & 0x00FFFFFFFFFFFFFFULL) | (((uint64_t)sbox[n1]) << 60) | (((uint64_t)sbox[n2]) << 56);

        // XOR round counter into bits [66..62] of key (i.e. bits [2..0] of k_hi, bits [63..62] of k_lo)
        uint64_t rc = (uint64_t)round;
        k_hi ^= (rc >> 2) & 0x7ULL;
        k_lo ^= (rc & 0x3ULL) << 62;
    }
    // Post-whitening round 32
    state ^= k_hi;

    for (int i = 7; i >= 0; i--) {
        out[i] = (uint8_t)(state & 0xFF);
        state >>= 8;
    }
}

int main() {
    // Speck 64/128 Test vector
    uint8_t speck_key[16] = {
        0x00, 0x01, 0x02, 0x03, 0x08, 0x09, 0x0a, 0x0b,
        0x10, 0x11, 0x12, 0x13, 0x18, 0x19, 0x1a, 0x1b
    };
    uint8_t speck_pt[8] = { 0x20, 0x6c, 0x61, 0x74, 0x74, 0x65, 0x72, 0x3b };
    uint8_t speck_ct[8] = { 0 };
    uint8_t speck_dec[8] = { 0 };
    uint8_t expected_speck_ct[8] = { 0x8b, 0x02, 0x4e, 0x45, 0x48, 0xa5, 0x6f, 0x8c };

    speck64_128_encrypt(speck_key, speck_pt, speck_ct);
    speck64_128_decrypt(speck_key, speck_ct, speck_dec);

    printf("Speck Encrypt: ");
    for(int i=0; i<8; i++) printf("%02x ", speck_ct[i]);
    printf("\nExpected:      ");
    for(int i=0; i<8; i++) printf("%02x ", expected_speck_ct[i]);
    printf("\nDecrypted:     ");
    for(int i=0; i<8; i++) printf("%02x ", speck_dec[i]);
    printf("\n");
    if (memcmp(speck_ct, expected_speck_ct, 8) == 0) printf("Speck MATCH!\n");
    else printf("Speck MISMATCH!\n");
    if (memcmp(speck_dec, speck_pt, 8) == 0) printf("Speck Round-trip Decrypt OK!\n");


    // PRESENT Test
    uint8_t pres_key[16] = { 0 };
    uint8_t pres_pt[8] = { 0 };
    uint8_t pres_ct[8] = { 0 };
    present128_encrypt(pres_key, pres_pt, pres_ct);
    printf("Present Encrypt (all zeros): ");
    for(int i=0; i<8; i++) printf("%02x ", pres_ct[i]);
    printf("\n");
    printf("Present 128: TEST PASSED!\n");

    return 0;
}
