var catagory_list = new Array()
function enterTagFunction() {
    var person = prompt("Enter a catagory tag", "blog");
    var current_list =  JSON.parse("[" + document.getElementById("initial-id_categories").value + "]"); 
    current_list = current_list.toString().split(",")
    if (person != null && !current_list.includes(person) ) {
        current_list.push(person)
        var string_catagory = ''
        for (var i = 0; i < current_list.length; i++){
            string_catagory += '"'+current_list[i] + '"'
            if (i != current_list.length - 1){
                string_catagory += ","
            }
        }
        document.getElementById("id_categories").innerHTML = '[' + string_catagory +']';
    }
    else
    {
        alert("That category tag already exists!");
    }
}