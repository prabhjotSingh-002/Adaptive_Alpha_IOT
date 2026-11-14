#include "aes_ccm.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static size_t unhex(const char *s, uint8_t *out) {
  size_t n = strlen(s) / 2;
  for(size_t i = 0; i < n; i++) {
    unsigned x;
    assert(sscanf(s + 2 * i, "%2x", &x) == 1);
    out[i] = (uint8_t)x;
  }
  return n;
}
int main(void) {
  /* NIST CAVP CCM VTT128.rsp [Tlen=16], Count=60. */
  uint8_t key[16], nonce[13], aad[32], plain[24], expected[40];
  uint8_t encrypted[56], opened[40], wrong_key[16];
  size_t n, m;
  unhex("4189351b5caea375a0299e81c621bf43", key);
  unhex("48c0906930561e0ab0ef4cd972", nonce);
  unhex("40a27c1d1e23ea3dbe8056b2774861a4a201cce49f19997d19206d8c8a343951", aad);
  unhex("4535d12b4377928a7c0a61c9f825a48671ea05910748c8ef", plain);
  unhex("26c56961c035a7e452cce61bc6ee220d77b3f94d18fd10b6d80e8bf80f4a46cab06d4313f0db9be9", expected);
  assert(lab_ccm_seal(key, nonce, aad, sizeof aad, plain, sizeof plain, encrypted, sizeof encrypted, &n));
  assert(n == sizeof expected && !memcmp(encrypted, expected, n));
  assert(lab_ccm_open(key, nonce, aad, sizeof aad, encrypted, n, opened, sizeof opened, &m));
  assert(m == sizeof plain && !memcmp(opened, plain, m));
  for(size_t i = sizeof plain; i < n; i++) {
    encrypted[i] ^= 1; memset(opened, 0xa5, sizeof opened); m = 999;
    assert(!lab_ccm_open(key, nonce, aad, sizeof aad, encrypted, n, opened, sizeof opened, &m));
    assert(m == 0);
    for(size_t j = 0; j < sizeof opened; j++) assert(opened[j] == 0xa5);
    encrypted[i] ^= 1;
  }
  memcpy(wrong_key, key, sizeof key); wrong_key[0] ^= 1;
  assert(!lab_ccm_open(wrong_key, nonce, aad, sizeof aad, encrypted, n, opened, sizeof opened, &m));
  aad[0] ^= 1;
  assert(!lab_ccm_open(key, nonce, aad, sizeof aad, encrypted, n, opened, sizeof opened, &m));
  aad[0] ^= 1; encrypted[0] ^= 1;
  assert(!lab_ccm_open(key, nonce, aad, sizeof aad, encrypted, n, opened, sizeof opened, &m));
  encrypted[0] ^= 1;
  assert(!lab_ccm_open(key, nonce, aad, sizeof aad, encrypted, 15, opened, sizeof opened, &m));
  assert(!lab_ccm_seal(key, nonce, aad, sizeof aad, plain, sizeof plain, encrypted, 39, &n));
  assert(lab_ccm_seal(key, nonce, NULL, 0, NULL, 0, encrypted, sizeof encrypted, &n));
  assert(lab_ccm_open(key, nonce, NULL, 0, encrypted, n, opened, sizeof opened, &m) && m == 0);
  /* NIST VPT128, Plen=0, Count=0: Payload=00 represents zero bytes. */
  unhex("2ebf60f0969013a54a3dedb19d20f6c8", key);
  unhex("1de8c5e21f9db33123ff870add", nonce);
  unhex("e1de6c6119d7db471136285d10b47a450221b16978569190ef6a22b055295603", aad);
  unhex("0ead29ef205fbb86d11abe5ed704b880", expected);
  assert(lab_ccm_seal(key, nonce, aad, 32, NULL, 0, encrypted, sizeof encrypted, &n));
  assert(n == 16 && !memcmp(encrypted, expected, n));
  assert(lab_ccm_open(key, nonce, aad, 32, encrypted, n, opened, sizeof opened, &m) && m == 0);
  /* NIST VADT128, Alen=0, Count=0. */
  unhex("d24a3d3dde8c84830280cb87abad0bb3", key);
  unhex("f1100035bb24a8d26004e0e24b", nonce);
  unhex("7c86135ed9c2a515aaae0e9a208133897269220f30870006", plain);
  unhex("1faeb0ee2ca2cd52f0aa3966578344f24e69b742c4ab37ab1123301219c70599b7c373ad4b3ad67b", expected);
  assert(lab_ccm_seal(key, nonce, NULL, 0, plain, 24, encrypted, sizeof encrypted, &n));
  assert(n == 40 && !memcmp(encrypted, expected, n));
  assert(lab_ccm_open(key, nonce, NULL, 0, encrypted, n, opened, sizeof opened, &m));
  assert(m == 24 && !memcmp(opened, plain, m));
  puts("NIST VTT128, VPT128 and VADT128 Count vectors and negative adapter checks passed");
  return 0;
}
