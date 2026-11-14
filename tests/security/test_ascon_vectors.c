#include "ascon_aead.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static size_t unhex(const char *s, unsigned char *out, size_t cap) {
  size_t n = strcspn(s, "\r\n");
  if(n % 2 || n / 2 > cap) { fprintf(stderr, "invalid vector length\n"); exit(1); }
  for(size_t i = 0; i < n / 2; i++) {
    unsigned x;
    if(sscanf(s + 2*i, "%2x", &x) != 1) { fprintf(stderr, "invalid vector hex\n"); exit(1); }
    out[i] = (unsigned char)x;
  }
  return n / 2;
}
int main(int argc, char **argv) {
  char line[512];
  unsigned char key[16], nonce[16], pt[40], ad[32], expected[56], actual[56], opened[40];
  size_t keylen=0, nlen=0, plen=0, alen=0, elen=0, outlen=0, openedlen=0, count=0;
  if(argc != 2) return 2;
  FILE *f = fopen(argv[1], "r");
  if(!f) { perror(argv[1]); return 2; }
  while(fgets(line, sizeof line, f)) {
    if(!strncmp(line, "Key = ", 6)) keylen=unhex(line+6,key,sizeof key);
    else if(!strncmp(line, "Nonce = ", 8)) nlen=unhex(line+8,nonce,sizeof nonce);
    else if(!strncmp(line, "PT = ", 5)) plen=unhex(line+5,pt,sizeof pt);
    else if(!strncmp(line, "AD = ", 5)) alen=unhex(line+5,ad,sizeof ad);
    else if(!strncmp(line, "CT = ", 5)) {
      elen=unhex(line+5,expected,sizeof expected);
      if(keylen!=16 || nlen!=16 || elen!=plen+16 ||
         !lab_ascon_seal(key,nonce,ad,alen,pt,plen,actual,sizeof actual,&outlen) ||
         outlen!=elen || memcmp(actual,expected,elen) ||
         !lab_ascon_open(key,nonce,ad,alen,actual,outlen,opened,sizeof opened,&openedlen) ||
         openedlen!=plen || memcmp(opened,pt,plen)) {
        fprintf(stderr, "vector %zu failed\n", count+1); fclose(f); return 1;
      }
      count++;
    }
  }
  if(ferror(f) || fclose(f) || count != 1089) {
    fprintf(stderr, "incomplete vector corpus: %zu\n", count); return 1;
  }
  printf("PASS: %zu official Ascon-AEAD128 vectors, seal and open\n", count);
  return 0;
}
