
const socket = new WebSocket("ws://192.168.68.108:8765");

function joinChat(event){
    if(localStorage.getItem("id") == null) {
        socket.send(JSON.stringify({"event": "join"}));
    }
}

function displayMessage(data){
    // let messageText = $("#messageinput").val();

    console.log("Recieved " + data.message);

    const width = 900;
    const height = 100;

    let svgMessage = $(`
        <svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
            <!-- Background rectangle -->
            <rect x="0" y="0" width="${width}" height="${height}" fill="#000000" />
            
            <text x="0" y="20" font-size="16" fill="white" text-decoration="underline">${data.name}</text>
        
            <text x="0" y="50%" font-size="16" fill="white">${data.message}</text>
        </svg>
    `);

    var position = getPosition(width, height);
    svgMessage.css({
        position: "absolute",
        left: position.x + "px",
        top: position.y + "px",
        opacity: 1,
    });

    $(".void").append(svgMessage);

    svgMessage.fadeOut(2000);

    // $("#messageinput").val('');
}


socket.addEventListener("error", (event)=>{
    console.log(event);
})

socket.addEventListener("open", joinChat);

let event_handler = {
    'joined': (data)=>{
        // ideally just copy
        localStorage.setItem('id', data.id);
        localStorage.setItem('name', data.name);
        console.log(localStorage);
        $("#username").text(localStorage.getItem('name') + ":");
    },
    'broadcast': (data)=>{
        displayMessage(data);
    }
}

socket.addEventListener("message", (event)=>{
    console.log("Message from server ", event.data);
    let data = JSON.parse(event.data);
    event_handler[data.event](data);
});

socket.addEventListener("close", (event)=>{
    console.log("closing...");
    localStorage.clear();
})

function getPosition(boxSizeX, boxSizeY) {
    var containerWidth = $(".void").width();
    var containerHeight = $(".void").height();
    var x = Math.floor(Math.random() * containerWidth);
    var y = Math.floor(Math.random() * containerHeight);
    return { x: x, y: y };
}

$("#whisper").on("click", ()=>{
    if(socket.readyState != WebSocket.CLOSED) {
        let messageText = $("#messageinput").val(); 
        socket.send(JSON.stringify({
            "event": "broadcast", 
            "id": localStorage.getItem("id"), 
            "name": localStorage.getItem("name"), 
            "message": messageText
        }));
    }
});

$("#messageinput").on('keypress', (e)=>{
    if(e.which == 13) {
        $("#whisper").click();
        e.preventDefault();
    }
});
