function nextPicture(){
    var pics = ["burger1.png", "burger2.png"];
    

    var myImage = document.querySelector('.myImg');
    var index = parseInt(myImage.getAttribute('index'));
    index = (index + 1) % pics.length ;
    

    myImage.src = pics[index];
    myImage.setAttribute('index', index);
    
}
function prevPicture(){
    var pics = ["burger1.png", "burger2.png"];
    

    var myImage = document.querySelector('.myImg');
    var index = parseInt(myImage.getAttribute('index'));
    if(index === 0){
        index = pics.length - 1;
    } else {
        index =(index - 1) % pics.length ;
    }

    myImage.src = pics[index];
    myImage.setAttribute('index', index);
}

//Add next button click handler
document.querySelector('#nextBtn').addEventListener('click', e => {
    nextPicture();
})

document.querySelector('#prevBtn').addEventListener('click', e => {
    prevPicture();
})
function addComment(){
    comments = document.querySelector('.commentList');

    var node = document.createElement('li');
    var textnode = document.createElement('span');
    
    textnode.className = "Username";
    textnode.innerText = 'Dang, that is a good looking burger!';
    
    node.appendChild(textnode);
    comments.appendChild(node);
}


document.querySelectorAll('.myPhoto').addEventListener('click', e => { 
    console.log(e); }
)
console.log("This is working")