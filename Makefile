MGRAST_DIR = ../MG-RAST/site

mgrast:
	cp metazen.cgi $(MGRAST_DIR)/CGI/metazen.cgi
	cp Html/* $(MGRAST_DIR)/CGI/Html/.

