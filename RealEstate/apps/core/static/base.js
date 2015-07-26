/*
 * Base JQuery functions for RealEstate Web App
 * Capstone Group G, July 2015
 */
var Page = function() {
    this.row = arguments[0];
    this.type = arguments[1];
    this.icon = [];
    console.log(arguments.length);
    for (var i=2; i<arguments.length; i++)
        this.icon.push(arguments[i]);
};
function hoverActions (Page) {
    $("." + Page.row).mouseenter( function() {
        console.log($(this).attr("id"));
        var id = $(this).attr("id").toString().replace(/row_/i, "");
        console.log(id);
        for (var i=0; i< Page.icon.length; i++){
            $("#"+Page.icon[i]+ "_" + id).fadeIn("slow");
            console.log("#"+Page.icon[i]+ "_" + id);
        }
        
        if ( $('#edit-modal').length ) {
            $("#edit_"+id).click(function(){
                getData(id, function(data) {
                    for(key in data) {
                        if ($('#edit-modal input[name='+key+']').length ) {
                            $('#edit-modal input[name='+key+']').val(data[key]);
                        } else {
                            $('#edit-modal textarea[name='+key+']').val(data[key]);
                        }
                    }
                    $('input[name="id"]').val(id);
                });
            });
            $("#delete_"+id).click( function(){
                var sum = $(this).parent().text();
                $("#confirmDelete").data("id", id );
                $("#confirmDelete .btn-danger").text("Delete " + sum);
            });
        }
    }).mouseleave( function() {
        var id = $(this).attr("id").toString().replace(/row_/i, "");
        for (var i=0; i<Page.icon.length; i++)
            $("#"+Page.icon[i]+ "_" + id).stop().fadeOut("fast");
    });
}
// Get model data from ID.
function getData(id, callBack) {
    $.ajax({
        type: "GET",
        data: {
            id: id
        },
        success: callBack
    });
}
// Deletes home given an ID
function deleteData(deleteID) {
    $.ajax({
        type: "POST",
        data: {
            csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
            id: deleteID,
            type: "delete"
        },
        success: function(data) {
            $("#li_"+data.id).remove();
        }
    });
}