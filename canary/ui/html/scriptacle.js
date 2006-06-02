// javascript routines specific to scriptaculous; to be called only 
// on pages not needing mochikit.
//
// $Id$

// Handle selections of human references on curate_five/summarize screen.
function addSummaryRef (input, item) {
    var d = document;
    var human_refs = d.getElementById('human-refs');
    var origHtml = human_refs.innerHTML;
    var match = item.innerHTML.match(/([\d]+)/);
    if (match != null) {
        var id = match[0];
        var element_id = "human-ref-" + id;
        var already_there = d.getElementById(element_id);
        if (already_there == null) {
            human_refs.innerHTML = origHtml + 
                '<div id="wrap-' + element_id + '" style="display:none;"><input id="' + element_id + '" checked="checked" type="checkbox" name="' + element_id + '" />' + item.innerHTML + '</div>\n';
            Effect.Appear("wrap-" + element_id, {duration: 1.0});
        } else {
            alert('That human reference is already listed.');
        }
        var input_field = d.getElementById('autocomplete_input');
        input_field.value = '';
    }
}

// Determine whether a form f has at least one item of type element_type with
// a name starting with any item in prefix_array that is selected.
function hasOneSelected (f, element_type, prefix_array) {
    var found = false;
    for (var i=0; i<f.length; i++) {
        var e = f.elements[i];
        if (e.type == element_type) {
            for (var p=0; p<prefix_array.length; p++) {
                var prefix = prefix_array[p];
                if (e.name.indexOf(prefix) >= 0) {
                    if (e.checked == true) {
                        found = true;
                        break;
                    } else {
                        // ignore
                    }
                }
            }
        }
    }
    
    return found;
}

// Verify new summaries in-place before submission
function verifySummary () {
    var f = document.getElementById('summary_form');
    
    // Check methodologies.  One must be selected.
    if (hasOneSelected(f, 'radio', ['methodology']) != true) {
        alert('Please choose a methodology.');
        return false;
    }
    
    // Check exposures and outcomes.  At least one of either must be selected.
    if (hasOneSelected(f, 'checkbox', ['exposures', 'outcomes']) != true) {
        alert('Please choose at least one exposure or outcome.');
        return false;
    }
    
    // Check species.  At least one must be selected.
    if (hasOneSelected(f, 'checkbox', ['species']) != true) {
        alert('Please choose at least one species.');
        return false;
    }
    
    // NOTE:  True?  At least on linkage should be selected, whether positive or negative.
    if (hasOneSelected(f, 'checkbox', ['has']) != true) {
        alert('Please choose at least one (positive or negative) linkage to human health.');
        return false;
    }
    
    // Note: Human references are optional.
    // Note: Public notes are optional.
    
    // Must be okay, so submit form to summary/add
    return true;
}
