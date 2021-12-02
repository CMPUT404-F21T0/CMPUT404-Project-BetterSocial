var catagory_list = new Array()

function enterTagFunction() {
    var new_catagory_list = catagory_list.concat(JSON.parse(document.getElementById("initial-id_categories").value))
    var tag = prompt("Enter a catagory tag", "blog");
    
    if (tag != null && !new_catagory_list.includes(tag) ) {
        new_catagory_list.push(tag)
        var string_catagory = ''
        for (var i = 0; i < new_catagory_list.length; i++){
            string_catagory += '"'+new_catagory_list[i] + '"'
            if (i != new_catagory_list.length - 1){
                string_catagory += ","
            }
        }
        document.getElementById("id_categories").innerHTML = '[' + string_catagory +']';
    }
    else if (new_catagory_list.includes(tag)) {
        alert("That category tag already exists!");
    }
}