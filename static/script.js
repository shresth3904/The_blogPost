function intersection(arr1, arr2) {
    return arr1.filter(value => arr2.includes(value));
}


let selected = [];

function show(TAG){
    console.log(all);
    selected.push(TAG);
    document.getElementById("tag").innerText = "✖ clear";
    document.getElementById("tag").className = "clear";
    document.getElementById(TAG).className = "tag_selected";
    for (let id of all){
        document.getElementById(id).style.display = "none";
    }
    let net = all;
    for (let tag of selected){
        console.log(tags[tag]);
        net = intersection(net, tags[tag]);
    }
    for (let id of net){
        document.getElementById(id).style.display = "flex";
    }
}


function clear_tags(){
    for (let tag of selected){
        document.getElementById(tag).className = "tag_categories";
    }
    for (let id of all){
        document.getElementById(id).style.display = "flex";
    }

    document.getElementById("tag").innerText = "#TAGS";
    document.getElementById("tag").className = "tag";

    selected = [];

}

function fetch_blog(id){
    window.location.href = blogUrl + "?id=" + encodeURIComponent(id);
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
    
}

function main_menu() {
    window.location.href = homeUrl
}

function setDefaultImage(imageElement) {
        imageElement.onerror = null; 
        imageElement.src = "{{ url_for('static', filename='blog.png') }}";
    }

document.getElementById('search_bar').addEventListener('input', function() {
  const suggestionsDiv = document.getElementById('suggestions');
  
  if (this.value.trim() !== '') {
    // If the input has any text, show the suggestions div.
    suggestionsDiv.style.display = 'block';
  } else {
    // If the input is empty, hide the suggestions div.
    suggestionsDiv.style.display = 'none';
  }
});


let input = document.querySelector('#search_bar');
input.addEventListener('input', async function() {
    let response = await fetch('/search?q=' + input.value);
    let blogs = await response.json();
    let html = '';
    for (let blog of blogs) {
        let title = blog.title;
        html += `<div id = "search_value" onclick = 'fetch_blog(${blog.id})'>
                    ⌕ ${title}
                </div>`;
    }
    document.querySelector('#suggestions').innerHTML = html;
});