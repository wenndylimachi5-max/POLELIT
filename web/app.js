var botones = document.querySelectorAll(".mode button");
var vistaEdu = document.getElementById("vista-edu");
var vistaTech = document.getElementById("vista-tech");

botones.forEach(function (b) {
  b.addEventListener("click", function () {
    botones.forEach(function (o) {
      o.setAttribute("aria-pressed", o === b ? "true" : "false");
    });
    var esTecnica = b.dataset.mode === "tech";
    vistaEdu.hidden = esTecnica;
    vistaTech.hidden = !esTecnica;
  });
});