CONTIKI_PROJECT = sensor root
all: $(CONTIKI_PROJECT)

WITH_UIP6 = 1
UIP_CONF_IPV6 = 1
CFLAGS += -DUIP_CONF_IPV6_RPL

PROJECTDIRS += ../crypto
PROJECT_SOURCEFILES += aggregate.c protocol.c speck.c present.c aes-128.c ccm-star.c aes_ccm.c secure_packet.c

CFLAGS += -std=gnu99 -Os -ffunction-sections -fdata-sections
LDFLAGS += -Wl,--gc-sections
CFLAGS += -DPROJECT_CONF_H=\"project-conf.h\"
CFLAGS += -I. -I../crypto

CONTIKI = ../contiki-2.7
include $(CONTIKI)/Makefile.include
