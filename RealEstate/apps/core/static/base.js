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
        // Nothing to do.
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
            if (data.name) {
                renderDeleteMessage(data.name);
            }
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
                $("#update_"+id).parent().parent().parent().css("background-color", "rgba(0, 255, 0,0.5)");
                $("#save-status").text("All changes saved.").show().css("color", "#333");
                $("#update_"+id).parent().parent().parent().animate({backgroundColor: "#fff"}, 3000);
            }, 1500);
        }
    });
};


// Close dismissable message windows.
function closeMessages () {
    return $(".alert.alert-dismissable button").click();
}

// Display appropriate message when an object is deleted.
function renderDeleteMessage(objectText) {
    closeMessages();
    var div = $('<div>')
              .appendTo('#messages')
              .addClass('alert alert-info alert-dismissable');
    $("<button>").appendTo(div)
                 .attr('type', 'button')
                 .attr('data-dismiss', 'alert')
                 .attr('aria-hidden', 'true')
                 .addClass('close')
                 .html("&times;");
    div.append("Successfully deleted '"+objectText+"'");
}
