/*
 * Base JQuery functions for RealEstate Web App
 * Capstone Group G, July 2015
 */

//
// Displays and acts on hoverable icons. To use, at least one argument is required,
// the class of the div over which you are hovering. After that, you may list as
// many showable icons as you wish by listing their id's.
// EXAMPLE: hoverActions("hover-div", "edit-icon", "delete-icon")
function hoverActions () {
    row = arguments[0];
    icon = [];
    for (var i=1; i<arguments.length; i++)
        this.icon.push(arguments[i]);
    $("." + row).mouseenter( function() {
        var id = $(this).attr("id").toString().replace(/row_/i, "");
        for (var i=0; i< icon.length; i++)
            $("#" + icon[i]+ "_" + id).fadeIn("slow");
        if ( $('#edit-modal').length ) {
            $("#edit_"+id).click(function(){
                getData(id, function(data) {
                    for(key in data) {
                        if ($('#edit-modal input[name='+key+']').length )
                            $('#edit-modal input[name='+key+']').val(data[key]);
                        else
                            $('#edit-modal textarea[name='+key+']').val(data[key]);
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
        for (var i=0; i < icon.length; i++)
            $("#" + icon[i]+ "_" + id).stop().fadeOut("fast");
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

// Deletes data given an ID
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

// Post slider data.
function slideChange (slideEvt) {
	var timer;
	clearTimeout(timer);
	var id = $(this).attr("id").toString().replace(/category_/i, "");
	$("#save-status").text("saving...").css("color", "#888");
	$.ajax({
		type: "POST",
		data: {
			csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].value,
			id: id,
			value: slideEvt.value.newValue,
			type: "update"
		},
		success: function(data) {
			timer = setTimeout(function(){
                $("#update_"+id).stop().show();
                $("#update_"+id).fadeOut(2000);
                $("#save-status").text("All changes saved.").show().css("color", "#333");
			}, 1500);
		}
	});
};
