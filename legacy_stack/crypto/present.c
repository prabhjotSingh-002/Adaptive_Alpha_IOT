#include "present.h"
#include <string.h>

#define PRESENT_ROUNDS 31

static const uint8_t sbox[16] = {
    0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2
};

static inline uint64_t load64_be(const uint8_t *p) {
    uint64_t v = 0;
    int i;
    for (i = 0; i < 8; i++) {
        v = (v << 8) | p[i];
    }
    return v;
}

static inline void store64_be(uint8_t *p, uint64_t v) {
    int i;
    for (i = 7; i >= 0; i--) {
        p[i] = (uint8_t)(v & 0xFF);
        v >>= 8;
    }
}

void present128_encrypt_block(const uint8_t key[16], const uint8_t in[8], uint8_t out[8]) {
    uint64_t state = load64_be(in);
    uint64_t k_hi = load64_be(key);
    uint64_t k_lo = load64_be(key + 8);
    int round;

    for (round = 1; round <= PRESENT_ROUNDS; round++) {
        uint16_t w0 = 0, w1 = 0, w2 = 0, w3 = 0;
        int j;
        uint64_t new_hi, new_lo;
        uint8_t n1, n2;
        uint64_t rc;

        // 1. Add round key
        state ^= k_hi;

        // 2. Combined S-box and Permutation layer (optimized for 16-bit MSP430)
        for (j = 0; j < 16; j++) {
            uint8_t n = (uint8_t)((state >> (j * 4)) & 0xF);
            uint8_t s = sbox[n];
            w0 |= (uint16_t)(((s >> 0) & 1) << j);
            w1 |= (uint16_t)(((s >> 1) & 1) << j);
            w2 |= (uint16_t)(((s >> 2) & 1) << j);
            w3 |= (uint16_t)(((s >> 3) & 1) << j);
        }
        state = ((uint64_t)w0) | (((uint64_t)w1) << 16) | (((uint64_t)w2) << 32) | (((uint64_t)w3) << 48);

        // 3. Key update: rotate 128-bit key left 61 bits (equivalent to right 3 bits)
        new_hi = (k_hi << 61) | (k_lo >> 3);
        new_lo = (k_lo << 61) | (k_hi >> 3);
        k_hi = new_hi;
        k_lo = new_lo;

        // S-Box on top 8 bits: bits [127..124] and [123..120]
        n1 = (uint8_t)((k_hi >> 60) & 0xF);
        n2 = (uint8_t)((k_hi >> 56) & 0xF);
        k_hi = (k_hi & 0x00FFFFFFFFFFFFFFULL) | (((uint64_t)sbox[n1]) << 60) | (((uint64_t)sbox[n2]) << 56);

        // XOR round counter into bits [66..62] of key
        rc = (uint64_t)round;
        k_hi ^= (rc >> 2) & 0x7ULL;
        k_lo ^= (rc & 0x3ULL) << 62;
    }

    // Post-whitening round 32
    state ^= k_hi;
    store64_be(out, state);
}

static void present_cbc_mac_16(const uint8_t key[16],
                              const uint8_t *aad, size_t aad_len,
                              const uint8_t *data, size_t data_len,
                              uint8_t mac[16]) {
    uint8_t state[8];
    uint8_t block[8];
    size_t i = 0;
    int b;
    memset(state, 0, 8);

    while (i < aad_len) {
        size_t chunk = (aad_len - i < 8) ? (aad_len - i) : 8;
        memset(block, 0, 8);
        memcpy(block, aad + i, chunk);
        for (b = 0; b < 8; b++) state[b] ^= block[b];

        present128_encrypt_block(key, state, state);
        i += 8;
    }

    i = 0;
    while (i < data_len) {
        size_t chunk = (data_len - i < 8) ? (data_len - i) : 8;
        memset(block, 0, 8);
        memcpy(block, data + i, chunk);
        for (b = 0; b < 8; b++) state[b] ^= block[b];

        present128_encrypt_block(key, state, state);
        i += 8;
    }

    // First 8 bytes is state
    memcpy(mac, state, 8);

    // Second 8 bytes is encryption of state XOR mask
    for (b = 0; b < 8; b++) block[b] = state[b] ^ 0x5Au;
    present128_encrypt_block(key, block, mac + 8);
}

static void present_ctr_crypt(const uint8_t key[16],
                             const uint8_t nonce[16],
                             const uint8_t *in, size_t len,
                             uint8_t *out) {
    uint8_t ctr_blk[8];
    uint8_t stream[8];
    uint16_t blk_idx = 0;
    size_t offset;

    for (offset = 0; offset < len; offset += 8) {
        size_t chunk;
        size_t b;
        memcpy(ctr_blk, nonce + 7, 6);
        ctr_blk[6] = (uint8_t)(blk_idx >> 8);
        ctr_blk[7] = (uint8_t)(blk_idx & 0xFF);
        blk_idx++;

        present128_encrypt_block(key, ctr_blk, stream);

        chunk = (len - offset < 8) ? (len - offset) : 8;
        for (b = 0; b < chunk; b++) {
            out[offset + b] = in[offset + b] ^ stream[b];
        }
    }
}

bool lab_present_seal(const uint8_t key[16], const uint8_t nonce[16],
                      const uint8_t *aad, size_t aad_len,
                      const uint8_t *plain, size_t plain_len,
                      uint8_t *out, size_t capacity, size_t *written) {
    uint8_t mac[16];
    if (!key || !nonce || !out || !written) return false;
    if (capacity < plain_len + PRESENT_TAG_SIZE) return false;

    present_cbc_mac_16(key, aad, aad_len, plain, plain_len, mac);
    present_ctr_crypt(key, nonce, plain, plain_len, out);

    memcpy(out + plain_len, mac, PRESENT_TAG_SIZE);
    *written = plain_len + PRESENT_TAG_SIZE;
    return true;
}

bool lab_present_open(const uint8_t key[16], const uint8_t nonce[16],
                      const uint8_t *aad, size_t aad_len,
                      const uint8_t *cipher, size_t cipher_len,
                      uint8_t *out, size_t capacity, size_t *written) {
    size_t plain_len;
    const uint8_t *expected_mac;
    uint8_t computed_mac[16];
    uint8_t diff = 0;
    int i;

    if (!key || !nonce || !cipher || !out || !written) return false;
    if (cipher_len < PRESENT_TAG_SIZE) return false;

    plain_len = cipher_len - PRESENT_TAG_SIZE;
    if (capacity < plain_len) return false;

    expected_mac = cipher + plain_len;

    present_ctr_crypt(key, nonce, cipher, plain_len, out);
    present_cbc_mac_16(key, aad, aad_len, out, plain_len, computed_mac);

    for (i = 0; i < 16; i++) diff |= (computed_mac[i] ^ expected_mac[i]);

    if (diff != 0) {
        memset(out, 0, plain_len);
        *written = 0;
        return false;
    }

    *written = plain_len;
    return true;
}
