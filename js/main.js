(function() {
    'use strict';

    angular
        .module('DecifraMe')
        .controller('MainCtrl', function($scope, $http, $window) {

          $scope.filtroArtista = [];
          $scope.filtroEstilo = [];
          $scope.filtroFacilidade = [0, 100];
          $scope.tituloMusica = "";

          $scope.musicas = [];
          $scope.meusAcordes = [];
          $scope.seqFamosa = [];

          $scope.acordesMaiores = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
          $scope.acordesMenores = ["Cm", "C#m", "Dm", "D#m", "Em", "Fm", "F#m", "Gm", "G#m", "Am", "A#m", "Bm"];
          $scope.acordesComSetima = ["C7", "C#7", "D7", "D#7", "E7", "F7", "F#7", "G7", "G#7", "A7", "A#7", "B7"];
          $scope.sequenciasFamosas = ['Bm - G - D - A', "C - G - Am - F", "Em - G", "C - A7 - Dm - G7", "Gm - F", "C - C7 - F - Fm"]

          $scope.tiraEBota = function(s) {
            if ($scope.meusAcordes.indexOf(s) == -1) {
              $scope.meusAcordes.push(s);
            } else {
              var index = $scope.meusAcordes.indexOf(s);
              if (index > -1) $scope.meusAcordes.splice(index, 1);
            }
          }

          $scope.pesquisarPorNome = function() {
            $http.get("http://localhost:5000/busca?musica=" + $scope.tituloMusica)
              .success(function(data, headers) {
                if(data.length == 1) $http.get("http://localhost:5000/rankByMusica?musica=" + data[0].musica +
                  "&artista=" + data[0].artista +
                  "&filtro-generos=" + JSON.stringify($scope.filtroEstilo) +
                  "&filtro-artistas=" + JSON.stringify($scope.filtroArtista) +
                  "&min=" + $scope.filtroFacilidade[0] +
                  "&max=" + $scope.filtroFacilidade[1]
                )
                  .success(function (data, headers) {
                    $scope.musicas = data;
                  })
                else console.log(data.length)
              })
              .error(function(data, headers) {
                console.log("Erro ao tentar pesquisar por nome!");
              });
          }

          $scope.pesquisarPorSequencia = function(i) {
            $http.get("http://localhost:5000/porSequencia?sequencia=" + i +
                  "&filtro-generos=" + JSON.stringify($scope.filtroEstilo) +
                  "&filtro-artistas=" + JSON.stringify($scope.filtroArtista) +
                  "&min=" + $scope.filtroFacilidade[0] +
                  "&max=" + $scope.filtroFacilidade[1]
                )
                  .success(function (data, headers) {
                    console.log(data);
                    $scope.musicas = data;
                  });
          }

          $scope.pesquisarPorAcordes = function() {

            function replaceAll(str, find, replace) {
              return str.replace(new RegExp(find, 'g'), replace);
            }

            $http.get(
              "http://localhost:5000/rankByAcordes?acordes=" + replaceAll(JSON.stringify($scope.meusAcordes), '#', "%23") +
                "&filtro-generos=" + JSON.stringify($scope.filtroEstilo) +
                "&filtro-artistas=" + JSON.stringify($scope.filtroArtista) +
                "&min=" + $scope.filtroFacilidade[0] +
                "&max=" + $scope.filtroFacilidade[1]
              )
                .success(function (data, headers) {
                  $scope.musicas = data;
                })
                .error(function () {
                  console.log("Erro ao tentar pesquisar por acordes!");
                })
          }
        })
})();
