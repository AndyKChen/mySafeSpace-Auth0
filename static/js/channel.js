document.addEventListener('DOMContentLoaded', () => {

    //connect to websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    // get username
    const sender = document.getElementById('get-username').innerHTML;


    socket.on('connect', () => {
        
        
        socket.emit("joined channel")

        document.addEventListener('onhashchange', () => {
            socket.emit("left")
        });

        
        updateScroll()

        document.querySelector('#text').addEventListener('keydown', event => {
            if (event.key == "Enter") {
                document.getElementById('button-send').click()
            }
        });

        document.querySelector('#button-send').addEventListener('click', () => {
            let msg = document.getElementById('text').value.trim();

            if (!msg || msg.length === 0) {
                return;
            }

            let timestamp = new Date;
            timestamp = timestamp.toLocaleDateString();    

            socket.emit('channel message', msg, timestamp, sender);

            document.getElementById('text').value = '';
        });
    });

    socket.on('announce channel_msg', data => {
        // Format message
        if (data.sender == sender) {

            $(function () {

                // Get template
                var template = $("#outgoing_template").html();
            
                // Create a new row from the template
                var $row = $(template);
            
                // Add data to the row
                $row.find("p[data-template='temp_message']").text(data.msg);
                $row.find("span[data-template='temp_time']").text(data.timestamp);
            
                // Add the row to the table
                $("#newmsg").append($row);

                updateScroll();
            });
        }
        else {
            $(function () {

                // Get template
                var template = $("#incoming_template").html();
            
                // Create a new row from the template
                var template_dom = $('<div/>').append(template);
                var $row = $(template);
                
                var img = "<img src=../static/avatars/beard.png>";

                // Add data to the row
                $row.find("p[data-template='temp_message']").text(data.msg);
                $row.find("span[data-template='temp_time']").text(data.timestamp);
                $row.find("small[data-template='sender']").text(data.sender);
                $row.find("div[data-template='temp_img']").html(img);
            
                // Add the row to the table
                $("#newmsg").append($row);

                updateScroll();
            });


        }
    });

    socket.on('status', data => {
        document.getElementById('joined').innerHTML = data.msg 
        updateScroll();
    });

    socket.on('warning message', data => {
        // set cookie
        expiry = new Date();
        expiry.setTime(expiry.getTime()+(10*1000)); 

        // Date()'s toGMTSting() method will format the date correctly for a cookie
        document.cookie = "timeout=yes; expires=" + expiry.toGMTString();

        // give user timeout from sending messages
        document.getElementById("button-send").disabled = true;
        setTimeout(function(){
            document.getElementById("button-send").disabled = false;
            }, 10000);

        // grey out send button for duration of timeout
        document.getElementById("button-send").style.background = "grey"
        setTimeout(function (){
            document.getElementById("button-send").style.background = "#05728f";
            }, 10000);

        // enable popup indicating timeout
        $(function togglePopup() {        
            document.getElementById("modal-btn").click();
            document.getElementById("warning-msg").innerHTML = data.msg;
          });
    });

    // check for timeout cookie
    if (document.cookie.indexOf("timeout=") >= 0) {
        document.getElementById("button-send").disabled = true;
        document.getElementById("button-send").style.background = "grey"
      }
    else {
        document.getElementById("button-send").style.background = "#05728f";
        document.getElementById("button-send").disabled = false;
    }

    // automatically scroll to bottom of page
    function updateScroll() {
        var objDiv = document.getElementById("newmsg");
        objDiv.scrollTop = objDiv.scrollHeight;
    }

});