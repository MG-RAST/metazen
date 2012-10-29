SHELL = /bin/sh

TOP_DIR    := $(PWD)
export TOP_DIR
TOOL_HDR   := tool_hdr
MGRAST_DIR := ../MG-RAST/site

bindir      = $(TOP_DIR)/bin
srcdir      = $(TOP_DIR)/src

mgrast:
	$(bindir)/makeScriptHeaders $(TOOL_HDR)
	cp tool_hdr metazen.cgi
	cat $(srcdir)/metazen.cgi >> metazen.cgi
	chmod 755 metazen.cgi
	cp metazen.cgi $(MGRAST_DIR)/CGI/metazen.cgi
	cp Html/* $(MGRAST_DIR)/CGI/Html/.
