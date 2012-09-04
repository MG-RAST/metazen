function toggle (id) {
  var item = document.getElementById(id);
  if (item.style.display == "none") {
    item.style.display = "";
  } else {
    item.style.display = "none";
  }
}

function selectAllOptionalFields (prefix) {
  var inputs, index;
  inputs = document.getElementsByTagName('input');
  for(index=0; index<inputs.length; ++index) {
    if(inputs[index].name.indexOf("checkbox") > -1 &&
       inputs[index].name.indexOf(prefix) == 0 &&
       inputs[index].getAttribute("selectall") == 1) {
      inputs[index].checked = true;
    }
  }
}

function deselectAllOptionalFields (prefix) {
  var inputs, index;
  inputs = document.getElementsByTagName('input');
  for(index=0; index<inputs.length; ++index) {
    if(inputs[index].name.indexOf("checkbox") > -1 &&
       inputs[index].name.indexOf(prefix) == 0 &&
       inputs[index].getAttribute("selectall") == 1) {
      inputs[index].checked = false;
    }
  }
}

// Function to toggle appearance of a text field for entering project funding source.
function showHideOtherProjectFunding (dropdownID, divID) {
  var divItem = document.getElementById(divID);
  if(document.forms['metadata_form'].elements[dropdownID].value == "Other - enter text") {
    divItem.style.display = "";
  } else {
    divItem.style.display = "none";
  }
}

// Function to get the selected concept names from the bioontology widgets and put them in text fields.
function setEnvField (ontologyTreeID) {
  var conceptName = null;
  app = document[ontologyTreeID];
  if (app && app.getOntologyID) {
    conceptName = app.getSelectedConceptName();
  }
  if(ontologyTreeID == "OntologyTreeBiome") {
    document.forms['metadata_form'].elements['sample_biome'].value = conceptName;
  } else if(ontologyTreeID == "OntologyTreeEnvFeature") {
    document.forms['metadata_form'].elements['sample_feature'].value = conceptName;
  } else if(ontologyTreeID == "OntologyTreeEnvMaterial") {
    document.forms['metadata_form'].elements['sample_material'].value = conceptName;
  }
}

function returnNumeric (ev) {
  return ( ev.ctrlKey || ev.altKey || (47<ev.keyCode && ev.keyCode<58 && ev.shiftKey==false) || (95<ev.keyCode && ev.keyCode<106) || (ev.keyCode==8) || (ev.keyCode==9) || (ev.keyCode>34 && ev.keyCode<41) || (ev.keyCode==46) );
}

function returnNumericDec (ev) {
  return ( ev.ctrlKey || ev.altKey || (47<ev.keyCode && ev.keyCode<58 && ev.shiftKey==false) || (95<ev.keyCode && ev.keyCode<106) || (ev.keyCode==8) || (ev.keyCode==9) || (ev.keyCode>34 && ev.keyCode<41) || (ev.keyCode==46) || (ev.keyCode==110) || (ev.keyCode==190) );
}

function returnNumericNegDec (ev) {
  return ( ev.ctrlKey || ev.altKey || (47<ev.keyCode && ev.keyCode<58 && ev.shiftKey==false) || (95<ev.keyCode && ev.keyCode<106) || (ev.keyCode==8) || (ev.keyCode==9) || (ev.keyCode>34 && ev.keyCode<41) || (ev.keyCode==46) || (ev.keyCode==109) || (ev.keyCode==110) || (ev.keyCode==190) );
}

function execute_ajax(func, target, form) {
  if(func == 'print_bottom_of_form') {
    if(!(validateTopOfForm())) {
      return;
    }
  } else if(func == 'generate_excel_spreadsheet') {
    if(!(validateTopOfForm()) || !(validateBottomOfForm())) {
      return;
    }
  } else if(func == 'search_address') {
    var addr = document.forms['metadata_form'].elements['sample_location'].value;
    if(addr == null || addr.match(/^ *$/)) {
      return;
    }
  }

  var items = $('#'+form).serializeArray();
  items.push({name:"update", value:func});
  jQuery.post("", items, function (data) {
    var script = data.substring(data.indexOf('<script>') + 8, data.indexOf('</script>'));
    document.getElementById(target).innerHTML = data;
    if(data.indexOf('<script>') > 0) {
      eval(script);
    }
  });

  if(func == 'print_top_of_form') {
    if(document.forms['prefill_form'].elements['previous_project'].value == 'none') {
      document.getElementById('prefill_status').innerHTML = "<p style='color:red'>Form filled with your contact information.</p>";
    } else {
      document.getElementById('prefill_status').innerHTML = "<p style='color:red'>Form filled with project and sample set information from previous project.</p>";
    }
  }
}

function validateTopOfForm() {
  for (var i=0; i<document.forms['metadata_form'].elements.length; i++) {
    var element = document.forms['metadata_form'].elements[i];
    if(element.getAttribute("validate") == 'email') {
      if(element.value != "" && !validateEmail(element.value)) {
        alert('Please enter a valid email for ' + element.getAttribute("displayField"));
        document.getElementById(element.name + '_div').className = 'control-group error';
        return false;
      } else {
        document.getElementById(element.name + '_div').className = 'control-group';
      }
    } else if(element.getAttribute("validate") == 'url') {
      if(element.value != "" && !isUrl(element.value)) {
        alert('Please enter a valid URL for ' + element.getAttribute("displayField") +
              '.  The URL is currently set to: ' + element.value);
        document.getElementById(element.name + '_div').className = 'control-group error';
        return false;
      } else {
        document.getElementById(element.name + '_div').className = 'control-group';
      }
    }

    if(element.getAttribute("project_required") == 1) {
      if(element.name == "env_package") {
        alert('env package selected? ');
        return false;
      }
      if(element.value == "") {
        alert('Please enter the required project field: ' + element.getAttribute("displayField"));
        document.getElementById(element.name + '_div').className = 'control-group error';
        return false;
      } else {
        document.getElementById(element.name + '_div').className = 'control-group';
      }
    }

    // Custom attribute "project_required" wouldn't work for html select fields, so I'm hard coding these.
    if(element.name == "project_PI_organization_country") {
      if(element.value == "") {
        alert('Please enter the required project field: PI Org Country');
        document.getElementById(element.name + '_div').className = 'control-group error';
        return false;
      } else {
        document.getElementById(element.name + '_div').className = 'control-group';
      }
    }
    if(element.name == "env_package") {
      if(element.value == "") {
        alert('Please enter the required sample set field: environmental package');
        document.getElementById(element.name + '_div').className = 'control-group error';
        return false;
      } else {
        document.getElementById(element.name + '_div').className = 'control-group';
      }
    }
  }

  if(document.forms['metadata_form'].elements['sample_count'].value < 1) {
    alert('Please enter a value greater than 1 for the number of samples.');
    document.getElementById('sample_count_div').className = 'control-group error';
    return false;
  } else {
    document.getElementById('sample_count_div').className = 'control-group';
  }

  if(document.forms['metadata_form'].elements['metagenome_count'].value < 1  &&
            document.forms['metadata_form'].elements['metatranscriptome_count'].value < 1  &&
            document.forms['metadata_form'].elements['mimarks-survey_count'].value < 1 ) {
    alert('Please enter a positive value for one of the library types.');
    document.getElementById('metagenome_count_div').className = 'control-group error';
    document.getElementById('metatranscriptome_count_div').className = 'control-group error';
    document.getElementById('mimarks-survey_count_div').className = 'control-group error';
    return false;
  } else {
    document.getElementById('metagenome_count_div').className = 'control-group';
    document.getElementById('metatranscriptome_count_div').className = 'control-group';
    document.getElementById('mimarks-survey_count_div').className = 'control-group';
  }

  return true;
}

function validateBottomOfForm() {
  for (var i=0; i<document.forms['metadata_form'].elements.length; i++) {
    var element = document.forms['metadata_form'].elements[i];
    if(element.getAttribute("validate") == 'float') {
      if(element.value != "" && isNaN(element.value)) {
        alert('Please enter a valid decimal value for ' + element.getAttribute("displayField"));
        document.getElementById(element.name + '_div').className = 'control-group error';
        return false;
      } else {
        document.getElementById(element.name + '_div').className = 'control-group';
      }
    } else if(element.getAttribute("validate") == 'url') {
      if(element.value != "" && !isUrl(element.value)) {
        alert('Please enter a valid URL for ' + element.getAttribute("displayField") +
              '.  The URL is currently set to: ' + element.value);
        document.getElementById(element.name + '_div').className = 'control-group error';
        return false;
      } else {
        document.getElementById(element.name + '_div').className = 'control-group';
      }
    } else if(element.getAttribute("validate") == 'date') {
      if(element.value != "" && !isDate(element.value)) {
        alert('Please enter a valid date for ' + element.getAttribute("displayField") +
              '.  The date is currently set to: ' + element.value);
        element.style.cssText = 'width:100px;color:#B94A48;border-color:#B94A48;';
        return false;
      } else {
        element.style.cssText = 'width:100px;';
      }
    }
  }
  return true;
}

function validateEmail(x) {
  var atpos=x.indexOf("@");
  var dotpos=x.lastIndexOf(".");
  if(x == '') {
    return true;
  }
  if(atpos<1 || dotpos<atpos+2 || dotpos+2>=x.length) {
    return false;
  }
  return true;
}

function isDate(s) {
  var regexp = /\d{4}-\d{2}-\d{2}/;
  return regexp.test(s);
}

function isUrl(s) {
  var regexp = /(ftp|http|https):\/\/(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?/;
  return regexp.test(s);
}

function addMiscParam(fieldLevel, myDivId) {
  var myDiv = document.getElementById(myDivId);
  var param_number = myDiv.innerHTML.split("Miscellaneous Param").length + 1;
  if(param_number > 10) {
    var message_shown = myDiv.innerHTML.split("maximum allowed").length - 1;
    if(!message_shown) {
      var divTag = document.createElement("div"); 
      divTag.innerHTML = "<table><tr><td style='vertical-align:middle;width:395px;text-align:justify;padding:10px;'>Note: 10 miscellaneous parameters is the maximum allowed thru this web tool.  If you would like to enter more miscellaneous parameters, please enter them manually after downloading the spreadsheet.</td></tr></table>\n";
      myDiv.appendChild(divTag);
    }
  } else {
    var divTag = document.createElement("div"); 
    divTag.innerHTML = "<table><tr><td style='vertical-align:middle;width:195px;'><input type=\"checkbox\" name=\""+fieldLevel+"_misc_param_"+param_number+"_checkbox\" checked />&nbsp;&nbsp;Miscellaneous Param "+param_number+"<span id='"+fieldLevel+"_misc_param_"+param_number+"' data-original-title=\"\"><sup style='cursor: help;'>[?]</sup></span>&nbsp;:</td><td style='vertical-align:middle;'><input style='width:195px;' type='text' name='"+fieldLevel+"_misc_param_"+param_number+"'></td></tr>\n";
    myDiv.appendChild(divTag);
  }

  for(var i=2; i<=param_number; ++i) {
    eval("$('#"+fieldLevel+"_misc_param_"+i+"').popover({ 'title': 'Miscellaneous Param', 'content': 'any other measurement performed or parameter collected, that is not listed here'});");
  }
}
