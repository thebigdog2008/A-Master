$(function() {
    var ul = document.querySelector("#content-main > ul");
    var li = document.createElement("li");
    var a = document.createElement("a");
    a.setAttribute("href","/api/custom-auth/user-report/");
    a.setAttribute("class","addlink");
    a.appendChild(document.createTextNode("User report"));
    ul.appendChild(li);
    li.appendChild(a);
});