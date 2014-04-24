Metazen v1.0
=======
<br />

REQUIREMENTS:

To install this tool, you will first need a cgi-bin directory on a
machine with a web server enabled with CGI support and Perl installed.

Additionally, if not already installed, you will need to install
the following perl modules:

CGI<br />
JSON<br />
LWP::UserAgent<br />
Spreadsheet::WriteExcel<br />
<br />

INSTALLATION:

Clone this GitHub repository to a location within your cgi-bin directory.
The GitHub repository is located at: https://github.com/MG-RAST/metazen

Edit the config file conf/metazen_config_template.pm and save it as conf/metazen_config.pm
Edit the perl header file tool_hdr_template and save it as tool_hdr

From the metazen directory run 'make'

We gratefully acknowledge the support of Metazen by the Gordon and Betty Moore Foundation, Grant 3354.
