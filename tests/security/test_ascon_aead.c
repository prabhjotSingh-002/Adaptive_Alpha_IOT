#include "ascon_aead.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
int main(void) {
  uint8_t key[16], nonce[16], output[56], opened[40], message[40];
  const uint8_t expected[16] = {0x4f,0x9c,0x27,0x82,0x11,0xbe,0xc9,0x31,
                                0x6b,0xf6,0x8f,0x46,0xee,0x8b,0x2e,0xc6};
  size_t length = 0, plain_len = 0;
  for(size_t i = 0; i < 16; i++) { key[i] = (uint8_t)i; nonce[i] = (uint8_t)(i + 16); }
  for(size_t i = 0; i < sizeof message; i++) message[i] = (uint8_t)i;
  assert(lab_ascon_seal(key, nonce, NULL, 0, NULL, 0, output, sizeof output, &length));
  assert(length == sizeof expected && memcmp(output, expected, length) == 0);
  assert(lab_ascon_open(key, nonce, NULL, 0, output, length, opened, sizeof opened, &plain_len));
  assert(plain_len == 0);
  assert(lab_ascon_seal(key, nonce, message, 11, message, sizeof message, output, sizeof output, &length));
  assert(lab_ascon_open(key, nonce, message, 11, output, length, opened, sizeof opened, &plain_len));
  assert(plain_len == sizeof message && memcmp(opened, message, plain_len) == 0);
  output[length - 1] ^= 1;
  memset(opened, 0xa5, sizeof opened);
  assert(!lab_ascon_open(key, nonce, message, 11, output, length, opened, sizeof opened, &plain_len));
  assert(plain_len == 0);
  for(size_t i = 0; i < sizeof opened; i++) assert(opened[i] == 0xa5);
  assert(!lab_ascon_seal(key, nonce, NULL, 0, message, 40, output, 55, &length));
  puts("Ascon official empty KAT, roundtrip, bad tag isolation and bounds: PASS");
  return 0;
}
