(function () {
    var errorClass = 'alert alert-danger';
    var loadingClass = 'loading';

    var $loginForm = $('#login-form');
    var $loginFeedback = $('#login-feedback');

    $loginForm.submit(function(e) {
        e.preventDefault();
        if (this.classList.contains(loadingClass)) {
            return false;
        }

        // On error: remove loading class, display error, clear password field.
        function resetForm (node, error) {
            node.classList.remove(loadingClass);
            $loginFeedback.addClass(errorClass)
                          .text(error);
            $("input[type='password']").val("");
        }

        var self = this;
        self.classList.add(loadingClass);
        $loginFeedback.removeClass().empty();
        $.ajax({
          type: "POST",
          url: "/login-handler/",
          dataType: 'json',
          data: $loginForm.serialize(),
          success: function (response) {
              if (response.success) {
                  window.location = response.location;
              } else {
                  resetForm(self, "Login Failed");
              }
          },
          error: function() {
              resetForm(self, "Server Error");
          },
        });
    });
})();
