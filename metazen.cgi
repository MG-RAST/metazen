#!/soft/packages/perl/5.12.1/bin/perl

use strict;
use warnings;

use CGI;
use JSON;
use Encode;
use LWP::UserAgent;
use HTML::Entities;
use Spreadsheet::WriteExcel;
use File::Temp qw/ tempfile tempdir /;

my $cgi = new CGI();
my $json = new JSON();

my $session_id = $cgi->cookie('WebSession');

my $url = "http://api.metagenomics.anl.gov/metadata/template";
my $ua = LWP::UserAgent->new;
my $res = $ua->get($url);

my $json_meta_template = $json->decode($res->content);
my $lib_descriptions = { 'metagenome' => 'shotgun metagenome',
                         'mimarks-survey' => 'amplicon metagenome (16S)',
                         'metatranscriptome' => 'meta transcriptome' };

my $project_display_fields = &get_project_display_fields();
my $sample_display_fields = &get_sample_display_fields();
my $library_display_fields = &get_library_display_fields(); 

my $previous_project = $cgi->param('previous_project') && $cgi->param('previous_project') ne "none" ? $cgi->param('previous_project') : "";
my $contact_status = $cgi->param('contact_status') ? $cgi->param('contact_status') : "";

my $json_project_data;
if ($previous_project ne "") {
  my $url = "http://api.metagenomics.anl.gov/project/$previous_project";
  my $ua = LWP::UserAgent->new;
  my $res = $ua->get($url, 'user_auth' => $session_id);
  $json_project_data = $json->decode($res->content); # Returns an array of hashes with project name, id, and pi
}

if ($cgi->param('update')) {
  if ($cgi->param('update') eq 'print_top_of_form') {
    print $cgi->header();
    print_top_of_form();
  } elsif ($cgi->param('update') eq 'print_bottom_of_form') {
    print $cgi->header();
    print_bottom_of_form();
  } elsif ($cgi->param('update') eq 'generate_excel_spreadsheet') {
    print $cgi->header();
    generate_excel_spreadsheet();
  } elsif ($cgi->param('update') eq 'search_address') {
    print $cgi->header();
    search_address();
  } elsif ($cgi->param('update') eq 'download') {
    download();
  }
  exit 0;
}

print $cgi->header();
print base_template();

print qq~
  <div id='metadata_help_tool'>
    <div class='well'><h3>about this tool:</h3>
      <br />
      <p>Metadata (or data about the data) has become a necessity as the community generates large quantities of data sets.</p>
      <p>Using community generated questionnaires we capture this metadata. MG-RAST has implemented the use of <a href='http://gensc.org/gc_wiki/index.php/MIxS' target=_blank>Minimum Information about any (X) Sequence</a> developed by the <a href='http://gensc.org' target=_blank >Genomic Standards Consortium</a> (GSC).</p>
      <p>The best form to capture metadata is via a simple spreadsheet with 12 mandatory terms. This tool is designed to help you fill out your metadata spreadsheet. The metadata you provide, helps us to analyze your data more accurately and helps make MG-RAST a more useful resource.</p>
      <br />
      <p style='font-size:14px;font-weight:bold;'>Terminology:</p>
      <ul>
      <li>project - a set of samples which are being analyzed together</li>
      <li>sample - a single entity that has been obtained for analysis</li>
      <li>library - a prepped collection of DNA fragments generated from a sample (also, in this case, corresponds to a sequencing run)</li>
      <li>environmental information - the characteristics which describe the environment in which your samples were obtained</li>
      <li>sample set - a group of samples sharing the same library and environmental characteristics</li>
      </ul>
      <br />
      <p>This tool will help you get started on completing your metadata spreadsheet by filling in any information that is common across all of your samples and/or libraries. This tool currently only allows users to enter one environmental package for your samples and all samples must have been sequenced by the same number of sequencing technologies with the same number of replicates.  This information is entered in tab #2 below.  If your project deviates from this convention, you must either produce multiple separate metadata spreadsheets or generate your spreadsheet and then edit the appropriate fields manually.</p>
    </div>\n~;

print_prefill_options();
print "    <div id='entire_form_div'>\n";
print_top_of_form();
  print qq~    </div>
  </div>~;

print close_template();


sub print_prefill_options {
  my $url = "http://api.metagenomics.anl.gov/project?display=name&display=pi&display=id";
  my $ua = LWP::UserAgent->new;

  my $res = $ua->get($url, 'user_auth' => $session_id);

  my $json_project_info = $json->decode($res->content); # Returns an array of hashes with project name, id, and pi

  print "
    <div class='well'><h3>prefill form:</h3>
      <br />
      <p>To prefill the project tab with information from a previous project, select a project from the drop-down menu below and click the 'prefill form' button.</p>
      <form method='post' enctype='multipart/form-data' id='prefill_form'>
        <p>Select your previous project from which to prefill the form:
          <select name='previous_project'>
            <option value='none'>none</option>\n";

  foreach my $info (@$json_project_info) {
    my $id = $info->{'id'};
    my $value = $id;
    $value .= ($info->{'name'} eq "") ? "" : " - ".$info->{'name'};
    $value .= ($info->{'pi'} eq "") ? "" : " - ".encode_entities(decode("utf8", $info->{'pi'}));
    print "            <option value='$id'>$value</option>\n";
  }

  print "
          </select>
        </p>
        <p><input type='button' class='btn' value='prefill form' onclick=\"execute_ajax('print_top_of_form', 'entire_form_div', 'prefill_form');\" /></p>
      </form>
      <div id=prefill_status></div>
    </div>\n";
}

sub print_top_of_form {
  print "
      <h3>Enter Metadata</h3>
      <div>
        <form method='post' enctype='multipart/form-data' id='metadata_form'>
          <ul class='nav nav-pills nav-stacked' style=\"display:'';margin-bottom:0\">
            <li><a onclick=\"toggle('project_info_div');\" class='pill_incomplete' id='project_info_pill' style='font-size: 17px; font-weight: bold;'>1. enter project information</a></li>
            <div id='project_info_div' style='display: none;' class='well'>
              <p>Please enter your contact information below.  It is important that the PI and technical contact information (if different than the PI) is entered so that if a technical contact is no longer available, the PI can still gain access to their data.  Note that selecting 'other' under 'Project Funding' enables an additional text field where you can type in your funding source.</p>
              <p>Required project fields are marked with a red asterisk (&nbsp;<font style='color:red;font-size:20px;vertical-align:bottom;'>*</font>&nbsp;) and must be entered before continuing on to the rest of the form.</p>
              <p>The selected (checked) optional fields will be included in your spreadsheet whether you complete those fields now or after download.</p>
              <br />\n";

  my $help = "<script>";
  my @pi_fields = ();
  my @id_fields = ();
  my %field_definitions = ();
  foreach my $field (sort keys %{$json_meta_template->{'project'}{'project'}}) {
    if($field =~ /^PI_.*$/) {
      push @pi_fields, $field;
    } elsif($field =~ /^.*_id$/) {
      push @id_fields, $field;
    }
    $field_definitions{$field} = $json_meta_template->{'project'}{'project'}{$field}{'definition'};
    $field_definitions{$field} =~ s/'/\\'/g;
    my $fn = (exists $project_display_fields->{$field}) ? $project_display_fields->{$field} : $field;
    $help .= "\$('#project_$field').popover({ 'title': '$fn', 'content': '".$field_definitions{$field}."'});\n";
  }

  print "
              <table border=0>
                <tr>
                  <td style='width:430px;vertical-align:top;padding:8px;'>
                    <table border=0>
                      <tr><td colspan=2 style='padding:0px 0px 20px 0px;'><strong>Principal Investigator (PI) Information:</strong></td></tr>\n";

  foreach my $field (@pi_fields) {
    print &print_field($field, 'project', $json_meta_template->{'project'}{'project'}{$field}{'type'},
                       $json_meta_template->{'project'}{'project'}{$field}{'required'}, 0);
  }

  print "             <tr><td>&nbsp;</td></tr>
                      <tr><td colspan=2 style='padding:10px 0px 15px 0px;'><strong>dbXref ID's:</strong></td></tr>
                      <tr>
                        <td style='vertical-align:middle;width:195px;text-align:justify;padding:0px 10px 15px 10px;' colspan=2><p style='width:390px;'>Below you can enter project ID's from different analysis tools so that your dataset can be linked across these resources.</p></td>
                      </tr>\n";

  foreach my $field (@id_fields) {
    print &print_field($field, 'project', $json_meta_template->{'project'}{'project'}{$field}{'type'},
                       $json_meta_template->{'project'}{'project'}{$field}{'required'}, 0);
  }

  print "
                    </table>
                  </td>
                  <td style='width:430px;vertical-align:top;padding:8px;'>
                    <table border=0>
                      <tr><td colspan=2 style='padding:0px 0px 20px 0px;'><strong>Technical Contact Information:</strong></td></tr>\n";

  foreach my $field ('email', 'firstname', 'lastname', 'organization', 'organization_address', 'organization_country', 'organization_url') {
    print &print_field($field, 'project', $json_meta_template->{'project'}{'project'}{$field}{'type'},
                       $json_meta_template->{'project'}{'project'}{$field}{'required'}, 0);
  }

  print "
                    </table>
                  </td>
                </tr>
                <tr>
                  <td colspan=2 style='vertical-align:top;padding:8px;'>
                    <table border=0 style='width:850px;'>
                      <tr><td colspan=2 style='padding:10px 0px 20px 0px;'><strong>Project Information:</strong></td></tr>\n";

  print &print_field('project_name', 'project', $json_meta_template->{'project'}{'project'}{'project_name'}{'type'},
                     $json_meta_template->{'project'}{'project'}{'project_name'}{'required'}, 0);

  print &print_field('project_funding', 'project', $json_meta_template->{'project'}{'project'}{'project_funding'}{'type'},
                     $json_meta_template->{'project'}{'project'}{'project_funding'}{'required'}, 0);

  print &print_field('project_description', 'project', $json_meta_template->{'project'}{'project'}{'project_description'}{'type'},
                     $json_meta_template->{'project'}{'project'}{'project_description'}{'required'}, 0);

  print "
                    </table>
                  </td>
                </tr>
                <tr>
                  <td colspan=2 style='width:430px;vertical-align:top;padding:8px 8px 0px 8px;'>
                    <table border=0 style='width:850px;'>
                      <tr><td colspan=2 style='padding:10px 0px 20px 0px;'><strong>Other project information:</strong></td></tr>
                      <tr>
                        <td style='vertical-align:middle;text-align:justify;padding:0px 10px 15px 10px;' colspan=2><p style='width:390px;'>Below you can enter other project information about your dataset for which their may not be an input field. (e.g. contact phone number)</p></td>
                      </tr>\n";

  print &print_field('misc_param', 'project', $json_meta_template->{'project'}{'project'}{'misc_param'}{'type'},
                     $json_meta_template->{'project'}{'project'}{'misc_param'}{'required'}, 0);

  print "
                    </table>
                  </td>
                </tr>
                <tr>
                  <td>
                    <div id='project_misc_params_div' style='padding:0px 0px 0px 8px;'>
                    </div>
                    <p style='padding:8px 0px 0px 8px;'><a style='cursor:pointer;' onclick=\"addMiscParam('project', 'project_misc_params_div');\">+ click to add another miscellaneous parameter</a></p>
                  </td>
                </tr>
              </table>
              <br />
            </div>

            <li><a onclick=\"toggle('sample_set_div');\" class='pill_incomplete' id='sample_set_pill' style='font-size: 17px; font-weight: bold;'>2. enter sample set information</a></li>
            <div id='sample_set_div' style='display: none;' class='well'>
              <p>Enter the information below about your set of samples. First, indicate the total number of samples in your set. Second, tell us which environmental package your samples belong to. Then, indicate how many times each of your samples was sequenced by each sequencing method. Note, that it is allowable to indicate here if your samples were sequenced using more than one sequencing method.</p>
              <p>You must submit the information here before proceeding with the rest of the form.  If you edit this information, please click 'submit' below again before continuing with the rest of the form or your spreadsheet will not be filled in properly.</p>
              <br />
              <table border= 1 cellpadding=8>
                <tr>
                  <td style='vertical-align:middle;height:35px;text-align:center;width:100px'># of samples</td>
                  <td style='vertical-align:middle;height:35px;text-align:center;'>&nbsp;<font style='color:red;font-size:20px;vertical-align:bottom;'>*</font>&nbsp;environmental package</td>\n";

  my @ep_list = ('', sort keys %{$json_meta_template->{'ep'}});
  my @lib_list = keys %{$json_meta_template->{'library'}};
  foreach my $lib (sort @lib_list) {
    print "
                  <td style='vertical-align:middle;height:35px;text-align:center;width:100px'># of ".$lib_descriptions->{$lib}." libraries per sample</td>\n";
  }

  my $value = 0;
  if($previous_project ne "" && exists $json_project_data->{'samples'}) {
    $value = @{$json_project_data->{'samples'}};
  }
  print "
                </tr>
                <tr>
                  <td style='vertical-align:middle;height:35px;text-align:center;'><div id=\"sample_count_div\" class=\"control-group\" style=\"margin-bottom:0px\"><input style='width:60px;' type='text' name='sample_count' value='$value' onkeydown=\"return returnNumeric(event);\" /></div></td>
                  <td style='vertical-align:middle;height:35px;text-align:center;'><div id=\"env_package_div\" class=\"control-group\" style=\"margin-bottom:0px\">".$cgi->popup_menu( -name => 'env_package', -values => \@ep_list, -style=> "width:205px;", -default => '' , -project_required => 1)."</div></td>\n";

  foreach my $lib (sort @lib_list) {
    print "
                  <td style='vertical-align:middle;height:35px;text-align:center;'><div id=\"$lib\_count_div\" class=\"control-group\" style=\"margin-bottom:0px\"><input style='width:60px;' type='text' name='$lib\_count' value='0' onkeydown=\"return returnNumeric(event);\" /></div></td>\n";
  }

  print "
                </tr>
              </table>
              <br />
              <table cellpadding=8 border=0>
                <tr>
                  <td style='vertical-align:middle;'><input type='button' class='btn' value='submit' onclick=\"execute_ajax('print_bottom_of_form', 'bottom_of_form_div', 'metadata_form');\"></td>
                </tr>
              </table>
            </div>
          </ul>
          <div id='bottom_of_form_div'></div>
        </form>
      </div>
    </div>
    <br />
    <br />\n";
  print $help."</script>";

}

sub print_bottom_of_form {

  print "
         <ul class='nav nav-pills nav-stacked'>
            <li><a onclick=\"toggle('env_div');\" class='pill_incomplete' id='env_pill' style='font-size: 17px; font-weight: bold;'>3. enter environment information</a></li>
            <div id='env_div' style='display: none;' class='well'>
              <h3>enter environment information</h3>
              <br />
              <p>Use three different terms from controlled vocabularies for biome, environmental feature, and environmental material to classify your samples. Note that while the terms might not be perfect matches for your specific project they are primarily meant to allow use of your data by others. You can enter your detailed project description in the project tab at the top of this form.</p>
              <br />
              <table cellpadding=0 border=0>
                <tr>
                  <td align=center style='font-weight: bold;'>Biome</td>
                  <td align=center style='font-weight: bold;'>Environmental Feature</td>
                  <td align=center style='font-weight: bold;'>Environmental Material</td>
                </tr>
                <tr>
                  <td align=center>
                    <object classid='clsid:D27CDB6E-AE6D-11cf-96B8-444553540000'
                            id='OntologyTreeBiome' width='300' height='100%'
                            codebase='http://fpdownload.macromedia.com/get/flashplayer/current/swflash.cab'>
                            <param name='movie' value='http://keg.cs.uvic.ca/ncbo/ontologytree/OntologyTree.swf' />
                            <param name='quality' value='high' />
                            <param name='bgcolor' value='#ffffff' />
                            <param name='allowScriptAccess' value='always' />
                            <param name='flashVars' value='ontology=1069&rootconceptid=ENVO:00000428&alerterrors=false&canchangeontology=false&canchangeroot=false&virtual=true&server=http://rest.bioontology.org/bioportal' />
                            <embed src='http://keg.cs.uvic.ca/ncbo/ontologytree/OntologyTree.swf' quality='high' bgcolor='#ffffff'
                                    width='300' height='100%' name='OntologyTreeBiome' align='middle'
                                    play='true'
                                    loop='false'
                                    allowScriptAccess='always'
                                    type='application/x-shockwave-flash'
                                    flashVars='ontology=1069&rootconceptid=ENVO:00000428&alerterrors=false&canchangeontology=false&canchangeroot=false&virtual=true&server=http://rest.bioontology.org/bioportal'
                                    pluginspage='http://www.adobe.com/go/getflashplayer'>
                            </embed>
                    </object>
                  </td>
                  <td align=center>
                    <object classid='clsid:D27CDB6E-AE6D-11cf-96B8-444553540000'
                            id='OntologyTreeEnvFeature' width='300' height='100%'
                            codebase='http://fpdownload.macromedia.com/get/flashplayer/current/swflash.cab'>
                            <param name='movie' value='http://keg.cs.uvic.ca/ncbo/ontologytree/OntologyTree.swf' />
                            <param name='quality' value='high' />
                            <param name='bgcolor' value='#ffffff' />
                            <param name='allowScriptAccess' value='always' />
                            <param name='flashVars' value='ontology=1069&rootconceptid=ENVO:00002297&alerterrors=false&canchangeontology=false&canchangeroot=false&virtual=true&server=http://rest.bioontology.org/bioportal' />
                            <embed src='http://keg.cs.uvic.ca/ncbo/ontologytree/OntologyTree.swf' quality='high' bgcolor='#ffffff'
                                    width='300' height='100%' name='OntologyTreeEnvFeature' align='middle'
                                    play='true'
                                    loop='false'
                                    allowScriptAccess='always'
                                    type='application/x-shockwave-flash'
                                    flashVars='ontology=1069&rootconceptid=ENVO:00002297&alerterrors=false&canchangeontology=false&canchangeroot=false&virtual=true&server=http://rest.bioontology.org/bioportal'
                                    pluginspage='http://www.adobe.com/go/getflashplayer'>
                            </embed>
                    </object>
                  </td>
                  <td align=center>
                    <object classid='clsid:D27CDB6E-AE6D-11cf-96B8-444553540000'
                            id='OntologyTreeEnvMaterial' width='300' height='100%'
                            codebase='http://fpdownload.macromedia.com/get/flashplayer/current/swflash.cab'>
                            <param name='movie' value='http://keg.cs.uvic.ca/ncbo/ontologytree/OntologyTree.swf' />
                            <param name='quality' value='high' />
                            <param name='bgcolor' value='#ffffff' />
                            <param name='allowScriptAccess' value='always' />
                            <param name='flashVars' value='ontology=1069&rootconceptid=ENVO:00010483&alerterrors=false&canchangeontology=false&canchangeroot=false&virtual=true&server=http://rest.bioontology.org/bioportal' />
                            <embed src='http://keg.cs.uvic.ca/ncbo/ontologytree/OntologyTree.swf' quality='high' bgcolor='#ffffff'
                                    width='300' height='100%' name='OntologyTreeEnvMaterial' align='middle'
                                    play='true'
                                    loop='false'
                                    allowScriptAccess='always'
                                    type='application/x-shockwave-flash'
                                    flashVars='ontology=1069&rootconceptid=ENVO:00010483&alerterrors=false&canchangeontology=false&canchangeroot=false&virtual=true&server=http://rest.bioontology.org/bioportal'
                                    pluginspage='http://www.adobe.com/go/getflashplayer'>
                            </embed>
                    </object>
                  </td>
                </tr>
                <tr>
                  <td align=center><input type='button' style='width: 250px' class='btn' value='enter selected term as biome' onclick=\"setEnvField('OntologyTreeBiome');\" /></td>
                  <td align=center><input type='button' style='width: 250px' class='btn' value='enter selected term as env feature' onclick=\"setEnvField('OntologyTreeEnvFeature')\" /></td>
                  <td align=center><input type='button' style='width: 250px' class='btn' value='enter selected term as env material' onclick=\"setEnvField('OntologyTreeEnvMaterial')\" /></td>
                </tr>
                <tr>
                  <td align=center><input type='text' name='sample_biome' readonly /></td>
                  <td align=center><input type='text' name='sample_feature' readonly /></td>
                  <td align=center><input type='text' name='sample_material' readonly /></td>
                </tr>
              </table>
            </div>

            <li><a onclick=\"toggle('sample_info_div');\" class='pill_incomplete' id='sample_info_pill' style='font-size: 17px; font-weight: bold;'>4. enter sample information</a></li>
            <div id='sample_info_div' style='display: none;' class='well'>
              <h3>enter sample information</h3>
              <br />
              <p>Please enter only information that is consistent across all samples. This data will be pre-filled in the spreadsheet.</p>
              <p>Required sample fields are marked with a blue asterisk (&nbsp;<font style='color:blue;font-size:20px;vertical-align:bottom;'>*</font>&nbsp;), because unlike required project fields, they can be entered after downloading your spreadsheet.</p>
              <p>The selected (checked) optional fields will be included in your spreadsheet whether you complete those fields now or after download.</p>\n";

  my $help = "<script>";
  my @opt_sample_fields = ();
  my %field_definitions = ();
  foreach my $field (keys %{$json_meta_template->{'sample'}{'sample'}}) {
    if($json_meta_template->{'sample'}{'sample'}{$field}{'required'} != 1) {
      push @opt_sample_fields, $field;
    }
    $field_definitions{$field} = $json_meta_template->{'sample'}{'sample'}{$field}{'definition'};
    $field_definitions{$field} =~ s/'/\\'/g;
    my $fn = (exists $sample_display_fields->{$field}) ? $sample_display_fields->{$field} : $field;
    $help .= "\$('#sample_$field').popover({ 'title': '$fn', 'content': '".$field_definitions{$field}."'});\n";
  }
  
  print "
              <br />
              <table cellpadding=8 border=0>
                <tr>
                  <td style='width:430px;vertical-align: top;'>
                    <!--<table border= 1><tr><td style='padding:5px;'>-->
                    <table border=0>
                      <tr><td colspan=2 style='padding:0px 0px 20px 0px;'><strong>Date/Time Information:</strong></td></tr>\n";

  print &print_field('collection_date', 'sample', $json_meta_template->{'sample'}{'sample'}{'collection_date'}{'type'},
                     $json_meta_template->{'sample'}{'sample'}{'collection_date'}{'required'}, 0);

  print &print_field('collection_time', 'sample', $json_meta_template->{'sample'}{'sample'}{'collection_time'}{'type'},
                     $json_meta_template->{'sample'}{'sample'}{'collection_time'}{'required'}, 0);

  print &print_field('collection_timezone', 'sample', $json_meta_template->{'sample'}{'sample'}{'collection_timezone'}{'type'},
                     $json_meta_template->{'sample'}{'sample'}{'collection_timezone'}{'required'}, 0);

  print "
                    </table>
                    <!--</td></tr></table>-->
                    <br />
                    <!--<table border= 1><tr><td style='padding:5px;'>-->
                    <table border=0>
                      <tr><td colspan=2 style='padding:20px 0px 20px 0px;'><strong>Location Information:</strong></td></tr>\n";

  print "
                      <tr>
                        <td style='vertical-align:middle;width:195px;text-align:justify;padding:0px 10px 15px 10px;' colspan=2><p style='width:390px;'>By entering an address or location below we can search google maps to try and identify the latitude and longitude of your location.  If you find that this does not work for your location, you can try using Google Maps <a href=\"https://maps.google.com/\" target=\"_blank\">here</a> and the instructions <a href=\"http://support.google.com/maps/bin/answer.py?hl=en&answer=1334236\" target=\"_blank\">here</a> to identify the latitude and longitude of your desired location.</p><div id='google_maps_address'></div></td>
                      </tr>
                      <tr>
                        <td style='vertical-align:middle;width:195px'>&nbsp;<font style='color:blue;font-size:20px;vertical-align:bottom;'>*</font>&nbsp;&nbsp;Location/Address<span id='sample_location'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td style='vertical-align:middle;'><input type='text' name='sample_location' style='width:195px;' value = ''></td>
                      </tr>
                      <tr style='height:50px;'>
                        <td>&nbsp;</td>
                        <td style='vertical-align:middle;padding:5px;'><input type='button' name='search_address' class='btn' value='Search for Latitude/Longitude' onclick=\"execute_ajax('search_address', 'search_address_div', 'metadata_form');\"></td>
                      </tr>
                    </table>
                    <div id='search_address_div'></div>
                    <table border=0>
                      <tr>
                        <td style='vertical-align:middle;width:195px'>&nbsp;<font style='color:blue;font-size:20px;vertical-align:bottom;'>*</font>&nbsp;&nbsp;Latitude<span id='sample_latitude'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td style='vertical-align:middle;'><input type='text' name='sample_latitude' style='width:195px;' value = ''></td>
                      </tr>
                      <tr>
                        <td style='vertical-align:middle;width:195px'>&nbsp;<font style='color:blue;font-size:20px;vertical-align:bottom;'>*</font>&nbsp;&nbsp;Longitude<span id='sample_longitude'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td style='vertical-align:middle;'><input type='text' name='sample_longitude' style='width:195px;' value = ''></td>
                      </tr>\n";

  print &print_field('country', 'sample', $json_meta_template->{'sample'}{'sample'}{'country'}{'type'},
                     $json_meta_template->{'sample'}{'sample'}{'country'}{'required'}, 0);

  print "
                      <tr>
                        <td colspan=2 style='vertical-align:top;'>
                          <table border=0>
                            <tr><td colspan=2 style='padding:20px 0px 20px 0px;'><strong>Other sample information:</strong></td></tr>
                            <tr>
                              <td style='vertical-align:middle;text-align:justify;padding:0px 10px 15px 10px;' colspan=2><p style='width:390px;'>Below you can enter other sample information for which their may not be an input field. (e.g. sample density)</p></td>
                            </tr>\n";

  print &print_field('misc_param', 'sample', $json_meta_template->{'sample'}{'sample'}{'misc_param'}{'type'},
                     $json_meta_template->{'sample'}{'sample'}{'misc_param'}{'required'}, 0);

  print "
                          </table>
                        </td>
                      </tr>
                      <tr>
                        <td colspan=2 style='vertical-align:top;'>
                          <div id='sample_misc_params_div'>
                          </div>
                          <p style='width:100%;padding:8px 0px 0px 0px;'><a style='cursor:pointer;' onclick=\"addMiscParam('sample', 'sample_misc_params_div');\">+ click to add another miscellaneous parameter</a></p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td style='width:430px;vertical-align: top;'>
                    <table border=0>
                      <tr>
                        <td colspan=2 style='padding:0px 0px 20px 0px;'>
                          <strong>Optional Fields:</strong>&nbsp;&nbsp;&nbsp;&nbsp;
                          <input type='radio' name='toggle_select_sample' onchange=\"selectAllOptionalFields('sample_');\">&nbsp;&nbsp;Select all&nbsp;&nbsp;&nbsp;&nbsp;
                          <input type='radio' name='toggle_select_sample' checked onchange=\"deselectAllOptionalFields('sample_');\">&nbsp;&nbsp;Deselect all
                        </td>
                      </tr>\n";

  my @top_fields = ('altitude', 'biotic_relationship', 'continent', 'depth', 'elevation', 'ph',
                    'rel_to_oxygen', 'sample_id', 'samp_collect_device', 'samp_size', 'temperature');
  my %top_fields_hash = ();
  foreach my $field (@top_fields) {
    $top_fields_hash{$field} = 1;
    print &print_field($field, 'sample', $json_meta_template->{'sample'}{'sample'}{$field}{'type'},
                       $json_meta_template->{'sample'}{'sample'}{$field}{'required'}, 1);
  }

  print "
                    </table>
                    <br />
                    <p style='padding:10px;'><a style='cursor:pointer;' onclick=\"toggle('sample_more_fields_div');\" >Click to view/hide more fields</a></p>
                    <br />
                    <div id='sample_more_fields_div' style='display: none;'>
                      <table>\n";

  foreach my $field (sort @opt_sample_fields) {
    unless($field eq 'misc_param' || exists $top_fields_hash{$field}) {
      print &print_field($field, 'sample', $json_meta_template->{'sample'}{'sample'}{$field}{'type'},
                         $json_meta_template->{'sample'}{'sample'}{$field}{'required'}, 1);
    }
  }

  print "
                      </table>
                    </div>
                  </td>
                </tr>
              </table>
              <br />
            </div>\n";

  my $tab_count = 4;
  my @lib_list = ();
  foreach my $lib (keys %{$json_meta_template->{'library'}}) {
    if($cgi->param("$lib\_count") > 0) {
      push @lib_list, $lib;
    }
  }
  foreach my $lib (sort @lib_list) {
    ++$tab_count;
    print "
            <li><a onclick=\"toggle('$lib\_info_div');\" class='pill_incomplete' id='$lib\_info_pill' style='font-size: 17px; font-weight: bold;'>$tab_count. enter ".$lib_descriptions->{$lib}." information</a></li>
            <div id='$lib\_info_div' style='display: none;' class='well'>
              <h3>enter ".$lib_descriptions->{$lib}." information</h3>
              <br />
              <p>Please enter only information that is consistent across all ".$lib_descriptions->{$lib}." libraries. This data will be pre-filled in the spreadsheet.</p>
              <p>Required ".$lib_descriptions->{$lib}." library fields are marked with a blue asterisk (&nbsp;<font style='color:blue;font-size:20px;vertical-align:bottom;'>*</font>&nbsp;), because unlike required project fields, they can be entered after downloading your spreadsheet.</p>
              <p>The selected (checked) optional fields will be included in your spreadsheet whether you complete those fields now or after download.</p>\n";

    my @req_library_fields = ();
    my @opt_library_fields = ();
    %field_definitions = ();
    foreach my $field (keys %{$json_meta_template->{'library'}{$lib}}) {
      if($json_meta_template->{'library'}{$lib}{$field}{'required'} == 1) {
        push @req_library_fields, $field;
      } else {
        push @opt_library_fields, $field;
      }
      $field_definitions{$field} = $json_meta_template->{'library'}{$lib}{$field}{'definition'};
      $field_definitions{$field} =~ s/'/\\'/g;
      my $fn = (exists $library_display_fields->{$field}) ? $library_display_fields->{$field} : $field;
      $help .= "\$('#$lib\_$field').popover({ 'title': '$fn', 'content': '".$field_definitions{$field}."'});\n";
    }

    print "
              <br />
              <table cellpadding=8 border=0>
                <tr style='vertical-align:top;'>
                  <td style='width:430px'>
                    <table border=0>
                      <tr><td colspan=2 style='padding:0px 0px 20px 0px;'><strong>Required Field(s):</strong></td></tr>\n";

    foreach my $field (sort @req_library_fields) {
      unless($field eq 'seq_meth' || $field eq 'investigation_type' || $field eq 'sample_name') {
        print &print_field($field, 'library', $json_meta_template->{'library'}{$lib}{$field}{'type'},
                           $json_meta_template->{'library'}{$lib}{$field}{'required'}, 0, $lib);
      }
    }

    print "
                      <tr><td>&nbsp;</td></tr>
                      <tr><td colspan=2 style='padding:10px 0px 20px 0px;'><strong>Sequencing information</strong></td></tr>\n";

    foreach my $field ('seq_meth', 'seq_make', 'seq_model', 'seq_chem', 'seq_url', 'seq_center', 'seq_quality_check') {
      print &print_field($field, 'library', $json_meta_template->{'library'}{$lib}{$field}{'type'},
                         $json_meta_template->{'library'}{$lib}{$field}{'required'}, 0, $lib);
    }

    if($lib eq 'mimarks-survey') {
      my $field = 'seq_direction';
      print &print_field($field, 'library', $json_meta_template->{'library'}{$lib}{$field}{'type'},
                         $json_meta_template->{'library'}{$lib}{$field}{'required'}, 0, $lib);
    }


    if($lib eq 'metagenome') {
      print "
                      <tr><td>&nbsp;</td></tr>
                      <tr><td colspan=2 style='padding:10px 0px 20px 0px;'><strong>Assembly information</strong></td></tr>\n";

      my $field_name = 'metagenome_assembly_name';
      my $displayed_field = 'Assembly Name';
      print "
                      <tr>
                        <td style='vertical-align:middle;width:195px;'><input type=\"checkbox\" name=\"$field_name\_checkbox\" selectall=\"0\" checked />&nbsp;&nbsp;$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td style='vertical-align:middle;'><input style='width:195px;' type='text' name='$field_name' value = ''></td>
                      </tr>\n";

      $field_name = 'metagenome_assembly_program';
      $displayed_field = 'Assembly Program';
      my @values = ('', 'ABySS', 'cap3', 'metaBDA', 'metavelvet', 'MIRA', 'PCAP', 'phrap', 'velvet');
      print "
                      <tr>
                        <td style='vertical-align:middle;width:195px;'><input type=\"checkbox\" name=\"$field_name\_checkbox\" selectall=\"0\" checked />&nbsp;&nbsp;$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td>".$cgi->popup_menu( -name => "$field_name", -values => \@values, -style=> "width:205px;", -default => '' )."</td>
                      </tr>\n";
      $help .= "\$('#$field_name').popover({ 'title': '$displayed_field', 'content': 'Program used to assemble your sequences.'});\n";

      $field_name = 'metagenome_error_rate';
      $displayed_field = 'Error Rate';
      print "
                      <tr>
                        <td style='vertical-align:middle;width:195px;'><input type=\"checkbox\" name=\"$field_name\_checkbox\" selectall=\"0\" checked />&nbsp;&nbsp;$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td style='vertical-align:middle;'><div id=\"$field_name\_div\" class=\"control-group\" style=\"margin-bottom:0px\"><input style='width:100px;' type='text' name='$field_name' value = '' displayField='$displayed_field' validate='float' onkeydown=\"return returnNumericDec(event);\"> (errors per 1kbp)</div></td> 
                      </tr>\n";
      $help .= "\$('#$field_name').popover({ 'title': '$displayed_field', 'content': 'Estimated error rate associated with the finished sequences.  Error rate of 1 in 1,000bp.'});\n";

      $field_name = 'metagenome_assembly_comments';
      $displayed_field = 'Assembly Comments';
      print "
                      <tr>
                        <td style='vertical-align:middle;width:195px;'><input type=\"checkbox\" name=\"$field_name\_checkbox\" selectall=\"0\" checked />&nbsp;&nbsp;$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td style='vertical-align:middle;'><input style='width:195px;' type='text' name='$field_name' value = ''></td>
                      </tr>\n";
      $help .= "\$('#$field_name').popover({ 'title': '$displayed_field', 'content': 'Enter other information about the sequence assembly that was performed (e.g. method of calculation).'});\n";

      print "
                      <tr>
                        <td colspan=2 style='vertical-align:middle;width:195px;text-align:justify;padding:0px 10px 15px 10px;'><p style='width:390px;'>Note that 'Assembly Program', 'Error Rate', and 'Assembly Comments' will be combined into one field ('Assembly') in the generated spreadsheet.</p></td>
                      <tr>\n";
    }

    print "
                      <tr>
                        <td colspan=2 style='vertical-align:top;'>
                          <table border=0>
                            <tr><td colspan=2 style='padding:20px 0px 20px 0px;'><strong>Other sample information:</strong></td></tr>
                            <tr>
                              <td style='vertical-align:middle;text-align:justify;padding:0px 10px 15px 10px;' colspan=2><p style='width:390px;'>Below you can enter other sample information for which their may not be an input field. (e.g. sample density)</p></td>
                            </tr>\n";

    print &print_field('misc_param', 'library', $json_meta_template->{'library'}{$lib}{'misc_param'}{'type'},
                       $json_meta_template->{'library'}{$lib}{'misc_param'}{'required'}, 0, $lib);

    print "
                          </table>
                        </td>
                      </tr>
                      <tr>
                        <td colspan=2 style='vertical-align:top;'>
                          <div id='$lib\_misc_params_div'>
                          </div>
                          <p style='width:100%;padding:8px 0px 0px 0px;'><a style='cursor:pointer;' onclick=\"addMiscParam('$lib', '$lib\_misc_params_div');\">+ click to add another miscellaneous parameter</a></p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td style='width:430px;vertical-align: top;'>
                    <table border=0>
                      <tr>
                        <td colspan=2 style='padding:0px 0px 20px 0px;'>
                          <strong>More Optional Fields:</strong>&nbsp;&nbsp;&nbsp;&nbsp;
                          <input type='radio' name='toggle_select_$lib' onchange=\"selectAllOptionalFields('$lib\_');\">&nbsp;&nbsp;Select all&nbsp;&nbsp;&nbsp;&nbsp;
                          <input type='radio' name='toggle_select_$lib' checked onchange=\"deselectAllOptionalFields('$lib\_');\">&nbsp;&nbsp;Deselect all
                        </td>
                      </tr>\n";

    my @top_fields = ();

    if($lib eq 'metagenome') {
      @top_fields = ('mgrast_id', 'metagenome_id', 'pubmed_id', 'gold_id', 'file_name', 'file_checksum', 'adapters');
    } elsif($lib eq 'metatranscriptome') {
      @top_fields = ('mgrast_id', 'metagenome_id', 'pubmed_id', 'gold_id', 'file_name', 'file_checksum', 'cdna_ampf_meth', 'cdna_purif_meth', 'rev_trans_meth', 'rrna_removal_meth', 'samp_isol_dur');
    } elsif($lib eq 'mimarks-survey') {
      @top_fields = ('mgrast_id', 'metagenome_id', 'file_name', 'file_checksum', 'adapters', 'amp_polymerase', 'denaturation_duration_initial', 'denaturation_temp_initial', 'cycle_annealing_duration', 'cycle_annealing_method', 'cycle_annealing_temp', 'cycle_count', 'cycle_denaturation_duration', 'cycle_denaturation_temp', 'cycle_extension_duration', 'cycle_extension_temp', 'extension_duration_final', 'extension_temp_final', 'forward_primers', 'forward_primer_final_conc', 'forward_barcodes', 'reverse_primers', 'reverse_primer_final_conc', 'reverse_barcodes', 'pcr_buffer_pH', 'pcr_clean_up_kits', 'pcr_clean_up_methods', 'pcr_notes', 'pcr_replicates', 'pcr_volume', 'target_subfragment', 'thermocycler');
    }

    my %top_fields_hash = ();
    foreach my $field (@top_fields) {
      $top_fields_hash{$field} = 1;
      print &print_field($field, 'library', $json_meta_template->{'library'}{$lib}{$field}{'type'},
                         $json_meta_template->{'library'}{$lib}{$field}{'required'}, 1, $lib);
    }

    print "
                      </table>
                      <br />
                      <p style='padding:10px;'><a style='cursor:pointer;' onclick=\"toggle('$lib\_more_fields_div');\" >Click to view/hide more fields</a></p>
                      <br />
                      <div id='$lib\_more_fields_div' style='display: none;'>
                        <table>\n";

    foreach my $field (sort @opt_library_fields) {
      unless($field eq 'misc_param' || $field eq 'run_machine_type' || exists $top_fields_hash{$field} ||
             $field =~ /^assembly.*$/ || $field =~ /^seq_.*$/) {
        print &print_field($field, 'library', $json_meta_template->{'library'}{$lib}{$field}{'type'},
                           $json_meta_template->{'library'}{$lib}{$field}{'required'}, 1, $lib);
      }
    }

    print "
                    </table>
                  </td>
                </tr>
              </table>
              <br />
            </div>\n";
  }

  print "
          <br />
          <table cellpadding=8 border=0>
            <tr>
              <td style='vertical-align:middle;'><input type='button' name='generate_spreadsheet' class='btn' value='click to generate spreadsheet' onclick=\"execute_ajax('generate_excel_spreadsheet', 'spreadsheet_generation_status_div', 'metadata_form');\"></td>
            </tr>
          </table>
          <br />
          <div id='spreadsheet_generation_status_div'>
          </div>
          </ul>\n";

  print $help."
  \$('#sample_collection_date_div').datepicker({
    format: 'yyyy-mm-dd'
  });
  \$('.timepicker-1').timepicker({
    minuteStep: 1,
    defaultTime: false,
    showSeconds: true,
    showMeridian: false
  });
  </script>";
}

sub search_address {
  my $json = new JSON();
  my $location = $cgi->param('sample_location');

  my $url = "https://maps.googleapis.com/maps/api/geocode/json?sensor=false&address=$location";
  my $ua = LWP::UserAgent->new;
  my $res = $ua->get($url);
  my $json_google_map = $json->decode($res->content);

  print "
                    <table border=0>
                      <tr>
                        <td style='vertical-align:middle;width:195px;' >Searched the location:</td>
                        <td style='padding:10px;width:202px'>$location</td>
                      </tr>\n";

  my $formatted_address = $json_google_map->{'results'}[0]->{'formatted_address'};
  if($formatted_address) {
    my $latitude = $json_google_map->{'results'}[0]->{'geometry'}{'location'}{'lat'};
    my $longitude = $json_google_map->{'results'}[0]->{'geometry'}{'location'}{'lng'};
    print "
                      <script>
                        document.forms['metadata_form'].elements['sample_latitude'].value = $latitude;
                        document.forms['metadata_form'].elements['sample_longitude'].value = $longitude;
                      </script>
                      <tr>
                        <td style='vertical-align:middle;width:195px;'>Top Google Result:</td>
                        <td style='padding:10px;width:202px;'>$formatted_address</td>
                      </tr>
                      <tr>
                        <td style='vertical-align:middle;width:195px;text-align:justify;padding:10px 20px 30px 10px;' colspan=2>Latitude and Longitude for this address were entered below.  If Google returned address is not correct, please try searching again or refer to the Google Maps links above.</td>
                      </tr>\n";
  } else {
    print "
                      <script>
                        document.forms['metadata_form'].elements['sample_latitude'].value = '';
                        document.forms['metadata_form'].elements['sample_longitude'].value = '';
                      </script>
                      <tr>
                        <td style='vertical-align:middle;text-align:justify;padding:10px 20px 30px 10px;' colspan=2>Google Maps returned no result for this address.</td>
                      </tr>\n";
  }
  print "
                    </table>\n";
}

sub generate_excel_spreadsheet {
  my ($file_handle, $filename) = tempfile("metadata_spreadsheet_XXXXXXX", DIR => './Tmp/', SUFFIX => '.xls');
  my $workbook  = Spreadsheet::WriteExcel->new($file_handle);

  # README worksheet ###########################
  my $readme_worksheet = $workbook->add_worksheet('README');

  my @readme = ('MG-RAST Metadata Spreadsheet',
          '',
          'project tab: enter values for one project in first row',
          'sample tab: enter values for one or more samples, one sample per row',
          'library tab: enter values for each sample (including sample name) in appropriate library type, one library per row',
          'ep (environmental package) tab: enter values for each sample (including sample name) in appropriate ep type, one ep per row',
          '',
          'pre-filled rows:',
          '1. metadata label - required fields are in red',
          '2. label description - includes units if applicable',
          '',
          'NOTE:',
          '1. Please enter data starting with first empty row, do not overwrite pre-filled rows',
          '2. Each sample must have only one enviromental package associated with it',
          '3. Each sample must have one, but may have more than one, library associated with it',
          '4. Library field metagenome_name must be unique for each library, and will be the name of the MG-RAST metagenome');

  for(my $row=0; $row<@readme; ++$row) {
    $readme_worksheet->write($row, 0, $readme[$row]);
  }

  my $format = $workbook->add_format();
  $format->set_color('red');

  # project worksheet ##########################
  my $project_worksheet = $workbook->add_worksheet('project');

  my @req_project_fields = ();
  my @opt_project_fields = ();
  my %field_definitions = ();
  foreach my $field (keys %{$json_meta_template->{'project'}{'project'}}) {
    if($json_meta_template->{'project'}{'project'}{$field}{'required'} == 1 && $field ne 'project_name') {
      push @req_project_fields, $field;
    } else {
      push @opt_project_fields, $field;
    }
    $field_definitions{$field} = $json_meta_template->{'project'}{'project'}{$field}{'definition'};
  }

  my $col = 0;
  foreach my $field ('project_name', sort @req_project_fields) {
    $project_worksheet->write(0, $col, $field, $format);
    $project_worksheet->write(1, $col, $field_definitions{$field});
    $project_worksheet->write(2, $col, decode("utf8", $cgi->param("project_$field")));
    ++$col;
  }

  foreach my $field (sort @opt_project_fields) {
    if($cgi->param("project_$field\_checkbox") && $field ne 'misc_param') {
      $project_worksheet->write(0, $col, $field);
      $project_worksheet->write(1, $col, $field_definitions{$field});
      if($field eq 'project_funding' && $cgi->param("project_project_funding") eq 'Other - enter text') {
        $project_worksheet->write(2, $col, decode("utf8", $cgi->param("project_other_funding")));
      } elsif($field eq 'project_description' &&
              $cgi->param("project_project_description") eq 'This project explores ... with xxx samples from nn different locations...') {
        # Do nothing here.  We just want to prevent the default project_description text from being entered.
      } else {
        $project_worksheet->write(2, $col, decode("utf8", $cgi->param("project_$field")));
      }
      ++$col;
    }
  }

  for(my $i=1; $i<=10; ++$i) {
    my $field = "misc_param";
    if($i > 1) { $field = "misc_param_$i"; }
    if($cgi->param("project_$field\_checkbox")) {
      $project_worksheet->write(0, $col, $field);
      $project_worksheet->write(1, $col, $field_definitions{'misc_param'});
      $project_worksheet->write(2, $col, decode("utf8", $cgi->param("project_$field")));
      ++$col;
    }
  }

  # sample worksheet ###########################
  my $sample_worksheet = $workbook->add_worksheet('sample');

  my $sample_count = $cgi->param('sample_count');
  my @req_sample_fields = ();
  my @opt_sample_fields = ();
  %field_definitions = ();
  foreach my $field (keys %{$json_meta_template->{'sample'}{'sample'}}) {
    if($json_meta_template->{'sample'}{'sample'}{$field}{'required'} == 1 && $field ne 'sample_name') {
      push @req_sample_fields, $field;
    } else {
      push @opt_sample_fields, $field;
    }
    $field_definitions{$field} = $json_meta_template->{'sample'}{'sample'}{$field}{'definition'};
  }

  $col = 0;
  foreach my $field ('sample_name', sort @req_sample_fields) {
    $sample_worksheet->write(0, $col, $field, $format);
    $sample_worksheet->write(1, $col, $field_definitions{$field});
    for(my $sample_counter=1; $sample_counter<=$sample_count; ++$sample_counter) {
      if($field eq 'sample_name') {
        $sample_worksheet->write(1+$sample_counter, $col, "Sample$sample_counter");
      } elsif($field eq 'env_package') {
        $sample_worksheet->write(1+$sample_counter, $col, $cgi->param("env_package"));
      } else {
        $sample_worksheet->write(1+$sample_counter, $col, decode("utf8", $cgi->param("sample_$field")));
      }
    }
    ++$col;
  }

  foreach my $field (sort @opt_sample_fields) {
    if($cgi->param("sample_$field\_checkbox") && $field ne 'misc_param') {
      $sample_worksheet->write(0, $col, $field);
      $sample_worksheet->write(1, $col, $field_definitions{$field});
      for(my $sample_counter=1; $sample_counter<=$sample_count; ++$sample_counter) {
        $sample_worksheet->write(1+$sample_counter, $col, decode("utf8", $cgi->param("sample_$field")));
      }
      ++$col;
    }
  }

  for(my $i=1; $i<=10; ++$i) {
    my $field = "misc_param";
    if($i > 1) { $field = "misc_param_$i"; }
    if($cgi->param("sample_$field\_checkbox")) {
      $sample_worksheet->write(0, $col, $field);
      $sample_worksheet->write(1, $col, $field_definitions{'misc_param'});
      for(my $sample_counter=1; $sample_counter<=$sample_count; ++$sample_counter) {
        $sample_worksheet->write(1+$sample_counter, $col, decode("utf8", $cgi->param("sample_$field")));
      }
      ++$col;
    }
  }

  # library worksheets #########################
  my @lib_list = keys %{$json_meta_template->{'library'}};
  foreach my $lib (sort @lib_list) {
    my $lib_count = $cgi->param($lib."_count");
    unless($lib_count > 0) {
      next;
    }
    my $library_worksheet = $workbook->add_worksheet("library $lib");

    my @req_library_fields = ();
    my @opt_library_fields = ();
    %field_definitions = ();
    foreach my $field (keys %{$json_meta_template->{'library'}{$lib}}) {
      if($json_meta_template->{'library'}{$lib}{$field}{'required'} == 1 && $field !~ /^\S+_name$/) {
        push @req_library_fields, $field;
      } else {
        push @opt_library_fields, $field;
      }
      $field_definitions{$field} = $json_meta_template->{'library'}{$lib}{$field}{'definition'};
    }

    $col = 0;
    foreach my $field ('sample_name', 'metagenome_name', sort @req_library_fields) {
      $library_worksheet->write(0, $col, $field, $format);
      $library_worksheet->write(1, $col, $field_definitions{$field});
      for(my $sample_counter=1; $sample_counter<=$sample_count; ++$sample_counter) {
        for(my $lib_counter=1; $lib_counter<=$lib_count; ++$lib_counter) {
          if($field eq 'sample_name') {
            $library_worksheet->write(1+$lib_counter+(($sample_counter-1)*$lib_count), $col, "Sample$sample_counter");
          } elsif($field eq 'investigation_type') {
            $library_worksheet->write(1+$lib_counter+(($sample_counter-1)*$lib_count), $col, "$lib");
          } else {
            $library_worksheet->write(1+$lib_counter+(($sample_counter-1)*$lib_count), $col, decode("utf8", $cgi->param($lib."_".$field)));
          }
        }
      }
      ++$col;
    }

    sort_opt_library_fields(\@opt_library_fields);
    foreach my $field (@opt_library_fields) {
      if($field eq 'assembly') {
        my @info = ();
        foreach my $sub_field ("assembly_program", "error_rate", "assembly_comments") {
          if($cgi->param("$lib\_$sub_field\_checkbox")) {
            if($sub_field eq "error_rate" && $cgi->param("$lib\_$sub_field")) {
              push @info, $cgi->param("$lib\_$sub_field")." errors/kbp";
            } elsif($cgi->param("$lib\_$sub_field")) {
              push @info, $cgi->param("$lib\_$sub_field");
            }
          }
        }
        my $str = join(" -- ", @info);
        $library_worksheet->write(0, $col, $field);
        $library_worksheet->write(1, $col, $field_definitions{$field});
        for(my $sample_counter=1; $sample_counter<=$sample_count; ++$sample_counter) {
          for(my $lib_counter=1; $lib_counter<=$lib_count; ++$lib_counter) {
            $library_worksheet->write(1+$lib_counter+(($sample_counter-1)*$lib_count), $col, decode("utf8", $str));
          }
        }
        ++$col;
      } elsif($cgi->param("$lib\_$field\_checkbox") && $field ne 'misc_param') {
        $library_worksheet->write(0, $col, $field);
        $library_worksheet->write(1, $col, $field_definitions{$field});
        for(my $sample_counter=1; $sample_counter<=$sample_count; ++$sample_counter) {
          for(my $lib_counter=1; $lib_counter<=$lib_count; ++$lib_counter) {
            $library_worksheet->write(1+$lib_counter+(($sample_counter-1)*$lib_count), $col, decode("utf8", $cgi->param($lib."_".$field)));
          }
        }
        ++$col;
      }
    }

    for(my $i=1; $i<=10; ++$i) {
      my $field = "misc_param";
      if($i > 1) { $field = "misc_param_$i"; }
      if($cgi->param("$lib\_$field\_checkbox")) {
        $library_worksheet->write(0, $col, $field);
        $library_worksheet->write(1, $col, $field_definitions{'misc_param'});
        for(my $sample_counter=1; $sample_counter<=$sample_count; ++$sample_counter) {
          for(my $lib_counter=1; $lib_counter<=$lib_count; ++$lib_counter) {
            $library_worksheet->write(1+$lib_counter+(($sample_counter-1)*$lib_count), $col, decode("utf8", $cgi->param("$lib\_$field")));
          }
        }
        ++$col;
      }
    }
  }

  # ep worksheet ###############################
  my $ep = $cgi->param("env_package");
  my $ep_worksheet = $workbook->add_worksheet("ep $ep");

  my @req_ep_fields = ();
  my @opt_ep_fields = ();
  %field_definitions = ();
  foreach my $field (keys %{$json_meta_template->{'ep'}{$ep}}) {
    if($json_meta_template->{'ep'}{$ep}{$field}{'required'} == 1) {
      push @req_ep_fields, $field;
    } else {
      push @opt_ep_fields, $field;
    }
    $field_definitions{$field} = $json_meta_template->{'ep'}{$ep}{$field}{'definition'};
  }

  $col = 0;
  foreach my $field (sort @req_ep_fields) {
    $ep_worksheet->write(0, $col, $field, $format);
    $ep_worksheet->write(1, $col, $field_definitions{$field});
    for(my $sample_counter=1; $sample_counter<=$sample_count; ++$sample_counter) {
      if($field eq 'sample_name') {
        $ep_worksheet->write(1+$sample_counter, $col, "Sample$sample_counter");
      }
    }
    ++$col;
  }

  foreach my $field (sort @opt_ep_fields) {
    $ep_worksheet->write(0, $col, $field);
    $ep_worksheet->write(1, $col, $field_definitions{$field});
    ++$col;
  }

  ##############################################

  $workbook->close();

  my $print_filename = $filename;
  $print_filename =~ s/^.*\/(.*)/$1/;
  
  print "
          <table>
            <tr>
              <td>Download file here: <a href='metazen.cgi?update=download&filename=$filename'>$print_filename</a></td>
            </tr>
            <tr><td>&nbsp;</td></tr>
            <tr>
              <td>NOTE: Once you have downloaded and filled out your metadata spreadsheet you can head over to the <a href=\"http://metagenomics.anl.gov/metagenomics.cgi?page=Upload\">upload page</a> and upload it under \"Prepare Data -> 2. upload files\".  After it is validated, it should appear under \"Data Submission -> 1. select metadata file\".</td>
            </tr>
          </table>\n";
}

sub download {
  my $filename = $cgi->param('filename');
  if (open(FH, "./$filename")) {
    my $content = "";
    while (<FH>) {
      $content .= $_;
    }

    print "Content-Type:application/x-download\n";
    print "Content-Length: " . length($content) . "\n";
    my $print_filename = $filename;
    $print_filename =~ s/^.*\/(.*)/$1/;
    print "Content-Disposition:attachment;filename=".$print_filename."\n\n";
    print $content;

    exit;
  } else {
    warning_message('warning', "Could not open download file");
  }

  return 1;
}

sub print_field {
  my $field = my $field_level = my $field_type = my $required_field_flag = my $select_all_flag = my $field_sub_level = "";
  if(@_ == 6) {
    ($field, $field_level, $field_type, $required_field_flag, $select_all_flag, $field_sub_level) = @_;
  } elsif(@_ == 5) {
    ($field, $field_level, $field_type, $required_field_flag, $select_all_flag) = @_;
  } else {
    return;
  }

  ########################################################
  #
  # Examples of input parameters:
  # $field:                               "project_name"
  # $field_level:                         'project', 'sample', 'library'
  # $field_type:                          'float', 'text', etc.
  # $required_field_flag:                 0,1
  # $field_sub_level:                     'mimarks-survey', 'metagenome', 'metatranscriptome'
  #
  ########################################################

  my $value = "";
  if($previous_project ne "" && exists $json_project_data->{'metadata'}{$field} && $json_project_data->{'metadata'}{$field} ne " - ") {
    $value = encode_entities(decode("utf8", $json_project_data->{'metadata'}{$field}));
  }

  if($previous_project ne "" && $field_level eq 'project' && $field eq 'mgrast_id') {
    $value = $previous_project;
  }

  # Note that if the user is logged in, and they are the pi, their name and email will override that of the $previous_project
#  if($user && ($contact_status eq "both" || $contact_status eq "pi") &&
#     ($field eq 'PI_firstname' || $field eq 'PI_lastname' || $field eq 'PI_email')) {
#    my $tmp = $field;
#    $tmp =~ s/PI_(.*)/$1/;
#    $value = $user->{$tmp};
#  }

#  if($user && ($contact_status eq "both" || $contact_status eq "tech")) {
#    $value = $user->{$field};
#  }

  my $displayed_field = "";
  if($field_level eq 'project') {
    $displayed_field = (exists $project_display_fields->{$field}) ? $project_display_fields->{$field} : $field;
  } elsif($field_level eq 'sample') {
    $displayed_field = (exists $sample_display_fields->{$field}) ? $sample_display_fields->{$field} : $field;
  } elsif($field_level eq 'library') {
    $displayed_field = (exists $library_display_fields->{$field}) ? $library_display_fields->{$field} : $field;
  }

  my $field_name = "$field_level\_$field";
  if($field_sub_level ne "") {
    $field_name = "$field_sub_level\_$field";
  }

  my $req_opt_html = "";
  if($required_field_flag == 1) {
    my $color = "blue";
    if($field_level eq 'project') {
      $color = "red";
    }
    $req_opt_html = "&nbsp;<font style='color:$color;font-size:20px;vertical-align:bottom;'>*</font>&nbsp;&nbsp;";
  } else {
    my $checked = "";
    if($select_all_flag == 0) { $checked = "checked"; }
    $req_opt_html = "<input type=\"checkbox\" name=\"$field_name\_checkbox\" selectall=\"$select_all_flag\" $checked />&nbsp;&nbsp;";
  }

  my $project_required_field_attr = "";
  if($field_level eq 'project' && $required_field_flag == 1) {
    $project_required_field_attr = "project_required='1'";
  }

  # Checking for a few special fields first.
  if($field eq 'mgrast_id' || $field eq 'metagenome_id') {
    if($field_level eq 'project') {
      return "
                      <tr>
                        <td style='vertical-align:middle;width:195px;'>$req_opt_html$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td style='vertical-align:middle;'><input style='width:195px;' type='text' name='$field_name' value = ''></td>
                      </tr>\n";
    } else {
      my $count_field_name = "";
      if($field_level eq 'sample') {
        $count_field_name = 'sample_count';
      } elsif($field_level eq 'library') {
        $count_field_name = "$field_sub_level\_count";
      }

      if($cgi->param($count_field_name) && $cgi->param($count_field_name) == 1) {
        return "
                      <tr>
                        <td style='vertical-align:middle;width:195px;'>$req_opt_html$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td style='vertical-align:middle;'><input style='width:195px;' type='text' name='$field_name' value = ''></td>
                      </tr>\n";
      } else {
      return "
                      <tr>
                        <td style='vertical-align:middle;width:195px;'>$req_opt_html$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td style='vertical-align:middle;height:39px'>Must enter after download.</td>
                      </tr>\n";
      }
    } 
  } elsif($field eq 'project_funding') {
    my @funds = ('', 'Alfred P. Sloan Foundation', 'Bill & Melinda Gates Foundation', 'DHS - Department of Homeland Security', 'DOD - U.S. Department of Defense', 'DOE - U.S. Department of Energy', 'European Science Foundation', 'Gordon and Betty Moore Foundation', 'NHGRI - National Human Genome Research Institute', 'NIH - National Institutes of Health', 'NSF - National Science Foundation', 'U.S. Department of Agriculture', 'Other - enter text');
    return "
                      <tr>
                        <td style='vertical-align:middle;width:195px;padding:0px 0px 0px 1px;'>$req_opt_html$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td style='padding:0px 0px 0px 1px;'>".$cgi->popup_menu( -name => "$field_name", -values => \@funds, -default => $value, -style=> "width:205px;", -onChange => "showHideOtherProjectFunding('project_project_funding', 'project_other_funding_div');" )."</td>
                        <td>
                          <div id='project_other_funding_div' style='display:none'>
                            <table border=0>
                              <tr>
                                <td style='padding:0px 8px 0px 8px;'>Enter \"other\" funding source: </td>
                                <td><input style='width:195px;' type='text' name='project_other_funding'></td>
                              </tr>
                            </table>
                          </div>
                        </td>
                      </tr>\n";
  } elsif($field eq 'project_description') {
    if($value eq "") {
      $value = "This project explores ... with xxx samples from nn different locations...";
    }
    return "
                      <tr>
                        <td style='vertical-align:top;width:195px;padding:10px 0px 0px 0px;'>$req_opt_html$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td style='vertical-align:middle;padding:3px 0px 0px 0px;' colspan=3><textarea style='width:600px;' rows=\"10\" name='$field_name'>$value</textarea></td>
                      </tr>\n";
  } elsif($field eq 'misc_param') {
    return "
                      <tr>
                        <td style='vertical-align:middle;width:195px;'><input type=\"checkbox\" name=\"$field_name\_checkbox\" selectall=\"$select_all_flag\" />&nbsp;&nbsp;$displayed_field 1<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td style='vertical-align:middle;'><input style='width:195px;' type='text' name='$field_name\' value = '$value' displayField='$displayed_field'></td>
                      </tr>\n";
  }

  # Then, print the remaining fields based on their type and $field
  if($field_type eq 'float') {
    my $var_text = "returnNumericNegDec(event);\"> (decimal value)";
    if($field_level eq 'sample' && ($field eq 'altitude' || $field eq 'depth' || $field eq 'elevation')) {
      $var_text = "returnNumericNegDec(event);\"> meters";
    } elsif(($field_level eq 'sample' && $field eq 'ph') ||
            ($field_level eq 'library' && ($field eq 'lib_size_mean' || $field eq 'polymerase_units'))) {
      $var_text = "returnNumericDec(event);\"> (decimal value)";
    } elsif(($field_level eq 'sample' && $field eq 'temperature') ||
            ($field_level eq 'library' && ($field =~ /_temp$/ || $field =~ /_temp_/))) {
      $var_text = "returnNumericNegDec(event);\"> celsius (decimal)";
    } elsif($field_level eq 'library' && $field eq 'BSA_final_conc') {
      $var_text = "returnNumericDec(event);\"> (mg/ml)";
    } elsif($field_level eq 'library' && ($field eq 'KCl_final_conc' || $field eq 'MgCl2_final_conc' || $field eq 'pcr_volume')) {
      $var_text = "returnNumericDec(event);\"> (microliters)";
    } elsif($field_level eq 'library' && $field eq 'Tris_HCl_final_conc') {
      $var_text = "returnNumericDec(event);\"> (millimolar)";
    } elsif($field_level eq 'library' && ($field eq 'cycle_annealing_duration' || $field eq 'cycle_denaturation_duration' || $field eq 'cycle_extension_duration' || $field eq 'denaturation_duration_initial' || $field eq 'extension_duration_final' || $field eq 'tail_duration' || $field eq 'samp_isol_dur')) {
      $var_text = "returnNumericDec(event);\"> time (seconds)";
    } elsif($field_level eq 'library' && ($field =~ /d[ACGT]TP_final_conc/ || $field eq 'forward_primer_final_conc' || $field eq 'reverse_primer_final_conc')) {
      $var_text = "returnNumericDec(event);\"> (micromolar)";
    } elsif($field_level eq 'library' && $field eq 'gelatin_final_conc') {
      $var_text = "returnNumericDec(event);\"> (percentage)";
    }
    return "
                      <tr>
                        <td style='vertical-align:middle;width:195px'>$req_opt_html$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td style='vertical-align:middle;'><div id=\"$field_name\_div\" class=\"control-group\" style=\"margin-bottom:0px\"><input style='width:100px;' type='text' name='$field_name' value = '' displayField='$displayed_field' validate='float' onkeydown=\"return $var_text</div></td> 
                      </tr>\n";
  } elsif($field_type eq 'text') {
    my $input_field = "<td style='vertical-align:middle;'><div id=\"$field_name\_div\" class=\"control-group\" style=\"margin-bottom:0px\"><input style='width:195px;' type='text' name='$field_name' $project_required_field_attr value = '$value' displayField='$displayed_field'></div></td>";
    if($field_level eq 'sample' && $field eq 'estimated_size') {
      $input_field = "<td style='vertical-align:middle;'><input style='width:100px;' type='text' name='$field_name' value = '' onkeydown=\"return returnNumeric(event);\"> bp</td>";
    } elsif(($field_level eq 'sample' && ($field eq 'extrachrom_elements' || $field eq 'num_replicons')) ||
            ($field_level eq 'library' && $field eq 'lib_reads_seqd')) {
      $input_field = "<td style='vertical-align:middle;'><input style='width:100px;' type='text' name='$field_name' value = '' onkeydown=\"return returnNumeric(event);\"> (integer value)</td>";
    } elsif($field_level eq 'library' && $field eq 'NAP_volume') {
      $input_field = "<td style='vertical-align:middle;'><input style='width:100px;' type='text' name='$field_name' value = '' onkeydown=\"return returnNumericDec(event);\"> (microliters)</td>";
    } elsif($field_level eq 'sample' && $field eq 'biotic_relationship') {
      my @values = ('', 'free living', 'commensal', 'parasite', 'symbiont');
      $input_field = "<td>".$cgi->popup_menu( -name => "$field_name", -values => \@values, -style=> "width:205px;", -default => '' )."</td>";
    } elsif($field_level eq 'sample' && $field eq 'rel_to_oxygen') {
      my @values = ('', 'aerobe', 'anaerobe', 'facultative', 'microaerophilic', 'microanaerobe', 'obligate aerobe', 'obligate anaerobe');
      $input_field = "<td>".$cgi->popup_menu( -name => "$field_name", -values => \@values, -style=> "width:205px;", -default => '' )."</td>";
    } elsif($field_level eq 'sample' && $field eq 'trophic_level') {
      my @values = ('', 'autotroph', 'carboxydotroph', 'chemoautotroph', 'chemoheterotroph', 'chemolithoautotroph', 'chemolithotroph', 'chemoorganoheterotroph', 'chemoorganotroph', 'chemosynthetic', 'chemotroph', 'copiotroph', 'diazotroph', 'facultative', 'autotroph', 'heterotroph', 'lithoautotroph', 'lithoheterotroph', 'lithotroph', 'methanotroph', 'methylotroph', 'mixotroph', 'obligate', 'chemoautolithotroph', 'oligotroph', 'organoheterotroph', 'organotroph', 'photoautotroph', 'photoheterotroph', 'photolithoautotroph', 'photolithotroph', 'photosynthetic', 'phototroph');
      $input_field = "<td>".$cgi->popup_menu( -name => "$field_name", -values => \@values, -style=> "width:205px;", -default => '' )."</td>";
    } elsif($field_level eq 'library' && $field eq 'cycle_annealing_method') {
      my @values = ('', 'gradient', 'static', 'touchdown', 'other');
      $input_field = "<td>".$cgi->popup_menu( -name => "$field_name", -values => \@values, -style=> "width:205px;", -default => '' )."</td>";
    }
    return "
                      <tr>
                        <td style='vertical-align:middle;width:195px;'>$req_opt_html$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        $input_field
                      </tr>\n";
  } elsif($field_type eq 'int') {
    return "
                      <tr>
                        <td style='vertical-align:middle;width:195px;'>$req_opt_html$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td style='vertical-align:middle;'><input style='width:100px;' type='text' name='$field_name' value = '' onkeydown=\"return returnNumeric(event);\"> (integer value)</td>
                      </tr>\n";
  } elsif($field_type eq 'select') {
    my $input_field = "<td style='vertical-align:middle;'><input style='width:195px;' type='text' name='$field_name' value = '$value'></td>";
    if($field_level eq 'sample' && $field eq 'continent') {
      my @values = ('', 'Africa', 'Antarctica', 'Asia', 'Australia', 'Europe', 'North America', 'South America');
      $input_field = "<td>".$cgi->popup_menu( -name => "$field_name", -values => \@values, -style=> "width:205px;", -default => '' )."</td>";
    } elsif($field_level eq 'library' && $field eq 'seq_meth') {
      my @values = ('', '454', 'ABI-SOLiD', 'Illumina', 'Ion Torrent', 'Sanger', 'Other');
      $input_field = "<td>".$cgi->popup_menu( -name => "$field_name", -values => \@values, -style=> "width:205px;", -default => '', -onChange => "updateSeqMakeModel('$field_sub_level');" )."</td>";
    } elsif($field_level eq 'library' && $field eq 'domain') {
      my @values = ('', 'Archaea', 'Bacteria', 'Eukarya');
      $input_field = "<td>".$cgi->popup_menu( -name => "$field_name", -values => \@values, -style=> "width:205px;", -default => '' )."</td>";
    } elsif($field_level eq 'library' && $field eq 'seq_direction') {
      my @values = ('', 'forward', 'reverse', 'both');
      $input_field = "<td>".$cgi->popup_menu( -name => "$field_name", -values => \@values, -style=> "width:205px;", -default => '' )."</td>";
    }
    return "
                      <tr>
                        <td style='vertical-align:middle;width:195px;'>$req_opt_html$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        $input_field
                      </tr>\n";
  } elsif($field_type eq 'email' || $field_type eq 'url') {
    return "
                      <tr>
                        <td style='vertical-align:middle;width:195px;'>$req_opt_html$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td style='vertical-align:middle;'><div id=\"$field_name\_div\" class=\"control-group\" style=\"margin-bottom:0px\"><input style='width:195px;' type='text' name='$field_name' $project_required_field_attr value = '$value' displayField='$displayed_field' validate='$field_type'></div></td>
                      </tr>\n";
  } elsif($field_type eq 'date') {
    my @time_data = localtime(time);
    my $day = $time_data[3];
    my $month = $time_data[4] + 1;
    if($day < 10) { $day = '0'.$day; }
    if($month < 10) { $month = '0'.$month; }
    my $year = $time_data[5] + 1900;
    return "
                      <tr>
                        <td style='vertical-align:middle;width:195px'>$req_opt_html$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td>
                          <div class=\"input-append date\" id=\"sample_collection_date_div\" data-date=\"$year-$month-$day\" data-date-format=\"yyyy-mm-dd\">
                            <input class=\"span2\" name=\"$field_name\" displayField='$displayed_field' validate='$field_type' type=\"text\" style=\"width:100px;\" />
                            <span class=\"add-on\"><i class=\"icon-th\"></i></span>
                          </div>
                        </td>
                      </tr>\n";
  } elsif($field_type eq 'time') {
    return "
                      <tr>
                        <td style='vertical-align:middle;width:195px'>$req_opt_html$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td>
                          <div class=\"input-append bootstrap-timepicker-component\">
                            <input class=\"timepicker-1 input-small\" name=\"$field_name\" type=\"text\" style=\"width: 100px;\" />
                            <span class=\"add-on\"><i class=\"icon-time\"></i></span>
                          </div>
                        </td>
                      </tr>\n";
  } elsif($field_type eq 'timezone') {
    my $timezone_codes = &get_timezones();
    my %printed_timezone_codes = ();
    my $timezone_values;
    push @$timezone_values, '';
    foreach my $key (sort {$a<=>$b} keys(%$timezone_codes)) {
      if($key ne '') {
        push @$timezone_values, "UTC$key";
      }
      $printed_timezone_codes{"UTC$key"} = $timezone_codes->{$key};
    }
    return "
                      <tr>
                        <td style='vertical-align:middle;width:195px'>$req_opt_html$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td>".$cgi->popup_menu( -name => "sample_$field", -values => $timezone_values, -labels => \%printed_timezone_codes, -style=> "width:205px;", -default => '' )."</td>
                      </tr>\n";
  } elsif($field_type eq 'ontology' && $field =~ /country/) {
    my $country_codes_list = country_codes();
    return "
                      <tr>
                        <td style='vertical-align:middle;width:195px;'>$req_opt_html$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td><div id=\"$field_name\_div\" class=\"control-group\" style=\"margin-bottom:0px\">".$cgi->popup_menu( -name => "$field_name", -values => $country_codes_list, -style=> "width:205px;", -default => $value )."</div></td>
                      </tr>\n";
  } else {
    return "
                      <tr>
                        <td style='vertical-align:middle;width:195px;'>$req_opt_html$displayed_field<span id='$field_name'><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td>
                        <td style='vertical-align:middle;'><input style='width:195px;' type='text' name='$field_name' value = '$value'></td>
                      </tr>\n";
  }
}

sub base_template {
    my $ajax_url = "http://dunkirk.mcs.anl.gov/~jbischof/mgrast/ajax.cg";
    return qq~<!DOCTYPE html>
<html>

  <head>

    <title>MetaZen</title>

    <script type="text/javascript" src="./Html/jquery.1.7.2.min.js"></script>
    <script type="text/javascript" src="./Html/bootstrap.min.js"></script>
    <script type="text/javascript" src="./Html/MetaZen.js"></script>
    <script type="text/javascript" src="./Html/bootstrap-datepicker.js"></script>
    <script type="text/javascript" src="./Html/bootstrap-timepicker.js"></script>

    <link rel="stylesheet" type="text/css" href="./Html/bootstrap.min.MetaZen.css">
    <link rel="stylesheet" type="text/css" href="./Html/Upload.css">
    <link rel="stylesheet" type="text/css" href="./Html/datepicker.css">
    <link rel="stylesheet" type="text/css" href="./Html/timepicker.css">
    <link rel="stylesheet" type="text/css" href="./Html/mgrast.css">

  </head>


  <body onload="showHideOtherProjectFunding('project_project_funding', 'project_other_funding_div');">
  <div id="header"><a href="http://metagenomics.anl.gov/metagenomics.cgi?page=Home" style="border: none;">
    <img style="float: left; 
                height: 80px; 
                margin-left: 40px;
                margin-top: 10px;" 
         src="./Html/MGRAST_logo.png" alt="MG-RAST Metagenomics Analysis Server" />
</a>
    <div id="nav_login_box">
      <div id="top_nav">    
        <div id="top_nav_links"><a class= "nav_top" href="http://metagenomics.anl.gov/metagenomics.cgi?page=Home"><img src='./Html/mg-home.png' style='width: 20px; height: 20px;' title='Home'></a></div>
        <div id="top_nav_links"><a class= "nav_top" href="http://metagenomics.anl.gov/metagenomics.cgi?page=MetagenomeSelect"><img src='./Html/mgrast_globe.png' style='width: 20px; height: 20px;' title='Browse'></a></div>
        <div id="top_nav_links"><a class= "nav_top" href="http://metagenomics.anl.gov/metagenomics.cgi?page=Analysis"><img src='./Html/analysis.gif' style='width: 20px; height: 20px;' title='Analyze'></a></div>
        <div id="top_nav_links"><a class= "nav_top" href="http://metagenomics.anl.gov/metagenomics.cgi?page=MetagenomeSearch"><img src='./Html/lupe.png' style='width: 20px; height: 20px;' title='Search'></a></div>
        <br>
        <div id="top_nav_links"><a class= "nav_top" href="http://metagenomics.anl.gov/metagenomics.cgi?page=DownloadMetagenome"><img src='./Html/mg-download.png' style='width: 20px; height: 20px;' title=Download></a></div>
            <div id="top_nav_links"><a class= "nav_top" href="http://metagenomics.anl.gov/metagenomics.cgi?page=Upload"><img src='./Html/mg-upload.png' style='width: 20px; height: 20px;' title='Upload'></a></div>
        <div id="top_nav_links"><a class= "nav_top" href="http://blog.metagenomics.anl.gov/howto/" target=_blank><img src='./Html/mg-help.png' style='width: 20px; height: 20px;' title='Support'></a></div>
        <div id="top_nav_links"><a class= "nav_top" href="http://metagenomics.anl.gov/metagenomics.cgi?page=Contact"><img src='./Html/mg-contact.png' style='width: 20px; height: 20px;' title='Contact'></a></div>
      </div>
    </div>
  </div>
  <div id="content_frame">
    <div id="page_title">
    MetaZen
    </div>
    <div id="content">~;
}

sub close_template {
    return qq~
    </div>

  </body>
</html>~;
}

sub warning_message {
    my ($message) = @_;

    print $cgi->header();
    print base_template();
    print qq~<div class="alert alert-error">
<button class="close" data-dismiss="alert" type="button">x</button>
<strong>Warning</strong><br>~;
    print $message;
    print qq~<br><a href="oAuth.cgi">return to home</a></div>~;
    print close_template();    
}

sub success_message {
    my ($message) = @_;

    print $cgi->header();
    print base_template();
    print qq~<div class="alert alert-success">
<button class="close" data-dismiss="alert" type="button">x</button>
<strong>Info</strong><br>~;
    print $message;
    print qq~<br><a href="oAuth.cgi">return to home</a></div>~;
    print close_template();
}

sub sort_opt_library_fields {
  my ($array) = @_;

  @$array = sort {lc(substr($a,0,1)).substr($a,1) cmp lc(substr($b,0,1)).substr($b,1)} @$array;
  my $misc_param_index = -1;
  for(my $i=0; $i<@$array; $i++) {
    if(@$array[$i] eq 'misc_param') {
      $misc_param_index = $i;
    }
  }
  if($misc_param_index != -1) {
    splice(@$array, $misc_param_index, 1);
  }

  # Moving 'mgrast_id' which is actually the MG-RAST Library ID up in the list just
  #  before 'metagenome_id' which is actually the MG-RAST Metagenome ID
  my ($mgrast_id_index, $metagenome_id_index) = -1;
  for(my $i=0; $i<@$array; $i++) {
    if(@$array[$i] eq 'mgrast_id') {
      $mgrast_id_index = $i;
    } elsif(@$array[$i] eq 'metagenome_id') {
      $metagenome_id_index = $i;
    }
  }
  unless(($mgrast_id_index != -1 && $metagenome_id_index != -1) ||
         ($mgrast_id_index < $metagenome_id_index)) {
    return;
  }

  for(my $i=$mgrast_id_index; $i>$metagenome_id_index; --$i) {
    @$array[$i] = @$array[$i-1];
  }
  @$array[$metagenome_id_index] = 'mgrast_id';
}

sub get_project_display_fields {
  return { 
           'PI_email'                => 'PI e-mail',
           'PI_firstname'            => 'PI First Name',
           'PI_lastname'             => 'PI Last Name',
           'PI_organization'         => 'PI Organization',
           'PI_organization_address' => 'PI Org Address',
           'PI_organization_country' => 'PI Org Country',
           'PI_organization_url'     => 'PI Organization URL',
           'email'                   => 'Contact E-mail',
           'firstname'               => 'Contact First Name',
           'greengenes_id'           => '<a href="http://greengenes.lbl.gov" target="_blank">Greengenes</a> Project ID',
           'lastname'                => 'Contact Last Name',
           'mgrast_id'               => '<a href="http://metagenomics.anl.gov/" target="_blank">MG-RAST</a> Project ID',
           'misc_param'              => 'Miscellaneous Param',
           'ncbi_id'                 => '<a href="http://www.ncbi.nlm.nih.gov/" target="_blank">NCBI</a> Project ID',
           'organization'            => 'Organization',
           'organization_address'    => 'Organization Address',
           'organization_country'    => 'Organization Country',
           'organization_url'        => 'Organization URL',
           'project_description'     => 'Project Description',
           'project_funding'         => 'Project Funding',
           'project_name'            => 'Project Name',
           'qiime_id'                => '<a href="http://qiime.org/" target="_blank">QIIME</a> Project ID',
           'submitted_to_insdc'      => 'Submitted to <a href="http://www.insdc.org/" target="_blank">INSDC</a>',
           'vamps_id'                => '<a href="http://vamps.mbl.edu/" target="_blank">VAMPS</a> Project ID' };
}

sub get_sample_display_fields {
  return { 
           'altitude'            => 'Altitude',
           'biome'               => 'Biome',
           'biotic_relationship' => 'Biotic Relationship',
           'collection_date'     => 'Collection Date',
           'collection_time'     => 'Collection Time',
           'collection_timezone' => 'Collection Timezone',
           'continent'           => 'Continent',
           'country'             => 'Country/Water body',
           'depth'               => 'Depth',
           'elevation'           => 'Elevation',
           'encoded_traits'      => 'Encoded Traits',
           'env_package'         => 'Environmental Package',
           'estimated_size'      => 'Estimated Size',
           'experimental_factor' => 'Experimental Factor',
           'extrachrom_elements' => 'Extrachrom Elements',
           'feature'             => 'Feature',
           'health_disease_stat' => 'Health/Disease Status',
           'host_spec_range'     => 'Host Specificity/Range',
           'isol_growth_condt'   => 'Isolation & Growth Cond',
           'latitude'            => 'Latitude',
           'location'            => 'Location',
           'longitude'           => 'Longitude',
           'material'            => 'Material',
           'mgrast_id'           => '<a href="http://metagenomics.anl.gov/" target="_blank">MG-RAST</a> Sample ID',
           'misc_param'          => 'Miscellaneous Param',
           'num_replicons'       => 'Number of Replicons',
           'pathogenicity'       => 'Pathogenicity',
           'ph'                  => 'pH',
           'propagation'         => 'Propagation',
           'ref_biomaterial'     => 'Ref Biomaterial',
           'rel_to_oxygen'       => 'Rel to Oxygen',
           'samp_collect_device' => 'Sample Collect Device',
           'samp_mat_process'    => 'Sample Mat Process',
           'samp_size'           => 'Sample Size',
           'sample_id'           => 'Sample ID',
           'sample_name'         => 'Sample Name',
           'sample_strategy'     => 'Sample Strategy',
           'source_mat_id'       => 'Source Material ID',
           'specific_host'       => 'Specific Host',
           'subspecf_gen_lin'    => 'Sub Genetic Lineage',
           'temperature'         => 'Temperature',
           'trophic_level'       => 'Trophic Level' };
}

sub get_library_display_fields {
  return { 
           '454_gasket_type'               => '454 Gasket Type',
           '454_regions'                   => '454 Regions',
           'BSA_final_conc'                => 'BSA Final Conc',
           'KCl_final_conc'                => 'KCl Final Conc',
           'MgCl2_final_conc'              => 'MgCl2 Final Conc',
           'NAP_volume'                    => 'NAP Folume',
           'Tris_HCl_final_conc'           => 'Tris HCl Final Conc',
           'adapters'                      => 'Adapters',
           'amp_polymerase'                => 'Amp Polymerase',
           'assembly'                      => 'Assembly',
           'assembly_name'                 => 'Assembly Name',
           'cdna_ampf_meth'                => 'cDNA Amp Meth',
           'cdna_purif_meth'               => 'cDNA Purification Meth',
           'cloning_kit'                   => 'Cloning Kit',
           'cycle_annealing_duration'      => 'Cycle Annealing Time',
           'cycle_annealing_method'        => 'Cycle Annealing Method',
           'cycle_annealing_temp'          => 'Cycle Annealing Temp',
           'cycle_count'                   => 'Cycle Count',
           'cycle_denaturation_duration'   => 'Cycle Denaturation Time',
           'cycle_denaturation_temp'       => 'Cycle Denaturation Temp',
           'cycle_extension_duration'      => 'Cycle Extension Time',
           'cycle_extension_temp'          => 'Cycle Extension Temp',
           'dATP_final_conc'               => 'dATP Final Conc',
           'dCTP_final_conc'               => 'dCTP Final Conc',
           'dGTP_final_conc'               => 'dGTP Final Conc',
           'dTTP_final_conc'               => 'dTTP Final Conc',
           'denaturation_duration_initial' => 'Denaturation Time (Init)',
           'denaturation_temp_initial'     => 'Denaturation Temp (Init)',
           'domain'                        => 'Domain',
           'extension_duration_final'      => 'Extension Time (Final)',
           'extension_temp_final'          => 'Extension Temp (Final)',
           'file_checksum'                 => 'File Checksum',
           'file_name'                     => 'File Name',
           'forward_barcodes'              => 'Fwd Barcodes',
           'forward_primer_final_conc'     => 'Fwd Primer Final Conc',
           'forward_primers'               => 'Fwd Primers',
           'gelatin_final_conc'            => 'Gelatin Final Conc',
           'gold_id'                       => '<a href="http://www.genomesonline.org" target="_blank">GOLD</a> ID',
           'host_cells'                    => 'Host Cells',
           'investigation_type'            => 'Investigation Type',
           'lib_const_meth'                => 'Lib Construct Method',
           'lib_reads_seqd'                => 'Lib Clones Sequenced',
           'lib_screen'                    => 'Lib Screening Method',
           'lib_size'                      => 'Lib Size',
           'lib_size_mean'                 => 'Lib Size Mean',
           'lib_type'                      => 'Lib Type',
           'lib_vector'                    => 'Lib Vector',
           'library_institute'             => 'Lib Institute',
           'library_notes'                 => 'Lib Notes',
           'local_NAP_ids'                 => 'Local NAP IDs',
           'metagenome_id'                 => '<a href="http://metagenomics.anl.gov/" target="_blank">MG-RAST</a> Metagenome ID',
           'metagenome_name'               => 'Metagenome Name',
           'mgrast_id'                     => '<a href="http://metagenomics.anl.gov/" target="_blank">MG-RAST</a> Library ID',
           'misc_param'                    => 'Miscellaneous Param',
           'mrna_percent'                  => 'mRNA Percent',
           'nucl_acid_amp'                 => 'Nucleic Acid Amp',
           'nucl_acid_ext'                 => 'Nucleic Acid Extension',
           'other_additives'               => 'Other Additives',
           'pcr_buffer_pH'                 => 'PCR Buffer pH',
           'pcr_clean_up_kits'             => 'PCR Clean Up Kits',
           'pcr_clean_up_methods'          => 'PCR Clean Up Methods',
           'pcr_notes'                     => 'PCR Notes',
           'pcr_replicates'                => 'PCR Replicates',
           'pcr_volume'                    => 'PCR Volume',
           'polymerase_units'              => 'Polymerase Units',
           'pubmed_id'                     => '<a href="http://www.pubmed.com/" target="_blank">PubMed</a> ID',
           'rev_trans_meth'                => 'Rev Transcript Meth',
           'reverse_barcodes'              => 'Rev Barcodes',
           'reverse_primer_final_conc'     => 'Rev Primer Final Conc',
           'reverse_primers'               => 'Rev Primers',
           'rrna_removal_meth'             => 'rRNA Removal Method',
           'run_machine_type'              => 'Run Machine Type',
           'samp_isol_dur'                 => 'Sample Isolation Time',
           'sample_name'                   => 'Sample Name',
           'seq_center'                    => 'Sequencing Center',
           'seq_chem'                      => 'Sequencing Chemistry',
           'seq_direction'                 => 'Sequencing Direction',
           'seq_make'                      => 'Sequencer Make',
           'seq_meth'                      => 'Sequencing Method',
           'seq_model'                     => 'Sequencer Model',
           'seq_quality_check'             => 'Sequence Qual Check',
           'seq_url'                       => 'Sequencing Center URL',
           'tail_duration'                 => 'Tailing Reaction Time',
           'tail_polymerase'               => 'Tailing Reaction Poly',
           'tail_temp'                     => 'Tailing Reaction Temp',
           'target_gene'                   => 'Target Gene',
           'target_subfragment'            => 'Target Subfragment',
           'thermocycler'                  => 'Thermocycler' };
}

# From GSC: Country or sea names should be chosen from the INSDC country
#  list (http://insdc.org/country.html). This list was from that URL.
sub country_codes {
  my @countries =
  ('',
   'Afghanistan',
   'Albania',
   'Algeria',
   'American Samoa',
   'Andorra',
   'Angola',
   'Anguilla',
   'Antarctica',
   'Antigua and Barbuda',
   'Arctic Ocean',
   'Argentina',
   'Armenia',
   'Aruba',
   'Ashmore and Cartier Islands',
   'Atlantic Ocean',
   'Australia',
   'Austria',
   'Azerbaijan',
   'Bahamas',
   'Bahrain',
   'Baltic Sea',
   'Baker Island',
   'Bangladesh',
   'Barbados',
   'Bassas da India',
   'Belarus',
   'Belgium',
   'Belize',
   'Benin',
   'Bermuda',
   'Bhutan',
   'Bolivia',
   'Borneo',
   'Bosnia and Herzegovina',
   'Botswana',
   'Bouvet Island',
   'Brazil',
   'British Virgin Islands',
   'Brunei',
   'Bulgaria',
   'Burkina Faso',
   'Burundi',
   'Cambodia',
   'Cameroon',
   'Canada',
   'Cape Verde',
   'Cayman Islands',
   'Central African Republic',
   'Chad',
   'Chile',
   'China',
   'Christmas Island',
   'Clipperton Island',
   'Cocos Islands',
   'Colombia',
   'Comoros',
   'Cook Islands',
   'Coral Sea Islands',
   'Costa Rica',
   'Cote d\'Ivoire',
   'Croatia',
   'Cuba',
   'Curacao',
   'Cyprus',
   'Czech Republic',
   'Democratic Republic of the Congo',
   'Denmark',
   'Djibouti',
   'Dominica',
   'Dominican Republic',
   'East Timor',
   'Ecuador',
   'Egypt',
   'El Salvador',
   'Equatorial Guinea',
   'Eritrea',
   'Estonia',
   'Ethiopia',
   'Europa Island',
   'Falkland Islands (Islas Malvinas)',
   'Faroe Islands',
   'Fiji',
   'Finland',
   'France',
   'French Guiana',
   'French Polynesia',
   'French Southern and Antarctic Lands',
   'Gabon',
   'Gambia',
   'Gaza Strip',
   'Georgia',
   'Germany',
   'Ghana',
   'Gibraltar',
   'Glorioso Islands',
   'Greece',
   'Greenland',
   'Grenada',
   'Guadeloupe',
   'Guam',
   'Guatemala',
   'Guernsey',
   'Guinea',
   'Guinea-Bissau',
   'Guyana',
   'Haiti',
   'Heard Island and McDonald Islands',
   'Honduras',
   'Hong Kong',
   'Howland Island',
   'Hungary',
   'Iceland',
   'India',
   'Indian Ocean',
   'Indonesia',
   'Iran',
   'Iraq',
   'Ireland',
   'Isle of Man',
   'Israel',
   'Italy',
   'Jamaica',
   'Jan Mayen',
   'Japan',
   'Jarvis Island',
   'Jersey',
   'Johnston Atoll',
   'Jordan',
   'Juan de Nova Island',
   'Kazakhstan',
   'Kenya',
   'Kerguelen Archipelago',
   'Kingman Reef',
   'Kiribati',
   'Kosovo',
   'Kuwait',
   'Kyrgyzstan',
   'Laos',
   'Latvia',
   'Lebanon',
   'Lesotho',
   'Liberia',
   'Libya',
   'Liechtenstein',
   'Lithuania',
   'Luxembourg',
   'Macau',
   'Macedonia',
   'Madagascar',
   'Malawi',
   'Malaysia',
   'Maldives',
   'Mali',
   'Malta',
   'Marshall Islands',
   'Martinique',
   'Mauritania',
   'Mauritius',
   'Mayotte',
   'Mediterranean Sea',
   'Mexico',
   'Micronesia',
   'Midway Islands',
   'Moldova',
   'Monaco',
   'Mongolia',
   'Montenegro',
   'Montserrat',
   'Morocco',
   'Mozambique',
   'Myanmar',
   'Namibia',
   'Nauru',
   'Navassa Island',
   'Nepal',
   'Netherlands',
   'New Caledonia',
   'New Zealand',
   'Nicaragua',
   'Niger',
   'Nigeria',
   'Niue',
   'Norfolk Island',
   'North Korea',
   'North Sea',
   'Northern Mariana Islands',
   'Norway',
   'Oman',
   'Pacific Ocean',
   'Pakistan',
   'Palau',
   'Palmyra Atoll',
   'Panama',
   'Papua New Guinea',
   'Paracel Islands',
   'Paraguay',
   'Peru',
   'Philippines',
   'Pitcairn Islands',
   'Poland',
   'Portugal',
   'Puerto Rico',
   'Qatar',
   'Republic of the Congo',
   'Reunion',
   'Romania',
   'Ross Sea',
   'Russia',
   'Rwanda',
   'Saint Helena',
   'Saint Kitts and Nevis',
   'Saint Lucia',
   'Saint Pierre and Miquelon',
   'Saint Vincent and the Grenadines',
   'Samoa',
   'San Marino',
   'Sao Tome and Principe',
   'Saudi Arabia',
   'Senegal',
   'Serbia',
   'Seychelles',
   'Sierra Leone',
   'Singapore',
   'Sint Maarten',
   'Slovakia',
   'Slovenia',
   'Solomon Islands',
   'Somalia',
   'South Africa',
   'South Georgia and the South Sandwich Islands',
   'South Korea',
   'Southern Ocean',
   'Spain',
   'Spratly Islands',
   'Sri Lanka',
   'Sudan',
   'Suriname',
   'Svalbard',
   'Swaziland',
   'Sweden',
   'Switzerland',
   'Syria',
   'Taiwan',
   'Tajikistan',
   'Tanzania',
   'Tasman Sea',
   'Thailand',
   'Togo',
   'Tokelau',
   'Tonga',
   'Trinidad and Tobago',
   'Tromelin Island',
   'Tunisia',
   'Turkey',
   'Turkmenistan',
   'Turks and Caicos Islands',
   'Tuvalu',
   'USA',
   'Uganda',
   'Ukraine',
   'United Arab Emirates',
   'United Kingdom',
   'Uruguay',
   'Uzbekistan',
   'Vanuatu',
   'Venezuela',
   'Viet Nam',
   'Virgin Islands',
   'Wake Island',
   'Wallis and Futuna',
   'West Bank',
   'Western Sahara',
   'Yemen',
   'Zambia',
   'Zimbabwe');
  return \@countries;
}

sub get_timezones {
  return { ''          => '',
           '-12'    => '(UTC-12:00) U.S. Baker Island, Howland Island',
           '-11'    => '(UTC-11:00) Hawaii, American Samoa',
           '-10'    => '(UTC-10:00) Cook Islands',
           '-9:30'  => '(UTC-9:30) Marguesas Islands',
           '-9'     => '(UTC-9:00) Gambier Islands',
           '-8'     => '(UTC-8:00) U.S. & Canada Pacific Time Zone',
           '-7'     => '(UTC-7:00) U.S. & Canada Mountain Time Zone',
           '-6'     => '(UTC-6:00) U.S. & Canada Central Time Zone',
           '-5'     => '(UTC-5:00) U.S. Eastern Time Zone',
           '-4:30'  => '(UTC-4:30) Venezuela',
           '-4'     => '(UTC-4:00) Canada Atlantic Time Zone',
           '-3:30'  => '(UTC-3:30) Newfoundland',
           '-3'     => '(UTC-3:00) French Guiana, Falkland Islands',
           '-2'     => '(UTC-2:00) South Georgia and the South Sandwich Islands',
           '-1'     => '(UTC-1:00) Cape Verde',
           '0'     => '(UTC+0:00) Ireland, London',
           '1'     => '(UTC+1:00) Amsterdam, Berlin',
           '2'     => '(UTC+2:00) Athens, Cairo, Johannesburg',
           '3'     => '(UTC+3:00) Baghdad, Riyadh',
           '3:30'  => '(UTC+3:30) Tehran',
           '4'     => '(UTC+4:00) Dubai, Moscow',
           '4:30'  => '(UTC+4:30) Kabul',
           '5'     => '(UTC+5:00) Pakistan',
           '5:30'  => '(UTC+5:30) Delhi, Mumbai',
           '5:45'  => '(UTC+5:45) Nepal',
           '6'     => '(UTC+6:00) Bangladesh',
           '6:30'  => '(UTC+6:30) Cocos Islands',
           '7'     => '(UTC+7:00) Bangkok, Hanoi',
           '8'     => '(UTC+8:00) Beijing, Singapore',
           '8:45'  => '(UTC+8:45) Eucla',
           '9'     => '(UTC+9:00) Seoul, Tokyo',
           '9:30'  => '(UTC+9:30) Adelaide',
           '10'    => '(UTC+10:00) Sydney, Melbourne',
           '10:30' => '(UTC+10:30) New South Wales',
           '11'    => '(UTC+11:00) Solomon Islands',
           '11:30' => '(UTC+11:30) Norfolk Island',
           '12'    => '(UTC+12:00) U.S. Wake Island',
           '12:45' => '(UTC+12:45) Chatham Islands',
           '13'    => '(UTC+13:00) Samoa',
           '14'    => '(UTC+14:00) Line Islands' };
}
