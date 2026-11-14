# Pin the vetted software AES backend for host/mote consistency. The pinned
# MSPSim CC2420 strobe switch does not implement SAES.
CFLAGS += -DAES_128_CONF=aes_128_driver
