Metazen
=======

INSTALLATION:

To install this tool, you will first need a cgi-bin directory on a
machine with a web server enabled with CGI support and Perl installed.
Next, you need to clone our GitHub repository to a location within
your cgi-bin directory.  The GitHub repository is located at:

https://github.com/MG-RAST/Metazen

You will need to edit the first line of the index.cgi file to point
to your local installation of Perl (commonly /usr/bin/perl).

Additionally, if not already installed, you will need to install
the following perl modules:

CGI
JSON
LWP::UserAgent
Spreadsheet::WriteExcel

After installing these components, you should be able to view the
Metazen tool on your server thru a web browser at the following URL:

http://(your-host-name)/~(your-user-name)/(your-sub-directory)/Metazen/index.cgi
