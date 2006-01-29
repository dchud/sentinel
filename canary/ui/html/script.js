// $Id$

// Uncomment to remove debugging info
createLoggingPane(true);

// *visible() funcs are suggested code from MochiKit docs
function toggleVisible(elem) {
    toggleElementClass("invisible", elem); 
}

function makeVisible(elem) {
    removeElementClass(elem, "invisible");
}

function makeInvisible(elem) {
    addElementClass(elem, "invisible");
}

function isVisible(elem) {
    // you may also want to check for
    // getElement(elem).style.display == "none"
    return !hasElementClass(elem, "invisible");
}; 


var succeeded = function (r) {
    if (r['status'] == '200') {
        ; // Success; maybe flash something?
    } else {
        alert(r['reason']);
    }
};

var failed = function (err) {
    alert('An error occurred, please try again.');
};

var hidewait = function (waitimage) {
    waitimage.innerHTML = '';
};

function record_has_sets (record_id) {
    var has_sets = 0;
    var record_set_checks = getElementsByTagAndClassName('input', 'checkbox');
    for (i=0; i<record_set_checks.length; i++) {
        var check = record_set_checks[i];
        var id = getNodeAttribute(check, 'id');
        if (id.indexOf('record-' + record_id + '-set') >= 0) {
            if (check.checked == true) {
                has_sets +=1;
            }
        }
    }
    return has_sets;
};

function recordClicked (record_id, user_id) {
    var recordsets = getElement('recordsets-' + record_id);
    var checkinput = getElement('recordcheckinput-' + record_id);
    var waitimage = getElement('waitimage-' + record_id);
    waitimage.innerHTML = '<img src="/images/wait.gif" alt="wait" />';
    var nowait = partial(hidewait, waitimage);
    var url = '';
    if (checkinput.checked == true) {
        url = '/user/add_record?record_id=' + record_id;
        makeVisible(recordsets);
    } else {
        var record_sets = record_has_sets(record_id);
        if (record_sets > 0) {
            if (!confirm("Drop record and its sets?")) {
                setNodeAttribute(checkinput, 'checked',  'CHECKED');
                waitimage.innerHTML = '';
                return;
            }
        }
        url = '/user/remove_record?record_id=' + record_id;
        makeInvisible(recordsets);
    }
    var d = loadJSONDoc(url);
    d.addCallbacks(succeeded, failed);
    d.addBoth(nowait);
};

function recordSetClicked (record_id, set_id) {
    var record_check = getElement('recordcheckinput-' + record_id)
    var rstr = 'record-' + record_id + '-set-' + set_id;
    var checkinput = getElement(rstr + '-checkinput');
    var waitimage = getElement('waitimage-' + record_id);
    waitimage.innerHTML = '<img src="/images/wait.gif" alt="wait" />';
    var nowait = partial(hidewait, waitimage);
    var url = '';
    if (checkinput.checked == true) {
        url = '/user/add_record_set?record_id=' + record_id + '&set_id=' + set_id;
        record_check.disabled = 'disabled';
    } else {
        url = '/user/remove_record_set?record_id=' + record_id + '&set_id=' + set_id;
        var record_sets = record_has_sets(record_id);
        if (record_sets == 0) {
            record_check.disabled = false;
            setNodeAttribute(record_check, 'checked',  'CHECKED');
        }
    }
    var d = loadJSONDoc(url);
    d.addCallbacks(succeeded, failed);
    d.addBoth(nowait);
}


function startCreateSet (id) {
    logDebug('Creating inputForm');
    var inputForm = FORM({'action': '/user/create-set',
        'method': 'get',
        'id': 'createsetform-' + id},
        INPUT(null, {'name': 'setname',
            'size': 30})
        );
    logDebug('Getting createuserset create-set-link-' + id);
    var createuserset = getElement('create-set-link-' + id);
    if (createuserset) {
        swapDOM(createuserset, inputForm);
    } else {
        logDebug('createuserset not found');
    }
}


function addUserSet (evt) {
    evt = (evt) ? evt : event;
    var charCode = (evt.charCode) ? evt.charCode :
        ((evt.which) ? evt.which : evt.keyCode);
    logDebug('charCode: ' + charCode);
    if (charCode == 13 || charCode == 3) {
        var waitimage = getElement('waitimage');
        waitimage.innerHTML = '<img src="/images/wait.gif" alt="wait" />';
        var nowait = partial(hidewait, waitimage);
        var set_name_input = getElement('set_name_input');
        var input = set_name_input.value;
        var url = '/user/create_set?set_name=' + input;
        var d = loadJSONDoc(url);
        var success = function (r) {
            if (r['status'] == '406') {
                alert(r['reason']);
            } else if (r['status'] == '200') {
                var uid = r['uid'];
                var newSet = TR({'id': 'usersetrow-' + uid,
                        'class': 'userset'},
                    TD({'class': 'userset',
                        'id': 'userset-' + uid},
                        A({'href': '/user/set/' + uid},
                            [input])),
                    TD(null, '0 records'),
                    TD(null, 
                        ['[',
                        A({'href': '/user/set/' + uid + '/lock'},
                            ['lock']),
                        '] [',
                        A({'href': '/user/set/' + uid + '/delete'},
                            ['delete']), 
                        ']']
                        )
                    );
                var addnewset = getElement('addnewset');
                removeElement(addnewset);
                var usersets = getElement('usersets');
                appendChildNodes(usersets, newSet, addnewset);
                set_name_input.value = '';
            }
        };
        d.addCallbacks(success, failed);
        d.addBoth(nowait);
    }
}
