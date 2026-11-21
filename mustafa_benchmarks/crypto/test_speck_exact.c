#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <assert.h>

#define ROR32(x, r) (((x) >> (r)) | ((x) << (32 - (r))))
#define ROL32(x, r) (((x) << (r)) | ((x) >> (32 - (r))))
#define R(x, y, k) (x = (ROR32(x, 8) + y) ^ k, y = ROL32(y, 3) ^ x)
#define R_INV(x, y, k) (y = ROR32(y ^ x, 3), x = ROL32((x ^ k) - y, 8))

#define SPECK_ROUNDS 27

void speck_test() {
    uint32_t k[SPECK_ROUNDS];
    uint32_t k0 = 0x03020100;
    uint32_t l[3] = { 0x0b0a0908, 0x13121110, 0x1b1a1918 };
    k[0] = k0;
    for (uint32_t i = 0; i < SPECK_ROUNDS - 1; i++) {
        uint32_t l_idx = i % 3;
        l[l_idx] = (k[i] + ROR32(l[l_idx], 8)) ^ i;
        k[i + 1] = ROL32(k[i], 3) ^ l[l_idx];
    }

    uint32_t x = 0x3b726574;
    uint32_t y = 0x74616c20;

    for (int i = 0; i < SPECK_ROUNDS; i++) {
        R(x, y, k[i]);
    }

    printf("Speck output: x = 0x%08x, y = 0x%08x\n", x, y);
    printf("Expected:     x = 0x8c6fa548, y = 0x454e028b\n");
    if(x == 0x8c6fa548 && y == 0x454e028b) printf("SPECK 64/128 TEST PASSED 100%% EXACT!\n");
    else printf("Differs in key schedule or round logic.\n");

}

int main() {
    speck_test();
    return 0;
}
