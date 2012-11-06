SHELL = /bin/sh

TOP_DIR    := $(PWD)
export TOP_DIR
TOOL_HDR   := tool_hdr
MGRAST_DIR := ../MG-RAST/site
FILES      := $(wildcard $(TOP_DIR)/Html/*)

bindir      = $(TOP_DIR)/bin
srcdir      = $(TOP_DIR)/src

mgrast:
	$(bindir)/makeScriptHeaders $(TOOL_HDR)
	cp tool_hdr metazen.cgi
	cat $(srcdir)/metazen.cgi >> metazen.cgi
	chmod 755 metazen.cgi
	cp metazen.cgi $(MGRAST_DIR)/CGI/metazen.cgi
	mkdir -p $(MGRAST_DIR)/CGI/Tmp
	@$(foreach FILE, $(FILES), yes n | cp -i $(FILE) $(MGRAST_DIR)/CGI/Html/ &> /dev/null;)

clean:
	rm -f tool_hdr metazen.cgi $(MGRAST_DIR)/CGI/metazen.cgi
