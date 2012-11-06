package Conf;

#####################################################################
# Metazen configuration
#####################################################################

$app_id       = 'MetaZen';
$app_secret   = '4igdibXTeSznDiuDAdd5BgKCL';
$oAuth_url    = 'http://metagenomics.anl.gov/oAuthPPO.cgi';
$redirect_url = 'http://metagenomics.anl.gov/metazen.cgi';

$google_analytics = "
    <script type=\"text/javascript\">
      var gaJsHost = ((\"https:\" == document.location.protocol) ? \"https://ssl.\" : \"http://www.\");
      document.write(unescape(\"%3Cscript src='\" + gaJsHost + \"google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E\"));
    </script>
    <script type=\"text/javascript\">
      try {
      var pageTracker = _gat._getTracker(\"UA-8339940-1\");
      pageTracker._trackPageview();
      pageTracker._trackPageLoadTime();
      } catch(err) {}
    </script>";
