var catagory_list = new Array()
function enterTagFunction() {
    var tag = prompt("Enter a catagory tag", "blog");
    var current_list = document.getElementById("initial-id_categories").value;
    current_list = current_list.split(",");
    for (var i = 0; i < current_list.length; i++){
        var curr_tag = current_list[i].replaceAll(/[\[\]'" ]+/g, "");
        if (!catagory_list.includes(curr_tag)){
            catagory_list.push(curr_tag)
        }
    }

    if (tag != null && !catagory_list.includes(tag) ) {
        var string_catagory = ''
        catagory_list.push(tag)
        for (var i = 0; i < catagory_list.length; i++){
            if (catagory_list[i] != ""){
                string_catagory += '"'+catagory_list[i] + '"'
                if (i != catagory_list.length - 1){
                    string_catagory += ","
                }
            }
        }
        document.getElementById("id_categories").innerHTML = '[' + string_catagory +']';
    }
    else
    {
        alert("That category tag already exists!");
    }
}

// Reference : https://ricardometring.com/getting-the-value-of-a-select-in-javascript
function validate()
{
    var select_vis = document.getElementById('id_visibility');
    var value_vis = select_vis.options[select_vis.selectedIndex].value;

    if (value_vis == "PUBLIC" || value_vis == "FRIENDS"){
        document.getElementById("id_unlisted").setAttribute("disabled", "disabled");
        document.getElementById("id_recipient_uuid").setAttribute("disabled", "disabled");
        document.getElementById("id_unlisted").checked = false;
        document.getElementById("id_recipient_uuid").required = false;
    }else{
        document.getElementById("id_unlisted").removeAttribute("disabled", "disabled");
        document.getElementById("id_recipient_uuid").removeAttribute("disabled", "disabled");
        document.getElementById("id_unlisted").checked = true;
    }
}

window.onload = function(){
    validate();
}
