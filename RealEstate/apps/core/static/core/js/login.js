(function () {
    var errorClass = 'alert alert-danger';
    var loadingClass = 'loading';

    var $loginForm = $('#login-form');
    var $loginFeedback = $('#login-feedback');

    var $emailInput = $('#modal-login #id_username');
    var $passwordInput = $("#modal-login #id_password");

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
            $passwordInput.val("").focus();
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

    // Focus on the email input field if it is empty, otherwise focus password
    $('#modal-login').on('shown.bs.modal', function shownModal() {
        var $emailInput = $('#modal-login #id_username');
        if (!$emailInput.val()) {
            $emailInput.focus();
        } else {
            $passwordInput.focus();
        }
    });

    $('#modal-login').on('hidden.bs.modal', function hiddenModal() {
        $loginFeedback.removeClass().empty();
    });
})();
