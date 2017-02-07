gapi.load('auth2', function() {
  auth2 = gapi.auth2.init({
    client_id: '381164472914-mpv6ips7t4hlc1672olafq556h59uiu2.apps.googleusercontent.com',
  });
});

$('#signinButton').click(function() {
    auth2.grantOfflineAccess({'redirect_uri': 'postmessage'}).then(signInCallback);
});

function signInCallback(json) {
  console.log('enter callback')
  authResult = json;
  if (authResult['code']) {
    // Hide the sign-in button now that the user is authorized, for example:
    $('#signinButton').attr('style', 'display: none');
    $('#result').html('One-Time Auth Code:</br>'+ authResult['code'] + '')
    // Send the code to the server
    $.ajax({
      type: 'POST',
      processData: false,
      data: JSON.stringify({"auth_code":authResult['code']}),
      dataType: "json",
      contentType: "application/json",
      success: function(result) {
        console.log('success')
        // Handle or verify the server response if necessary.
        if (result) {
          $('#result').html('Login Successful!</br>'+ result + '')
        } else if (authResult['error']) {
          console.log('There was an error: ' + authResult['error']);
        } else {
          $('#result').html('Failed to make a server-side call. Check your configuration and console.');
        }
      },
      error: function(e) {
        console.log(e);
      }
    });
  }
}