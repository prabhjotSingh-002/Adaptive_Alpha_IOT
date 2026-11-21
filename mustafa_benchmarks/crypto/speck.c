#include "speck.h"
#include <string.h>

#define SPECK_ROUNDS 27

#define ROR32(v, r) (((v) >> (r)) | ((v) << (32 - (r))))
#define ROL32(v, r) (((v) << (r)) | ((v) >> (32 - (r))))
#define R_ROUND(x, y, k) (x = (ROR32((x), 8) + (y)) ^ (k), y = ROL32((y), 3) ^ (x))
#define R_INV(x, y, k)   (y = ROR32((y) ^ (x), 3), x = ROL32(((x) ^ (k)) - (y), 8))

static inline uint32_t load32_le(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static inline void store32_le(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)v;
    p[1] = (uint8_t)(v >> 8);
    p[2] = (uint8_t)(v >> 16);
    p[3] = (uint8_t)(v >> 24);
}

static void speck_key_schedule(const uint8_t key[16], uint32_t round_keys[SPECK_ROUNDS]) {
    uint32_t k0 = load32_le(key);
    uint32_t l[3];
    uint32_t i;
    l[0] = load32_le(key + 4);
    l[1] = load32_le(key + 8);
    l[2] = load32_le(key + 12);
    round_keys[0] = k0;
    for (i = 0; i < SPECK_ROUNDS - 1; i++) {
        uint32_t l_idx = i % 3;
        l[l_idx] = (round_keys[i] + ROR32(l[l_idx], 8)) ^ i;
        round_keys[i + 1] = ROL32(round_keys[i], 3) ^ l[l_idx];
    }
}

void speck64_128_encrypt_block(const uint8_t key[16], const uint8_t in[8], uint8_t out[8]) {
    uint32_t round_keys[SPECK_ROUNDS];
    int i;
    uint32_t x, y;
    speck_key_schedule(key, round_keys);

    x = load32_le(in);
    y = load32_le(in + 4);

    for (i = 0; i < SPECK_ROUNDS; i++) {
        R_ROUND(x, y, round_keys[i]);
    }

    store32_le(out, x);
    store32_le(out + 4, y);
}

void speck64_128_decrypt_block(const uint8_t key[16], const uint8_t in[8], uint8_t out[8]) {
    uint32_t round_keys[SPECK_ROUNDS];
    int i;
    uint32_t x, y;
    speck_key_schedule(key, round_keys);

    x = load32_le(in);
    y = load32_le(in + 4);

    for (i = SPECK_ROUNDS - 1; i >= 0; i--) {
        R_INV(x, y, round_keys[i]);
    }

    store32_le(out, x);
    store32_le(out + 4, y);
}

static void speck_cbc_mac_16(const uint32_t rk[SPECK_ROUNDS],
                             const uint8_t *aad, size_t aad_len,
                             const uint8_t *data, size_t data_len,
                             uint8_t mac[16]) {
    uint8_t state[8];
    uint8_t block[8];
    size_t i = 0;
    int b, r;
    uint32_t x, y;
    memset(state, 0, 8);

    while (i < aad_len) {
        size_t chunk = (aad_len - i < 8) ? (aad_len - i) : 8;
        memset(block, 0, 8);
        memcpy(block, aad + i, chunk);
        for (b = 0; b < 8; b++) state[b] ^= block[b];

        x = load32_le(state);
        y = load32_le(state + 4);
        for (r = 0; r < SPECK_ROUNDS; r++) R_ROUND(x, y, rk[r]);
        store32_le(state, x);
        store32_le(state + 4, y);

        i += 8;
    }

    i = 0;
    while (i < data_len) {
        size_t chunk = (data_len - i < 8) ? (data_len - i) : 8;
        memset(block, 0, 8);
        memcpy(block, data + i, chunk);
        for (b = 0; b < 8; b++) state[b] ^= block[b];

        x = load32_le(state);
        y = load32_le(state + 4);
        for (r = 0; r < SPECK_ROUNDS; r++) R_ROUND(x, y, rk[r]);
        store32_le(state, x);
        store32_le(state + 4, y);

        i += 8;
    }

    // First 8 bytes of tag is CBC-MAC state
    memcpy(mac, state, 8);

    // Second 8 bytes is encryption of state XOR mask
    for (b = 0; b < 8; b++) block[b] = state[b] ^ 0x5Au;
    x = load32_le(block);
    y = load32_le(block + 4);
    for (r = 0; r < SPECK_ROUNDS; r++) R_ROUND(x, y, rk[r]);
    store32_le(mac + 8, x);
    store32_le(mac + 12, y);
}

static void speck_ctr_crypt(const uint32_t rk[SPECK_ROUNDS],
                           const uint8_t nonce[16],
                           const uint8_t *in, size_t len,
                           uint8_t *out) {
    uint8_t ctr_blk[8];
    uint8_t stream[8];
    uint16_t blk_idx = 0;
    size_t offset;
    int r;

    for (offset = 0; offset < len; offset += 8) {
        size_t chunk;
        size_t b;
        uint32_t x, y;
        memcpy(ctr_blk, nonce + 7, 6);
        ctr_blk[6] = (uint8_t)(blk_idx >> 8);
        ctr_blk[7] = (uint8_t)(blk_idx & 0xFF);
        blk_idx++;

        x = load32_le(ctr_blk);
        y = load32_le(ctr_blk + 4);
        for (r = 0; r < SPECK_ROUNDS; r++) R_ROUND(x, y, rk[r]);
        store32_le(stream, x);
        store32_le(stream + 4, y);

        chunk = (len - offset < 8) ? (len - offset) : 8;
        for (b = 0; b < chunk; b++) {
            out[offset + b] = in[offset + b] ^ stream[b];
        }
    }
}

bool lab_speck_seal(const uint8_t key[16], const uint8_t nonce[16],
                    const uint8_t *aad, size_t aad_len,
                    const uint8_t *plain, size_t plain_len,
                    uint8_t *out, size_t capacity, size_t *written) {
    uint32_t rk[SPECK_ROUNDS];
    uint8_t mac[16];
    if (!key || !nonce || !out || !written) return false;
    if (capacity < plain_len + SPECK_TAG_SIZE) return false;

    speck_key_schedule(key, rk);
    speck_cbc_mac_16(rk, aad, aad_len, plain, plain_len, mac);
    speck_ctr_crypt(rk, nonce, plain, plain_len, out);

    memcpy(out + plain_len, mac, SPECK_TAG_SIZE);
    *written = plain_len + SPECK_TAG_SIZE;
    return true;
}

bool lab_speck_open(const uint8_t key[16], const uint8_t nonce[16],
                    const uint8_t *aad, size_t aad_len,
                    const uint8_t *cipher, size_t cipher_len,
                    uint8_t *out, size_t capacity, size_t *written) {
    size_t plain_len;
    uint32_t rk[SPECK_ROUNDS];
    const uint8_t *expected_mac;
    uint8_t computed_mac[16];
    uint8_t diff = 0;
    int i;

    if (!key || !nonce || !cipher || !out || !written) return false;
    if (cipher_len < SPECK_TAG_SIZE) return false;

    plain_len = cipher_len - SPECK_TAG_SIZE;
    if (capacity < plain_len) return false;

    speck_key_schedule(key, rk);
    expected_mac = cipher + plain_len;

    speck_ctr_crypt(rk, nonce, cipher, plain_len, out);
    speck_cbc_mac_16(rk, aad, aad_len, out, plain_len, computed_mac);

    for (i = 0; i < 16; i++) diff |= (computed_mac[i] ^ expected_mac[i]);

    if (diff != 0) {
        memset(out, 0, plain_len);
        *written = 0;
        return false;
    }

    *written = plain_len;
    return true;
}
