/* Official pinned corpus Count 1 and 35; not generated test results. */
#include "contiki.h"
#include "ascon_aead.h"
#include <stdio.h>
#include <string.h>
static const uint8_t v0_Key[] = {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15};
static const uint8_t v0_Nonce[] = {16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31};
static const uint8_t v0_PT[] = {0};
static const uint8_t v0_AD[] = {0};
static const uint8_t v0_CT[] = {79,156,39,130,17,190,201,49,107,246,143,70,238,139,46,198};
static const uint8_t v1_Key[] = {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15};
static const uint8_t v1_Nonce[] = {16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31};
static const uint8_t v1_PT[] = {32};
static const uint8_t v1_AD[] = {48};
static const uint8_t v1_CT[] = {150,43,128,22,131,108,117,167,216,104,102,88,140,162,69,216,134};
PROCESS(ascon_kat_process, "Official Ascon KAT");
AUTOSTART_PROCESSES(&ascon_kat_process);
PROCESS_THREAD(ascon_kat_process, ev, data) {
  static uint8_t cipher[56], plain[40];
  static size_t n, m;
  (void)ev; (void)data;
  PROCESS_BEGIN();
  if(!lab_ascon_seal(v0_Key, v0_Nonce, v0_AD, 0, v0_PT, 0, cipher, sizeof cipher, &n) || n != 16 || memcmp(cipher, v0_CT, n) ||
     !lab_ascon_open(v0_Key, v0_Nonce, v0_AD, 0, cipher, n, plain, sizeof plain, &m) || m != 0 || memcmp(plain, v0_PT, m)) { puts("PHASE4_KAT_FAIL_1"); PROCESS_EXIT(); }
  cipher[n-1] ^= 1;
  memset(plain, 0xa5, sizeof plain);
  if(lab_ascon_open(v0_Key, v0_Nonce, v0_AD, 0, cipher, n, plain, sizeof plain, &m)) { puts("PHASE4_KAT_FAIL_2"); PROCESS_EXIT(); }
  for(unsigned i=0; i<sizeof plain; i++) if(plain[i] != 0xa5) { puts("PHASE4_KAT_FAIL_3"); PROCESS_EXIT(); }
  if(!lab_ascon_seal(v1_Key, v1_Nonce, v1_AD, 1, v1_PT, 1, cipher, sizeof cipher, &n) || n != 17 || memcmp(cipher, v1_CT, n) ||
     !lab_ascon_open(v1_Key, v1_Nonce, v1_AD, 1, cipher, n, plain, sizeof plain, &m) || m != 1 || memcmp(plain, v1_PT, m)) { puts("PHASE4_KAT_FAIL_4"); PROCESS_EXIT(); }
  cipher[n-1] ^= 1;
  memset(plain, 0xa5, sizeof plain);
  if(lab_ascon_open(v1_Key, v1_Nonce, v1_AD, 1, cipher, n, plain, sizeof plain, &m)) { puts("PHASE4_KAT_FAIL_5"); PROCESS_EXIT(); }
  for(unsigned i=0; i<sizeof plain; i++) if(plain[i] != 0xa5) { puts("PHASE4_KAT_FAIL_6"); PROCESS_EXIT(); }
  puts("PHASE4_KAT_PASS");
  PROCESS_END();
}
