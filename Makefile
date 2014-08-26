SHELL = /bin/sh

TOP_DIR    := $(PWD)
export TOP_DIR
TOOL_HDR   := tool_hdr
MGRAST_DIR := ../MG-RAST/site
JS_FILES   := $(wildcard $(TOP_DIR)/assets/js/*)
CSS_FILES  := $(wildcard $(TOP_DIR)/assets/css/*)
IMG_FILES  := $(wildcard $(TOP_DIR)/assets/images/*)

bindir      = $(TOP_DIR)/bin
srcdir      = $(TOP_DIR)/src

all:
	$(bindir)/makeScriptHeaders $(TOOL_HDR)
	cp tool_hdr metazen.cgi
	cat $(srcdir)/metazen.cgi >> metazen.cgi
	chmod 755 metazen.cgi

mgrast:
	$(bindir)/makeScriptHeaders $(TOOL_HDR)
	cp tool_hdr metazen.cgi
	cat $(srcdir)/metazen.cgi >> metazen.cgi
	chmod 755 metazen.cgi
	cp metazen.cgi $(MGRAST_DIR)/CGI/metazen.cgi
	mkdir -p $(MGRAST_DIR)/CGI/Tmp
	mkdir -p $(MGRAST_DIR)/CGI/assets/js
	mkdir -p $(MGRAST_DIR)/CGI/assets/css
	mkdir -p $(MGRAST_DIR)/CGI/assets/images
	$(foreach FILE, $(JS_FILES), yes n | cp -i $(FILE) $(MGRAST_DIR)/CGI/assets/js/ &> /dev/null;)
	$(foreach FILE, $(CSS_FILES), yes n | cp -i $(FILE) $(MGRAST_DIR)/CGI/assets/css/ &> /dev/null;)
	$(foreach FILE, $(IMG_FILES), yes n | cp -i $(FILE) $(MGRAST_DIR)/CGI/assets/images/ &> /dev/null;)

clean:
	rm -f tool_hdr metazen.cgi $(MGRAST_DIR)/CGI/metazen.cgi
