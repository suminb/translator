var examples = [
    "여러분이 몰랐던 구글 번역기",
    "샌디에고에 살고 있는 김근모씨는 오늘도 힘찬 출근",
    "구글은 세계 정복을 꿈꾸고 있다.",
    "강선구 이사님은 오늘도 새로운 기술을 찾아나선다.",
    "전망 좋은 카페에 앉아 먹었던 티라미수",
    //"청년들을 타락시킨 죄로 독콜라를 마시는 홍민희"
];

var global = {};

window.onload = function() {
    var mode = getParameterByName("mode") == "1";
    $(mode ? "#radio-mode-1" : "#radio-mode-2").attr("checked", "checked");

    // The following code was copied from
    // http://stackoverflow.com/questions/2161906/handle-url-anchor-change-event-in-js
    if ("onhashchange" in window) { // event supported?
        window.onhashchange = function () {
            hashChanged(window.location.hash);
        }
    }
    else { // event not supported:
        var storedHash = window.location.hash;
        window.setInterval(function () {
            if (window.location.hash != storedHash) {
                storedHash = window.location.hash;
                hashChanged(storedHash);
            }
        }, 100);
    }
    
    hashChanged(window.location.hash ? window.location.hash : "");
    
    $("#text").autoResize({
        // On resize:
        onResize : function() {
            $(this).css({opacity:0.8});
        },
        // After resize:
        animateCallback : function() {
            $(this).css({opacity:1});
        },
        // Quite slow animation:
        animateDuration : 300,
        // More extra space:
        extraSpace : 40
    }).trigger("change");
}

/**
 * Parsing a URL query string
 * http://stackoverflow.com/questions/901115/how-can-i-get-query-string-values
 */
function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
    var regexS = "[\\?&]" + name + "=([^&#]*)";
    var regex = new RegExp(regexS);
    var results = regex.exec(window.location.search);
    if(results == null)
        return "";
    else
        return decodeURIComponent(results[1].replace(/\+/g, " "));
}

function onchangeTextarea(t) {
    console.log("textarea changed");
}

function resizeTextarea(t) {
    console.log("textarea onkeyup");
    console.log(t.cols);
    a = t.value.split('\n');
    b = 1;
    for (x=0;x < a.length; x++) {
        if (a[x].length >= t.cols) b+= Math.floor(a[x].length/t.cols);
    }
    b+= a.length;
    if (b > t.rows) t.rows = b;
}

function _translate() {
    var mode = $("#radio-mode-1").is(":checked") ? "1" : "2";
    var text = $("#text").val();
    console.log(text);
    $.get("/translate", {
            mode: mode,
            text: text
        }, function(response) {
            displayResult(response);
        }
    ).error(function(response) {
            console.log(response);
        }
    );
    
    return false;
}

// TODO: Refactor this function
function displayExample() {
    global.ei = parseInt(getParameterByName("example"));
    if (isNaN(global.ei)) {
        // Randomly chooses an example sentence
        global.ei = Math.floor(Math.random() * examples.length)
    }

    var example = examples[global.ei % examples.length];

    $("#text").html(example);
    _translate();
}

// TODO: Refactor this function
function refreshExample() {
    var example = examples[++global.ei % examples.length];

    $("#text").html(example);
    _translate();
}

function displayResult(result) {
    $("#result").html(result);
}

function hashChanged(hash) {
    if(hash.match(/^#t=/)) {
        $("#text").val(decodeURIComponent(hash.substring(3)));
        _translate();
    }
    else {
        displayExample();
    }
}

function toggle_screenshot() {
    $("#google-translate").toggle();
}