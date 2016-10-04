var app = angular
  .module('deciframeApp', ['ngRoute', 'ngAnimate', 'ng-mfb', 'ngProgress', 'ui.bootstrap'])
  .constant('RESTAPI', {
    url: 'http://localhost:5003'
  })
  .constant('GENEROS', [
    "Brega",
    "Gótico",
    "Samba",
    "Emocore",
    "Eletrônica",
    "Psicodelia",
    "Clássico",
    "Gospel/Religioso",
    "Heavy Metal",
    "Instrumental",
    "Reggae",
    "Hard Rock",
    "Pop Rock",
    "Marchas/Hinos",
    "Regional",
    "Romântico",
    "Velha Guarda",
    "Pagode",
    "Jovem Guarda",
    "Rockabilly",
    "Hardcore",
    "Bossa Nova",
    "Punk Rock",
    "Power-Pop",
    "Country",
    "Guarânia",
    "Funk Carioca",
    "Soul",
    "Disco",
    "New Wave",
    "Soft Rock",
    "Rock Progressivo",
    "World Music",
    "Rock",
    "Sertanejo",
    "Grunge",
    "Samba Enredo",
    "Bolero",
    "Industrial",
    "MPB",
    "Hip Hop/Rap",
    "Indie",
    "Surf Music",
    "Infantil",
    "Pop",
    "Alternativo",
    "Forró",
    "Blues",
    "Axé",
    "Jazz",
    "Folk"
    ]);
