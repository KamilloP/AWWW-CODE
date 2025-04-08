  // Ustawienie podstawowych elementów
  var toggler = document.getElementsByClassName("folder");

  for (let i = 0; i < toggler.length; i++) {
    toggler[i].addEventListener("click", function() {
      this.parentElement.querySelector(".nested").classList.toggle("active");
      this.classList.toggle("folder-down");
    });
  }

  // Zmiana widoku strony (na ciemny/jasny)

  document.getElementById('light-mode-button').onclick = function() {
    document.getElementById('light-mode-button').style.display = 'none';
    document.getElementById('dark-mode-button').style.display = 'block';
    var r = document.querySelector(':root');
    r.style.setProperty('--background', 'rgb(213, 207, 166)');
    r.style.setProperty('--border', 'rgb(66, 19, 22)');
    r.style.setProperty('--header', 'rgb(14, 47, 88)');
    r.style.setProperty('--elements', 'rgb(6, 28, 55)');
    r.style.setProperty('--font', 'rgb(0, 0, 0)');
  }
  document.getElementById('dark-mode-button').onclick = function() {
    document.getElementById('dark-mode-button').style.display = 'none';
    document.getElementById('light-mode-button').style.display = 'block';
    var r = document.querySelector(':root');
    r.style.setProperty('--background', 'rgb(6, 25, 35) ');
    r.style.setProperty('--border', 'rgb(192, 177, 178)');
    r.style.setProperty('--header', 'rgb(42, 5, 5)');
    r.style.setProperty('--elements', 'rgb(53, 8, 19)');
    r.style.setProperty('--font', 'rgb(255, 255, 255)');
  }

  // csrf_token

  $.ajaxSetup({
    data: {csrfmiddlewaretoken: '{{ csrf_token }}' },
  });

  // Klasy

  class UserFile {
    constructor(pk, name, description, content) {
      this.pk = pk;
      this.name = name;
      this.description = description;
      this.content = content;
    }
  }

  // Zmienne

  var current_file;
  var inserting = false;
  var deleting = false;

  // Funkcje

  // function isNumeric(str) {
  //   if (typeof str != "string") return false
  //   return !isNaN(str);
  // }

  function showInsertChoose() {
    $(".item.files form").remove();
    if (inserting) {
      $(".insert").hide();
      inserting = false;
    }
    else {
      inserting = true;
      $(".insert").show();
    }
    deleting = false;
    $(".delete").hide();
  }

  function showDeleteChoose() {
    $(".item.files form").remove();
    if (deleting) {
      $(".delete").hide();
      deleting = false;
    }
    else {
      deleting = true;
      $(".delete").show();
    }
    inserting = false;
    $(".insert").hide();
  }

  function chooseCurrentFile(id) {
    $.ajax({
      url: "{% url 'fileInfo' %}",
      type: 'POST',
      dataType: 'json',
      data: {
        'csrfmiddlewaretoken': $("input[name=csrfmiddlewaretoken]").val(),
        "file_id": id,
      },
      success: function(response) {
        if (response.status == 'success' && response.pk == id){
          current_file = new UserFile(
            response.pk,
            response.name,
            response.description,
            response.content
          );
          $(".item.code > p").text(current_file.name);
          $(".item.code > textarea").remove();
          let $textarea = $('<textarea>').val(current_file.content);
          $(".item.code").append($textarea);
          $(".item.code > textarea").attr("spellcheck", "false");
          $(".item.snippet > p").text(current_file.name);
        }
        else {
          alert("An error has occurred:" + response.status);
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        console.error('Error: ', errorThrown);
      }
    });
  }

  function removeFile(id) {
    deleting = false;
    $(".delete").hide();
    $.ajax({
      url: "{% url 'deleteFile' %}",
      type: 'POST',
      dataType: 'json',
      data: {
        'csrfmiddlewaretoken': $("input[name=csrfmiddlewaretoken]").val(),
        "file_id": id,
      },
      success: function(response) {
        if (response.status == 'success' && response.pk == id){
          $(".file." + id).parent().remove();
        }
        else {
          alert("An error has occurred:" + response.status);
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        console.error('Error: ', errorThrown);
      }
    });
  }

  function removeFolder(id) {
    deleting = false;
    $(".delete").hide();
    $.ajax({
      url: "{% url 'deleteFolder' %}",
      type: 'POST',
      dataType: 'json',
      data: {
        'csrfmiddlewaretoken': $("input[name=csrfmiddlewaretoken]").val(),
        "folder_id": id,
      },
      success: function(response) {
        if (response.status == 'success' && response.pk == id){
          $(".folder." + id).parent().remove();
        }
        else {
          alert("An error has occurred:" + response.status);
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        console.error('Error: ', errorThrown);
      }
    });
  }

  function insertFolder(id, name) {
    inserting = false;
    $(".insert").hide();
    $(".item.files").append('<form id="insert_folder_form" action="{% url "postFolderForm" %}" method="POST" style="margin-bottom: 0px;">');
    $("#insert_folder_form").append('{% csrf_token %}');
    $("#insert_folder_form").append('<div class="appm">Dodaj folder do ' + name + '</div>');
    $("#insert_folder_form").append('<input type="text" placeholder="Nazwa" name="folder-name" id="folder-name" maxlength="255"/>');
    $("#insert_folder_form").append('<input type="text" placeholder="Opcjonalny opis" name="folder-description" id="folder-description" maxlength="255" value="" style="word-break: break-word;"/>');
    $("#insert_folder_form").append('<br><input type="submit" id="savebutton" value="Dodaj" />');
    $("#insert_folder_form").append("</form>");
    $('#insert_folder_form').on('submit', function(event){
        event.preventDefault();
        create_post_folder(id);
    });
  }

  function create_post_folder(id) {
    $.ajax({
      url : "{% url 'postFolderForm' %}", // the endpoint
      type : "POST", // http method
      data : {
        name: $('#folder-name').val(),
        description: $('#folder-description').val(),
        pk: id,
        csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
      }, // data sent with the post request
      success : function(response) {
          if (response.status == 'success' && response.pk == id) {
            $("#insert_folder_form").remove();
            $(".folder." + id).parent().children(".nested").append("<li></li>");
            $(".folder." + id).parent().children(".nested").children("li:last").
              append('<span class="folder ' + response.new_id + '">' + response.name + '</span>');
            $(".folder." + id).parent().children(".nested").children("li:last").
              append('<span class="insert" style="display: none;"> | <a href="" onclick="insertFile(' + response.new_id + ', ' + response.name + ');return false;">Dodaj plik</a> |'  + '<a href="" onclick="insertFolder(' + response.new_id + ', ' + response.name + ');return false;">Dodaj folder</a> |</span>');
            $(".folder." + id).parent().children(".nested").children("li:last").
              append('<span class="delete" style="display: none;"> | <a href="" onclick="removeFolder(' + response.new_id + ');return false;">| Usuń |</a></span>');
            $(".folder." + id).parent().children(".nested").children("li:last").
              append('<ul class="nested"></ul>');
            var temp_toggler = document.getElementsByClassName("folder " + response.new_id);
            temp_toggler[0].addEventListener("click", function() {
              this.parentElement.querySelector(".nested").classList.toggle("active");
              this.classList.toggle("folder-down");
            });
          }
          else {
            alert("Error");
          }
      },
      error : function(xhr,errmsg, err) {
        alert("Error: " + err);
      }
    });
  }

  function insertFile(id, name) {
    alert("insert file " + id);
  }

  // Dodanie linków do ustawienia strony.

  // $(document).ready(function () {
  //   let file_list = document.getElementsByClassName("file");
  //   for (let file of file_list) {
  //     let f = file.className.split(/\s+/);
  //     // file.children[1].children[0] to <a>| Usuń |</a>
  //     file.children[1].children[0].setAttribute("href", "#");
  //     file.children[1].children[0].setAttribute("onclick", "removeFile(" + f[1] + ")");
  //   }
  //   // let folder_list = document.getElementsByClassName("");
  //   // for (let file of file_list) {
  //   //   let f = file.className.split(/\s+/);
  //   //   // file.children[1].children[0] to <a>| Usuń |</a>
  //   //   file.children[1].children[0].setAttribute("href", "#");
  //   //   file.children[1].children[0].setAttribute("onclick", "removeFile(" + f[1] + ")");
  //   // }
  //   // for (let file of file_list) {
  //   //   let f = file.className.split(/\s+/);
  //   //   for(let c of f) {
  //   //     if (!isNan(c)) {
  //   //       let id = parseInt(c);
  //   //       alert(c);
  //   //       // $(this).text(s);
  //   //       // $(this).attr("title", "Click to choose current file");
  //   //       // $(this).attr("href", "#");
  //   //       // $(this).css("text-decoration", "none");
  //   //       // $(this).css("color", "inherit");
  //   //       // $(this).attr("onclick", "chooseCurrentFile(" + c + ");return false;");
  //   //     }
  //   //     // alert(c);
  //   //   }
  //   // }
  // });

  // $("a.file-id").each(function() {
  //   let s = $(this).text();
  //   let ret = s.split(" ");
  //   let id = parseInt(ret[0]);
  //   s = ret[1];
  //   for(let i = 2; i < ret.length; i++) {
  //     s += " ";
  //     s += ret[i];
  //   }
  //   $(this).text(s);
  //   // $(this).attr("onclick", "chooseCurrentFile(" + id + ");return false;");
  // });